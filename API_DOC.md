# 塔罗牌占卜 API 接口文档

> 所有接口统一需要请求头 `X-WX-OPENID`（微信小程序自动注入用户身份）

---

## 一、塔罗牌解读

### 1.1 提交占卜请求

**请求**

```
POST /api/tarot
```

**请求体**

```json
{
    "question": "我今年的学业发展如何啊？",
    "cards": {"愚者": "正", "女祭司": "负", "命运之轮": "正"},
    "spread": "时间之流三牌阵",
    "positions": ["过去", "现在", "未来"]
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| question | string | 是 | 用户的提问 |
| cards | object | 是 | 抽到的牌，key 为牌名，value 为 `"正"` 或 `"负"` |
| spread | string | 是 | 牌阵名称 |
| positions | array | 否 | 牌位含义列表，顺序与 cards 一一对应，如 `["过去", "现在", "未来"]` |

> **0218 修改**：cards 从数组格式 `["愚者", "女祭司"]` 改为字典格式 `{"愚者": "正", "女祭司": "负"}`，携带正负位信息
>
> **0219 修改**：新增 `positions` 参数，传入各牌位的含义，大模型会结合牌位语境进行解读

**响应**（立即返回，后台异步解读）

```json
{
    "code": 0,
    "msg": "已提交解读，请稍候查询结果",
    "reading_id": 10
}
```

| 字段 | 说明 |
|------|------|
| code | 0=成功，1=失败 |
| msg | 提示信息 |
| reading_id | 解读记录 ID，用于轮询结果 |

---

### 1.2 查询解读结果（轮询）

**请求**

```
GET /api/tarot/result?id={reading_id}
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | int | 是 | 提交占卜返回的 reading_id |

**响应**

解读完成时：
```json
{
    "code": 0,
    "status": "completed",
    "msg": "解读成功",
    "result": {
        "reading_content": "牌面解读内容（含引子、牌阵说明、逐张解读）",
        "综合分析": "用情绪逻辑总结所有牌的关系，围绕用户问题分析",
        "金句": "一句温暖而有力量的话",
        "建议": "3条具体建议，每条带行动提示"
    }
}
```

> **result 字段说明**：`result` 为 JSON 对象，包含 4 个字段，前端可分模块展示

| result 子字段 | 类型 | 说明 |
|--------------|------|------|
| reading_content | string | 牌面逐张解读 |
| 综合分析 | string | 所有牌的关系总结 |
| 金句 | string | 一句总结性金句 |
| 建议 | string | 3 条行动建议 |

解读中：
```json
{
    "code": 0,
    "status": "processing",
    "msg": "正在解读中，请稍候...",
    "result": {}
}
```

解读失败：
```json
{
    "code": 1,
    "status": "failed",
    "msg": "失败原因",
    "result": {}
}
```

| status 值 | 说明 |
|-----------|------|
| pending | 等待解读 |
| processing | 解读中 |
| completed | 解读完成 |
| failed | 解读失败 |

**前端轮询建议**：每 2 秒请求一次，最多轮询 60 秒

---

### 1.3 大模型调用实现

**System Prompt（0214 版）**

```
你是一位富有同理心的塔罗占卜师，请根据用户抽到的牌阵和牌面，生成一段温暖、易懂、有启发性的个性化解读。
1、整体语气：像一位智慧的朋友在低语，温柔而不说教，有温度、有力量；
2、内容结构：
开头用一句引子营造氛围（如"你的爱情现状解读"）
简要说明牌阵含义（不超过 2 句）
每张牌用 "关键词 + 描述 + 情绪连接" 的方式解读：
• 牌名 + 正逆位
• 图像描述（简洁）
• 在当前情境下的象征意义
• 与用户内心的关联（共情）
用 "能量链" 或 "情绪逻辑" 总结三张牌的关系
给出 3 条具体建议，每条带行动提示（如"写下来"、"尝试一次对话"）
最后用一句金句总结，引发共鸣
注意：避免术语堆砌，如"潜意识"、"能量场"等可用"内心声音"、"情绪流动"替代。不要使用任何emoji表情符号，用纯文字表达
```

**User Message 模板（0219 修改）**

```
我的问题是：{question}

使用的牌阵：{spread}

各牌位含义（按顺序）：过去、现在、未来

抽到的牌（按牌位顺序）：愚者牌正位、女祭司牌负位、命运之轮牌正位

请为我解读这些牌。
```

> **0218 修改**：牌面描述改为 "xx牌x位" 格式，如 "愚者牌正位"
>
> **0219 修改**：当传入 positions 时，新增"各牌位含义"行，牌位含义与牌面按顺序一一对应
<<<<<<< Current (Your changes)
=======

---

### 1.4 获取塔罗牌图片

**请求**

