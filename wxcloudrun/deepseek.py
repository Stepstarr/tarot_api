import json
import logging
import requests
import config

logger = logging.getLogger('log')

# 塔罗牌解读的系统提示词
SYSTEM_PROMPT = """你是一位经验丰富的塔罗牌解读师，精通韦特塔罗牌的象征意义和解读方法。
用户会告诉你他们的问题、使用的牌阵以及抽到的牌。请根据这些信息，给出专业、详细且有深度的塔罗牌解读。

解读要求：
1. 简要解释每张牌在当前牌位的含义
2. 综合分析牌面之间的关系
3. 针对用户的具体问题，给出有针对性的解读和建议
4. 语言温暖、有洞察力，通俗易懂
5. 总字数控制在500字以内，简洁有力"""


def call_deepseek(question, cards, spread):
    """
    调用 DeepSeek API 进行塔罗牌解读
    :param question: 用户的问题
    :param cards: 抽到的牌列表
    :param spread: 牌阵名称
    :return: (success, message, result)
             success: bool, 是否成功
             message: str, 提示信息
             result: str, 解读结果（失败时为空字符串）
    """
    if not config.DEEPSEEK_API_KEY:
        return False, "DeepSeek API Key 未配置", ""

    # 构造用户消息
    cards_str = "、".join(cards)
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
