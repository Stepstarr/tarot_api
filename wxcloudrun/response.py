import json

from flask import Response


def make_succ_empty_response():
    data = json.dumps({'code': 0, 'data': {}})
    return Response(data, mimetype='application/json')


def make_succ_response(data):
    data = json.dumps({'code': 0, 'data': data})
    return Response(data, mimetype='application/json')


def make_err_response(err_msg):
    data = json.dumps({'code': -1, 'errorMsg': err_msg})
    return Response(data, mimetype='application/json')


# ============ 塔罗牌解读专用响应 ============

def make_tarot_succ_response(msg, result):
    """塔罗牌解读成功响应"""
    data = json.dumps({'code': 0, 'msg': msg, 'result': result}, ensure_ascii=False)
    return Response(data, mimetype='application/json')


def make_tarot_err_response(msg):
    """塔罗牌解读失败响应"""
    data = json.dumps({'code': 1, 'msg': msg, 'result': ''}, ensure_ascii=False)
    return Response(data, mimetype='application/json')
