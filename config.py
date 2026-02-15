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
