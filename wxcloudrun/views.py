import json
import logging
from datetime import datetime

from flask import render_template, request
from run import app
from wxcloudrun import db
from wxcloudrun.dao import delete_counterbyid, query_counterbyid, insert_counter, update_counterbyid, \
    insert_tarot_reading, query_readings_by_openid
from wxcloudrun.model import Counters, TarotReading
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


@app.route('/api/count', methods=['POST'])
def count():
    """
    :return:计数结果/清除结果
    """

    # 获取请求体参数
    params = request.get_json()

    # 检查action参数
    if 'action' not in params:
        return make_err_response('缺少action参数')

    # 按照不同的action的值，进行不同的操作
    action = params['action']

    # 执行自增操作
    if action == 'inc':
        counter = query_counterbyid(1)
        if counter is None:
            counter = Counters()
            counter.id = 1
            counter.count = 1
            counter.created_at = datetime.now()
            counter.updated_at = datetime.now()
            insert_counter(counter)
        else:
            counter.id = 1
            counter.count += 1
            counter.updated_at = datetime.now()
            update_counterbyid(counter)
        return make_succ_response(counter.count)

    # 执行清0操作
    elif action == 'clear':
        delete_counterbyid(1)
        return make_succ_empty_response()

    # action参数错误
    else:
        return make_err_response('action参数错误')


@app.route('/api/count', methods=['GET'])
def get_count():
    """
    :return: 计数的值
    """
    counter = Counters.query.filter(Counters.id == 1).first()
    return make_succ_response(0) if counter is None else make_succ_response(counter.count)


@app.route('/api/tarot', methods=['POST'])
def tarot_reading():
    """
    塔罗牌解读接口
    请求体:
    {
        "question": "我今年的事业发展如何？",
        "cards": ["愚者", "女祭司", "命运之轮"],
        "spread": "时间之流三牌阵"
    }
    响应:
    {
        "code": 0,    // 0成功, 1失败
        "msg": "解读成功",
        "result": "解读内容..."
    }
    """
    # 获取用户openid（微信云托管会自动在header中注入用户信息）
    openid = request.headers.get('X-WX-OPENID', '')
    if not openid:
        return make_tarot_err_response('无法获取用户身份信息，请通过微信小程序调用')

    # 解析请求参数
    params = request.get_json()
    if not params:
        return make_tarot_err_response('请求参数不能为空')

    question = params.get('question', '').strip()
    cards = params.get('cards', [])
    spread = params.get('spread', '').strip()

    # 参数校验
    if not question:
        return make_tarot_err_response('缺少问题(question)参数')
    if not cards or not isinstance(cards, list) or len(cards) == 0:
        return make_tarot_err_response('缺少牌面(cards)参数或格式不正确')
    if not spread:
        return make_tarot_err_response('缺少牌阵(spread)参数')

    # 调用 DeepSeek 进行解读
    success, msg, result = call_deepseek(question, cards, spread)

    if not success:
        return make_tarot_err_response(msg)

    # 将解读记录存入数据库
    try:
        reading = TarotReading()
        reading.openid = openid
        reading.question = question
        reading.cards = json.dumps(cards, ensure_ascii=False)
        reading.spread = spread
        reading.result = result
        reading.created_at = datetime.now()

        if not insert_tarot_reading(reading):
            logger.error("塔罗解读记录存储失败, openid={}".format(openid))
            # 存储失败不影响返回结果给用户
    except Exception as e:
        logger.error("塔罗解读记录存储异常: {}".format(e))

    return make_tarot_succ_response(msg, result)


@app.route('/api/tarot/history', methods=['GET'])
def tarot_history():
    """
    获取用户的塔罗牌解读历史记录
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
            'result': reading.result,
            'created_at': reading.created_at.strftime('%Y-%m-%d %H:%M:%S') if reading.created_at else ''
        })

    return make_succ_response({
        'list': records,
        'total': pagination.total,
        'page': page,
        'page_size': page_size
    })


@app.route('/api/dbtest', methods=['GET'])
def db_test():
    """
    调试接口：测试数据库连接状态（上线后可删除）
    """
    import config
    info = {
        'mysql_address': config.db_address,
        'mysql_username': config.username,
        'password_length': len(config.password) if config.password else 0,
        'password_set': bool(config.password),
    }
    try:
        result = db.session.execute('SELECT 1').fetchone()
        info['db_connection'] = '成功'
        info['db_result'] = str(result[0])
    except Exception as e:
        info['db_connection'] = '失败'
        info['db_error'] = str(e)
    return make_succ_response(info)


@app.before_first_request
def init_db():
    """
    首次请求时自动创建数据库表
    """
    db.create_all()
