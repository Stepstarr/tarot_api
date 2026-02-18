import os

# 是否开启debug模式
DEBUG = True

# 读取数据库环境变量（实际值在云托管控制台「服务设置」→「环境变量」中配置）
username = os.environ.get("MYSQL_USERNAME", '')
password = os.environ.get("MYSQL_PASSWORD", '')
db_address = os.environ.get("MYSQL_ADDRESS", '')

# DeepSeek API 配置（实际值在云托管控制台「服务设置」→「环境变量」中配置）
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_API_URL = os.environ.get("DEEPSEEK_API_URL", "https://api.deepseek.com/chat/completions")
DEEPSEEK_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")

# 云托管对象存储配置（塔罗牌图片）
# cloud://prod-4gl5ea883a5593e8.7072-prod-4gl5ea883a5593e8-1314762925/xxx.png
STORAGE_BASE_URL = os.environ.get(
    "STORAGE_BASE_URL",
    "https://7072-prod-4gl5ea883a5593e8-1314762925.tcb.qcloud.la"
)
STORAGE_DEFAULT_IMAGE = "10命运之轮.png"
