import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import pymysql
from urllib.parse import quote_plus
import config

# 因MySQLDB不支持Python3，使用pymysql扩展库代替MySQLDB库
pymysql.install_as_MySQLdb()

logger = logging.getLogger('log')

# 启动时自动创建数据库（如果不存在）
def _ensure_database_exists():
    """确保 flask_demo 数据库存在，不存在则自动创建"""
    if not config.db_address or not config.username:
        logger.warning("数据库配置不完整，跳过自动创建数据库")
        return
    try:
        host, port = config.db_address.split(':')
        conn = pymysql.connect(
            host=host,
            port=int(port),
            user=config.username,
            password=config.password,
            charset='utf8mb4'
        )
        cursor = conn.cursor()
        cursor.execute("ALTER DATABASE flask_demo CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        # 重建tarot_readings表以添加status字段（部署一次后请删除此行）
        cursor.execute("USE flask_demo")
        cursor.execute("DROP TABLE IF EXISTS tarot_readings")
        conn.commit()
        cursor.close()
        conn.close()
        logger.info("数据库 flask_demo 已就绪")
    except Exception as e:
        logger.error("自动创建数据库失败: {}".format(e))

_ensure_database_exists()

# 初始化web应用
app = Flask(__name__, instance_relative_config=True)
app.config['DEBUG'] = config.DEBUG

# 设定数据库链接（密码中可能含有特殊字符，需要URL编码）
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://{}:{}@{}/flask_demo?charset=utf8mb4'.format(
    config.username,
    quote_plus(config.password),
    config.db_address
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 初始化DB操作对象
db = SQLAlchemy(app)

# 加载控制器
from wxcloudrun import views

# 加载配置
app.config.from_object('config')