```
GET /api/tarot/image?name={图片名称}
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | string | 是 | 图片名称，如 `10命运之轮`、`the_fool`，可带或不带扩展名 |

**响应**

```json
{
    "code": 0,
    "data": {
        "url": "https://xxx.tcb.qcloud.la/10命运之轮.png"
    }
}
```

| 字段 | 说明 |
|------|------|
| url | 图片访问地址，前端直接用于 `<image src="url">` 或 `wx.previewImage` |
| 若名称对应图片不存在 | 返回默认图片（10命运之轮.png）的 URL |

> 图片存储在云托管对象存储中，无需 X-WX-OPENID
>>>>>>> Incoming (Background Agent changes)

---

## 二、历史记录

### 2.1 获取历史记录

**请求**

```
GET /api/tarot/history?page=1&page_size=10
```

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| page | int | 否 | 1 | 页码 |
| page_size | int | 否 | 10 | 每页条数 |

**响应**

```json
{
    "code": 0,
    "data": {
        "list": [
            {
                "id": 123,
                "question": "我今年的事业发展如何？",
                "cards": {"愚者": "正", "女祭司": "负", "命运之轮": "正"},
                "spread": "时间之流三牌阵",
                "status": "completed",
                "result": {
                    "reading_content": "牌面解读内容...",
                    "综合分析": "综合分析内容...",
                    "金句": "一句金句...",
                    "建议": "3条建议..."
                },
                "created_at": "2026-02-18 14:30:00"
            }
        ],
        "total": 15,
        "page": 1,
        "page_size": 10
    }
}
```

| 字段 | 说明 |
|------|------|
| list | 记录数组 |
| list[].id | 记录 ID（删除时需要传此值） |
| list[].question | 用户提问 |
| list[].cards | 牌面及正负位 |
| list[].spread | 牌阵名称 |
| list[].status | 状态 |
| list[].result | 解读结果对象（仅 completed 有内容，结构同 1.2 的 result） |
| list[].created_at | 创建时间 |
| total | 总记录数 |
| page | 当前页码 |
| page_size | 每页条数 |

---

### 2.2 删除单条历史记录

> 软删除，数据库保留，仅前端不再显示

**请求**

```
POST /api/tarot/history/delete
```

**请求体**

```json
{
    "id": 123
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | int | 是 | 要删除的记录 ID（对应历史记录中的 id 字段） |

**响应**

成功：
```json
{
    "code": 0,
    "data": {
        "msg": "删除成功"
    }
}
```

失败：
```json
{
    "code": 1,
    "msg": "记录不存在",
    "result": ""
}
```

---

### 2.3 删除全部历史记录

> 软删除，数据库保留，仅前端不再显示

**请求**

```
POST /api/tarot/history/delete_all
```

无需请求体。

**响应**

成功：
```json
{
    "code": 0,
    "data": {
        "msg": "删除成功",
        "deleted_count": 5
    }
}
```

| 字段 | 说明 |
|------|------|
| msg | 提示信息 |
| deleted_count | 本次删除的记录条数 |

---

## 三、用户信息

> 0218 新增，用户首次占卜时自动注册

### 3.1 获取用户信息

**请求**

```
GET /api/user/info
```

无需参数，通过请求头 `X-WX-OPENID` 识别用户。

**响应**

```json
{
    "code": 0,
    "data": {
        "openid": "oXXXXXXXXXXX",
        "nickname": "用户昵称",
        "avatar_url": "https://...",
        "created_at": "2026-02-18 10:00:00"
    }
}
```

---

### 3.2 更新用户信息

**请求**

```
POST /api/user/update
```

**请求体**

```json
{
    "nickname": "新昵称",
    "avatar_url": "https://新头像URL"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| nickname | string | 否 | 用户昵称 |
| avatar_url | string | 否 | 用户头像 URL |

**响应**

```json
{
    "code": 0,
    "data": {
        "msg": "更新成功"
    }
}
```

---

## 四、待开发功能

### 4.1 分享解读结果

**产品形态**：分享结果 => 输出一张带有内容的图 => 可供用户下载

**技术方案调研**：

- 方案一：后端生成动态分享图（通过云函数）
- 方案二：前端通过 Canvas 绘制分享图

**参考资料**：

- [腾讯云：小程序动态分享卡片](https://cloud.tencent.com/developer/article/2492124)
- [知乎：小程序分享实现](https://zhuanlan.zhihu.com/p/1907871372799095205)
- [微信官方：wx.showShareImageMenu](https://developers.weixin.qq.com/minigame/dev/api/share/wx.showShareImageMenu.html)

**实现思路**：

1. 使用 `onShareAppMessage` 自定义分享卡片
2. 后端云函数生成动态分享图，返回云文件 ID
3. 前端展示并支持保存到相册

---

## 五、数据库表结构

### users 用户表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT, 主键, 自增 | 用户 ID |
| openid | VARCHAR(128), 唯一索引 | 微信 openid |
| nickname | VARCHAR(64), 可空 | 用户昵称 |
| avatar_url | VARCHAR(500), 可空 | 头像 URL |
| created_at | TIMESTAMP | 首次使用时间 |
| updated_at | TIMESTAMP | 最后活跃时间 |

### tarot_readings 解读记录表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT, 主键, 自增 | 记录 ID |
| openid | VARCHAR(128), 索引 | 用户微信 openid |
| question | VARCHAR(500) | 用户提问 |
| cards | VARCHAR(500) | 牌面 JSON 字符串 |
| spread | VARCHAR(100) | 牌阵名称 |
| status | VARCHAR(20), 默认 pending | 任务状态 |
| result | TEXT, 可空 | 大模型解读结果 |
| is_deleted | TINYINT(1), 默认 0 | 软删除标记 |
| created_at | TIMESTAMP | 创建时间 |

---

## 更新日志

| 日期 | 内容 |
|------|------|
| 0214 | 初版上线：占卜解读、历史记录、异步模式 |
| 0218 | cards 改为字典格式支持正负位；新增软删除接口；新增 User 用户表；删除 Counters 表 |
| 0219 | 解读结果改为结构化 JSON；新增 positions 牌位含义参数；新增分享图片接口 |
