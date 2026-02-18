import json
import logging
import re
import requests
import config

logger = logging.getLogger('log')

RESULT_REQUIRED_KEYS = ["reading_content", "综合分析", "金句", "建议"]

SYSTEM_PROMPT = """你是一位富有同理心的塔罗占卜师，请根据用户抽到的牌阵和牌面，生成个性化解读。

你必须严格以 JSON 格式回复，不要在 JSON 之外输出任何其他内容（不要包含 ```json 标记）。JSON 结构如下：

{
    "reading_content": "牌面解读内容",
    "综合分析": "综合分析内容",
    "金句": "一句金句",
    "建议": "具体建议"
}

各字段要求：
1. reading_content（牌面解读）：
   - 开头用一句引子营造氛围（如"让我们来看看你的爱情现状"）
   - 简要说明牌阵含义（不超过2句）
   - 每张牌用"关键词 + 描述 + 情绪连接"的方式解读：牌名+正逆位、图像描述（简洁）、在当前情境下的象征意义、与用户内心的关联（共情）
   - 多张牌之间用换行分隔

2. 综合分析：
   - 总结所有牌的关系
   - 严格围绕用户的问题进行分析，直接回答用户的疑问

3. 金句：
   - 一句温暖而有力量的话，引发共鸣

4. 建议：
   - 给出3条具体建议，每条带行动提示（如"写下来"、"尝试一次对话"）
   - 每条建议之间用换行分隔

语气要求：像一位智慧的朋友在低语，温柔而不说教，有温度、有力量。
注意：避免术语堆砌，如"潜意识"、"能量场"等可用"内心声音"、"情绪流动"替代。不要使用任何emoji表情符号，用纯文字表达。"""


def parse_reading_result(raw_text):
    """
    从大模型原始回复中提取并验证 JSON 结构。
    :return: (success, parsed_dict_or_error_msg)
    """
    text = raw_text.strip()

    # 尝试直接解析
    parsed = _try_parse_json(text)
    if parsed:
        return True, parsed

    # 尝试提取 ```json ... ``` 代码块
    match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    if match:
        parsed = _try_parse_json(match.group(1))
        if parsed:
            return True, parsed

    # 尝试提取最外层 { ... }
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        parsed = _try_parse_json(match.group(0))
        if parsed:
            return True, parsed

    logger.warning("无法从大模型回复中解析 JSON，使用 fallback 结构: %s", text[:200])
    return False, text


def _try_parse_json(text):
    """尝试解析 JSON 并验证必要字段存在"""
    try:
        data = json.loads(text)
        if not isinstance(data, dict):
            return None
        for key in RESULT_REQUIRED_KEYS:
            if key not in data:
                data[key] = ""
        return data
    except (json.JSONDecodeError, TypeError):
        return None


def safe_parse_result(result_str):
    """
    安全地将数据库中存储的 result 字符串解析为 dict。
    兼容旧的纯文本格式记录。
    """
    if not result_str:
        return {}
    try:
        data = json.loads(result_str)
        if isinstance(data, dict):
            return data
    except (json.JSONDecodeError, TypeError):
        pass
    return {"reading_content": result_str, "综合分析": "", "金句": "", "建议": ""}


def call_deepseek(question, cards, spread, positions=None):
    """
    调用 DeepSeek API 进行塔罗牌解读
    :param question: 用户的问题
    :param cards: 抽到的牌字典，格式 {"牌名": "正/负"}
    :param spread: 牌阵名称
    :param positions: 牌位含义列表，如 ["过去", "现在", "未来"]
    :return: (success, message, result_json_str)
             success: bool, 是否成功
             message: str, 提示信息
             result_json_str: str, JSON 格式的解读结果（失败时为空字符串）
    """
    if not config.DEEPSEEK_API_KEY:
        return False, "DeepSeek API Key 未配置", ""

    cards_str = "、".join(f"{name}牌{pos}位" for name, pos in cards.items())

    positions_str = ""
    if positions and len(positions) == len(cards):
        positions_str = f"\n\n各牌位含义（按顺序）：{'、'.join(positions)}"

    user_message = f"""我的问题是：{question}

使用的牌阵：{spread}{positions_str}

抽到的牌（按牌位顺序）：{cards_str}

请为我解读这些牌。"""

    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config.DEEPSEEK_API_KEY}"
        }

        payload = {
            "model": config.DEEPSEEK_MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ],
            "temperature": 0.7,
            "max_tokens": 2000
        }

        response = requests.post(
            config.DEEPSEEK_API_URL,
            headers=headers,
            json=payload,
            timeout=60
        )

        if response.status_code != 200:
            logger.error(f"DeepSeek API 请求失败, status={response.status_code}, body={response.text}")
            return False, f"AI 服务请求失败 (HTTP {response.status_code})", ""

        resp_data = response.json()

        raw_result = resp_data.get("choices", [{}])[0].get("message", {}).get("content", "")
        if not raw_result:
            logger.error(f"DeepSeek API 返回内容为空, response={resp_data}")
            return False, "AI 服务返回内容为空", ""

        # 解析 JSON 结构
        ok, parsed = parse_reading_result(raw_result)
        if ok:
            result_json_str = json.dumps(parsed, ensure_ascii=False)
        else:
            fallback = {"reading_content": parsed, "综合分析": "", "金句": "", "建议": ""}
            result_json_str = json.dumps(fallback, ensure_ascii=False)
            logger.warning("大模型返回格式异常，已使用 fallback 结构")

        return True, "解读成功", result_json_str

    except requests.exceptions.Timeout:
        logger.error("DeepSeek API 请求超时")
        return False, "AI 服务请求超时，请稍后重试", ""
    except requests.exceptions.RequestException as e:
        logger.error(f"DeepSeek API 请求异常: {e}")
        return False, f"AI 服务请求异常: {str(e)}", ""
    except (json.JSONDecodeError, KeyError, IndexError) as e:
        logger.error(f"DeepSeek API 响应解析失败: {e}")
        return False, "AI 服务响应解析失败", ""
