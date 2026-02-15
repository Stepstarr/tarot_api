import logging

from sqlalchemy.exc import OperationalError

from wxcloudrun import db
from wxcloudrun.model import Counters, TarotReading

# 初始化日志
logger = logging.getLogger('log')


def query_counterbyid(id):
    """
    根据ID查询Counter实体
    :param id: Counter的ID
    :return: Counter实体
    """
    try:
        return Counters.query.filter(Counters.id == id).first()
    except OperationalError as e:
        logger.info("query_counterbyid errorMsg= {} ".format(e))
        return None


def delete_counterbyid(id):
    """
    根据ID删除Counter实体
    :param id: Counter的ID
    """
    try:
        counter = Counters.query.get(id)
        if counter is None:
            return
        db.session.delete(counter)
        db.session.commit()
    except OperationalError as e:
        logger.info("delete_counterbyid errorMsg= {} ".format(e))


def insert_counter(counter):
    """
    插入一个Counter实体
    :param counter: Counters实体
    """
    try:
        db.session.add(counter)
        db.session.commit()
    except OperationalError as e:
        logger.info("insert_counter errorMsg= {} ".format(e))


def update_counterbyid(counter):
    """
    根据ID更新counter的值
    :param counter实体
    """
    try:
        counter = query_counterbyid(counter.id)
        if counter is None:
            return
        db.session.flush()
        db.session.commit()
    except OperationalError as e:
        logger.info("update_counterbyid errorMsg= {} ".format(e))


# ============ 塔罗牌解读记录相关操作 ============

def insert_tarot_reading(reading):
    """
    插入一条塔罗牌解读记录
    :param reading: TarotReading 实体
    :return: 插入成功返回 True，失败返回 False
    """
    try:
        db.session.add(reading)
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        logger.error("insert_tarot_reading errorMsg= {} ".format(e))
        return False


def query_readings_by_openid(openid, page=1, page_size=10):
    """
    根据openid查询用户的塔罗牌解读历史记录
    :param openid: 用户微信openid
    :param page: 页码
    :param page_size: 每页条数
    :return: 解读记录列表
    """
    try:
        return TarotReading.query.filter(
            TarotReading.openid == openid
        ).order_by(
            TarotReading.created_at.desc()
        ).paginate(page=page, per_page=page_size, error_out=False)
    except Exception as e:
        logger.error("query_readings_by_openid errorMsg= {} ".format(e))
        return None
