from datetime import datetime

from wxcloudrun import db


# 计数表（保留原有模型）
class Counters(db.Model):
    # 设置结构体表格名称
    __tablename__ = 'Counters'

    # 设定结构体对应表格的字段
    id = db.Column(db.Integer, primary_key=True)
    count = db.Column(db.Integer, default=1)
    created_at = db.Column('createdAt', db.TIMESTAMP, nullable=False, default=datetime.now())
    updated_at = db.Column('updatedAt', db.TIMESTAMP, nullable=False, default=datetime.now())


# 塔罗牌解读记录表
class TarotReading(db.Model):
    __tablename__ = 'tarot_readings'
    __table_args__ = {'mysql_charset': 'utf8mb4', 'mysql_collate': 'utf8mb4_unicode_ci'}

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    openid = db.Column(db.String(128), nullable=False, index=True, comment='用户微信openid')
    question = db.Column(db.String(500), nullable=False, comment='用户提问')
    cards = db.Column(db.String(500), nullable=False, comment='抽到的牌，JSON数组字符串')
    spread = db.Column(db.String(100), nullable=False, comment='牌阵名称')
    # status: pending=等待解读, processing=解读中, completed=解读完成, failed=解读失败
    status = db.Column(db.String(20), nullable=False, default='pending', comment='任务状态')
    result = db.Column(db.Text, nullable=True, comment='大模型解读结果')
    created_at = db.Column(db.TIMESTAMP, nullable=False, default=datetime.now, comment='创建时间')
