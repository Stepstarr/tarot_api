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
    :return: 插入成功返回记录ID，失败返回 None
    """
    try:
        db.session.add(reading)
        db.session.commit()
        return reading.id
    except Exception as e:
        db.session.rollback()
        logger.error("insert_tarot_reading errorMsg= {} ".format(e))
        return None


def update_tarot_reading(reading_id, status, result=None):
    """
    更新塔罗牌解读记录的状态和结果
    :param reading_id: 记录ID
    :param status: 新状态
    :param result: 解读结果（可选）
    """
    try:
        reading = TarotReading.query.get(reading_id)
        if reading is None:
            logger.error("update_tarot_reading: 记录不存在, id={}".format(reading_id))
            return False
        reading.status = status
        if result is not None:
            reading.result = result
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        logger.error("update_tarot_reading errorMsg= {} ".format(e))
        return False


def query_tarot_reading_by_id(reading_id):
    """
    根据ID查询塔罗牌解读记录
    """
    try:
        return TarotReading.query.get(reading_id)
    except Exception as e:
        logger.error("query_tarot_reading_by_id errorMsg= {} ".format(e))
        return None


def query_readings_by_openid(openid, page=1, page_size=10):
    """
    根据openid查询用户的塔罗牌解读历史记录（排除已软删除的）
    :param openid: 用户微信openid
    :param page: 页码
    :param page_size: 每页条数
    :return: 解读记录列表
    """
    try:
        return TarotReading.query.filter(
            TarotReading.openid == openid,
            TarotReading.is_deleted == False
        ).order_by(
            TarotReading.created_at.desc()
        ).paginate(page=page, per_page=page_size, error_out=False)
    except Exception as e:
        logger.error("query_readings_by_openid errorMsg= {} ".format(e))
        return None


def soft_delete_reading(reading_id, openid):
    """
    软删除单条塔罗牌解读记录
    :param reading_id: 记录ID
    :param openid: 用户openid（用于验证归属）
    :return: (success, msg)
    """
    try:
        reading = TarotReading.query.get(reading_id)
        if reading is None:
            return False, '记录不存在'
        if reading.openid != openid:
            return False, '无权操作此记录'
        if reading.is_deleted:
            return False, '记录已被删除'
        reading.is_deleted = True
        db.session.commit()
        return True, '删除成功'
    except Exception as e:
        db.session.rollback()
        logger.error("soft_delete_reading errorMsg= {} ".format(e))
        return False, '删除失败'


def soft_delete_all_readings(openid):
    """
    软删除用户的所有塔罗牌解读记录
    :param openid: 用户openid
    :return: (success, msg, count)
    """
    try:
        count = TarotReading.query.filter(
            TarotReading.openid == openid,
            TarotReading.is_deleted == False
        ).update({'is_deleted': True})
        db.session.commit()
        return True, '删除成功', count
    except Exception as e:
        db.session.rollback()
        logger.error("soft_delete_all_readings errorMsg= {} ".format(e))
        return False, '删除失败', 0
