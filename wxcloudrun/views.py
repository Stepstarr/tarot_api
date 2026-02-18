import json
import logging
import threading
from datetime import datetime

from flask import render_template, request
from run import app
from wxcloudrun import db
from wxcloudrun.dao import insert_tarot_reading, query_readings_by_openid, update_tarot_reading, \
    query_tarot_reading_by_id, soft_delete_reading, soft_delete_all_readings, \
    get_or_create_user, update_user, query_user_by_openid
from wxcloudrun.model import TarotReading
from wxcloudrun.response import make_succ_empty_response, make_succ_response, make_err_response, \
    make_tarot_succ_response, make_tarot_err_response
from wxcloudrun.deepseek import call_deepseek

logger = logging.getLogger('log')


@app.route('/')
def index():
    """
    :return: 返回index页面
    """
    return render_template('index.html')


def _process_tarot_reading(app_context, reading_id, question, cards, spread):
    """
    后台线程：调用 DeepSeek 解读并将结果存入数据库
    """
    with app_context:
        try:
            update_tarot_reading(reading_id, 'processing')

            success, msg, result = call_deepseek(question, cards, spread)

            if success:
                update_tarot_reading(reading_id, 'completed', result)
                logger.info("塔罗解读完成, id={}, 结果长度={}".format(reading_id, len(result)))
            else:
                update_tarot_reading(reading_id, 'failed', msg)
                logger.error("塔罗解读失败, id={}, msg={}".format(reading_id, msg))
        except Exception as e:
            logger.error("塔罗解读异常, id={}, error={}".format(reading_id, str(e)))
            try:
                update_tarot_reading(reading_id, 'failed', '解读过程发生异常')
            except Exception:
                pass


@app.route('/api/tarot', methods=['POST'])
def tarot_reading():
    """
    塔罗牌解读接口（异步模式）
    请求体:
    {
        "question": "我今年的学业发展如何啊？",
        "cards": {"愚者": "正", "女祭司": "负", "命运之轮": "正"},
        "spread": "时间之流三牌阵"
    }
    响应（立即返回）:
    {
        "code": 0,
        "msg": "已提交解读",
        "reading_id": 123
    }
    然后前端用 reading_id 轮询 /api/tarot/result?id=123 获取结果
    """
    openid = request.headers.get('X-WX-OPENID', '')
    if not openid:
        return make_tarot_err_response('无法获取用户身份信息，请通过微信小程序调用')

    params = request.get_json()
    if not params:
        return make_tarot_err_response('请求参数不能为空')

    question = params.get('question', '').strip()
    cards = params.get('cards', {})
    spread = params.get('spread', '').strip()

    if not question:
        return make_tarot_err_response('缺少问题(question)参数')
    if not cards or not isinstance(cards, dict) or len(cards) == 0:
        return make_tarot_err_response('缺少牌面(cards)参数或格式不正确，应为 {"牌名": "正/负"} 格式')
    if not spread:
        return make_tarot_err_response('缺少牌阵(spread)参数')

    # 自动注册/更新用户活跃时间
    get_or_create_user(openid)

    reading = TarotReading()
    reading.openid = openid
    reading.question = question
    reading.cards = json.dumps(cards, ensure_ascii=False)
    reading.spread = spread
    reading.status = 'pending'
    reading.created_at = datetime.now()

    reading_id = insert_tarot_reading(reading)
    if not reading_id:
        return make_tarot_err_response('创建解读任务失败')

    thread = threading.Thread(
        target=_process_tarot_reading,
        args=(app.app_context(), reading_id, question, cards, spread)
    )
    thread.daemon = True
    thread.start()

    data = json.dumps({
        'code': 0,
        'msg': '已提交解读，请稍候查询结果',
        'reading_id': reading_id
    }, ensure_ascii=False)
    from flask import Response
    return Response(data, mimetype='application/json')


@app.route('/api/tarot/result', methods=['GET'])
def tarot_result():
    """
    查询塔罗牌解读结果（轮询接口）
    请求参数: ?id=123
    """
    reading_id = request.args.get('id', type=int)
    if not reading_id:
        return make_tarot_err_response('缺少id参数')

    reading = query_tarot_reading_by_id(reading_id)
    if not reading:
        return make_tarot_err_response('解读记录不存在')

    openid = request.headers.get('X-WX-OPENID', '')
    if openid and reading.openid != openid:
        return make_tarot_err_response('无权查看此记录')

    if reading.status == 'completed':
        data = json.dumps({
            'code': 0,
            'status': 'completed',
            'msg': '解读成功',
            'result': reading.result
        }, ensure_ascii=False)
    elif reading.status == 'failed':
        data = json.dumps({
            'code': 1,
            'status': 'failed',
            'msg': reading.result or '解读失败',
            'result': ''
        }, ensure_ascii=False)
    else:
        data = json.dumps({
            'code': 0,
            'status': reading.status,
            'msg': '正在解读中，请稍候...',
            'result': ''
        }, ensure_ascii=False)

    from flask import Response
    return Response(data, mimetype='application/json')


