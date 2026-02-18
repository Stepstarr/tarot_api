import json
import logging
import requests
import config

logger = logging.getLogger('log')

# 塔罗牌解读的系统提示词
SYSTEM_PROMPT = """你是一位富有同理心的塔罗占卜师，请根据用户抽到的牌阵和牌面，生成一段温暖、易懂、有启发性的个性化解读。
1、整体语气：像一位智慧的朋友在低语，温柔而不说教，有温度、有力量；
2、内容结构：
开头用一句引子营造氛围（如“你的爱情现状解读”）
简要说明牌阵含义（不超过 2 句）
每张牌用 “关键词 + 描述 + 情绪连接” 的方式解读：
• 牌名 + 正逆位
• 图像描述（简洁）
• 在当前情境下的象征意义
• 与用户内心的关联（共情）
用 “能量链” 或 “情绪逻辑” 总结三张牌的关系
给出 3 条具体建议，每条带行动提示（如“写下来”、“尝试一次对话”）
最后用一句金句总结，引发共鸣
注意：避免术语堆砌，如“潜意识”、“能量场”等可用“内心声音”、“情绪流动”替代。不要使用任何emoji表情符号，用纯文字表达"""


def call_deepseek(question, cards, spread):
    """
    调用 DeepSeek API 进行塔罗牌解读
    :param question: 用户的问题
    :param cards: 抽到的牌字典，格式 {"牌名": "正/负"}
    :param spread: 牌阵名称
    :return: (success, message, result)
             success: bool, 是否成功
             message: str, 提示信息
             result: str, 解读结果（失败时为空字符串）
    """
    if not config.DEEPSEEK_API_KEY:
        return False, "DeepSeek API Key 未配置", ""

    # 构造用户消息，格式：xx牌x位
    cards_str = "、".join(f"{name}牌{pos}位" for name, pos in cards.items())
    user_message = f"""我的问题是：{question}

使用的牌阵：{spread}

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
            "max_tokens": 1000
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

        # 提取回复内容
        result = resp_data.get("choices", [{}])[0].get("message", {}).get("content", "")
        if not result:
            logger.error(f"DeepSeek API 返回内容为空, response={resp_data}")
            return False, "AI 服务返回内容为空", ""

        return True, "解读成功", result

    except requests.exceptions.Timeout:
        logger.error("DeepSeek API 请求超时")
        return False, "AI 服务请求超时，请稍后重试", ""
    except requests.exceptions.RequestException as e:
        logger.error(f"DeepSeek API 请求异常: {e}")
        return False, f"AI 服务请求异常: {str(e)}", ""
    except (json.JSONDecodeError, KeyError, IndexError) as e:
        logger.error(f"DeepSeek API 响应解析失败: {e}")
        return False, "AI 服务响应解析失败", ""
