from datetime import datetime

from wxcloudrun import db


# 用户表
class User(db.Model):
    __tablename__ = 'users'
    __table_args__ = {'mysql_charset': 'utf8mb4', 'mysql_collate': 'utf8mb4_unicode_ci'}

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    openid = db.Column(db.String(128), nullable=False, unique=True, index=True, comment='用户微信openid')
    nickname = db.Column(db.String(64), nullable=True, comment='用户昵称')
    avatar_url = db.Column(db.String(500), nullable=True, comment='用户头像URL')
    created_at = db.Column(db.TIMESTAMP, nullable=False, default=datetime.now, comment='首次使用时间')
    updated_at = db.Column(db.TIMESTAMP, nullable=False, default=datetime.now, onupdate=datetime.now, comment='最后活跃时间')


# 塔罗牌解读记录表
class TarotReading(db.Model):
    __tablename__ = 'tarot_readings'
    __table_args__ = {'mysql_charset': 'utf8mb4', 'mysql_collate': 'utf8mb4_unicode_ci'}

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    openid = db.Column(db.String(128), nullable=False, index=True, comment='用户微信openid')
    question = db.Column(db.String(500), nullable=False, comment='用户提问')
    cards = db.Column(db.String(500), nullable=False, comment='抽到的牌，JSON字符串')
    spread = db.Column(db.String(100), nullable=False, comment='牌阵名称')
    # status: pending=等待解读, processing=解读中, completed=解读完成, failed=解读失败
    status = db.Column(db.String(20), nullable=False, default='pending', comment='任务状态')
    result = db.Column(db.Text, nullable=True, comment='大模型解读结果')
    is_deleted = db.Column(db.Boolean, nullable=False, default=False, server_default='0', comment='是否已删除（软删除）')
    created_at = db.Column(db.TIMESTAMP, nullable=False, default=datetime.now, comment='创建时间')