@app.route('/api/tarot/history', methods=['GET'])
def tarot_history():
    """
    获取用户的塔罗牌解读历史记录（只返回未被软删除的）
    请求参数(query string):
        page: 页码，默认1
        page_size: 每页条数，默认10
    """
    openid = request.headers.get('X-WX-OPENID', '')
    if not openid:
        return make_tarot_err_response('无法获取用户身份信息，请通过微信小程序调用')

    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 10, type=int)

    pagination = query_readings_by_openid(openid, page, page_size)
    if pagination is None:
        return make_tarot_err_response('查询历史记录失败')

    records = []
    for reading in pagination.items:
        records.append({
            'id': reading.id,
            'question': reading.question,
            'cards': json.loads(reading.cards),
            'spread': reading.spread,
            'status': reading.status,
            'result': reading.result if reading.status == 'completed' else '',
            'created_at': reading.created_at.strftime('%Y-%m-%d %H:%M:%S') if reading.created_at else ''
        })

    return make_succ_response({
        'list': records,
        'total': pagination.total,
        'page': page,
        'page_size': page_size
    })


@app.route('/api/tarot/history/delete', methods=['POST'])
def tarot_history_delete():
    """
    删除单条塔罗牌解读历史记录（软删除，数据库保留）
    请求体: { "id": 123 }
    """
    openid = request.headers.get('X-WX-OPENID', '')
    if not openid:
        return make_tarot_err_response('无法获取用户身份信息，请通过微信小程序调用')

    params = request.get_json()
    if not params:
        return make_tarot_err_response('请求参数不能为空')

    reading_id = params.get('id')
    if not reading_id:
        return make_tarot_err_response('缺少记录id参数')

    success, msg = soft_delete_reading(reading_id, openid)
    if success:
        return make_succ_response({'msg': msg})
    else:
        return make_tarot_err_response(msg)


@app.route('/api/tarot/history/delete_all', methods=['POST'])
def tarot_history_delete_all():
    """
    删除用户所有塔罗牌解读历史记录（软删除，数据库保留）
    """
    openid = request.headers.get('X-WX-OPENID', '')
    if not openid:
        return make_tarot_err_response('无法获取用户身份信息，请通过微信小程序调用')

    success, msg, count = soft_delete_all_readings(openid)
    if success:
        return make_succ_response({'msg': msg, 'deleted_count': count})
    else:
        return make_tarot_err_response(msg)


# ============ 用户相关接口 ============

@app.route('/api/user/info', methods=['GET'])
def user_info():
    """
    获取用户信息
    """
    openid = request.headers.get('X-WX-OPENID', '')
    if not openid:
        return make_tarot_err_response('无法获取用户身份信息')

    user = get_or_create_user(openid)
    if not user:
        return make_tarot_err_response('获取用户信息失败')

    return make_succ_response({
        'openid': user.openid,
        'nickname': user.nickname or '',
        'avatar_url': user.avatar_url or '',
        'created_at': user.created_at.strftime('%Y-%m-%d %H:%M:%S') if user.created_at else ''
    })


@app.route('/api/user/update', methods=['POST'])
def user_update():
    """
    更新用户信息
    请求体: { "nickname": "昵称", "avatar_url": "头像URL" }
    """
    openid = request.headers.get('X-WX-OPENID', '')
    if not openid:
        return make_tarot_err_response('无法获取用户身份信息')

    params = request.get_json()
    if not params:
        return make_tarot_err_response('请求参数不能为空')

    # 先确保用户存在
    get_or_create_user(openid)

    nickname = params.get('nickname')
    avatar_url = params.get('avatar_url')

    success, msg = update_user(openid, nickname=nickname, avatar_url=avatar_url)
    if success:
        return make_succ_response({'msg': msg})
    else:
        return make_tarot_err_response(msg)


# ============ 管理/调试接口 ============

@app.route('/api/admin/readings', methods=['GET'])
def admin_readings():
    """
    管理接口：查看所有塔罗解读记录（上线后应删除或加权限）
    """
    try:
        readings = TarotReading.query.order_by(TarotReading.created_at.desc()).limit(50).all()
        records = []
        for r in readings:
            records.append({
                'id': r.id,
                'openid': r.openid,
                'question': r.question,
                'cards': r.cards,
                'spread': r.spread,
                'status': r.status,
                'result': r.result[:100] + '...' if r.result and len(r.result) > 100 else r.result,
                'created_at': r.created_at.strftime('%Y-%m-%d %H:%M:%S') if r.created_at else ''
            })
        return make_succ_response({'total': len(records), 'records': records})
    except Exception as e:
        return make_err_response('查询失败: {}'.format(str(e)))


@app.route('/api/dbtest', methods=['GET'])
def db_test():
    """
    调试接口：测试数据库连接 + 写入（上线后可删除）
    """
    import config
    info = {
        'mysql_address': config.db_address,
        'mysql_username': config.username,
        'password_set': bool(config.password),
    }
    try:
        result = db.session.execute('SELECT 1').fetchone()
        info['db_connection'] = '成功'
    except Exception as e:
        info['db_connection'] = '失败'
        info['db_error'] = str(e)
        return make_succ_response(info)

    try:
        reading = TarotReading()
        reading.openid = 'test_dbtest'
        reading.question = '测试问题'
        reading.cards = '["测试牌"]'
        reading.spread = '测试牌阵'
        reading.status = 'completed'
        reading.result = '这是一段测试解读内容，包含中文。'
        reading.created_at = datetime.now()
        insert_tarot_reading(reading)
        info['db_write'] = '成功'
    except Exception as e:
        info['db_write'] = '失败'
        info['db_write_error'] = str(e)

    try:
        count = TarotReading.query.count()
        info['total_readings'] = count
    except Exception as e:
        info['db_read_error'] = str(e)

    return make_succ_response(info)


@app.before_first_request
def init_db():
    """
    首次请求时自动创建数据库表
    """
    db.create_all()
