# 接口契约

> 前端 Mock 和后端实现的唯一对齐依据。任何变更必须同步更新本文件。

## 1. 通用约定

### 1.1 基础路径

- 后端接口统一以 `/api` 开头。
- 健康检查接口为 `/health`，不带 `/api` 前缀。

### 1.2 认证方式

除登录和健康检查外，所有接口都需要请求头：

```http
Authorization: Bearer access_token_demo
```

### 1.3 统一响应格式

成功：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "request_id": "req_demo_001"
  }
}
```

错误：

```json
{
  "code": 400,
  "message": "参数错误",
  "data": null
}
```

分页：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [],
    "total": 0,
    "page": 1,
    "page_size": 20
  }
}
```

### 1.4 通用字段约定

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | string | 通用业务 ID |
| `created_at` | string | ISO 8601 时间字符串 |
| `updated_at` | string | ISO 8601 时间字符串 |
| `page` | integer | 页码，从 1 开始 |
| `page_size` | integer | 每页数量，默认 20 |
| `keyword` | string | 搜索关键词，空字符串表示不过滤 |

### 1.5 枚举值

| 字段 | 可选值 | 说明 |
|---|---|---|
| `ticket_status` | `open` / `processing` / `completed` | 待接取 / 处理中 / 已完成 |
| `priority` | `low` / `medium` / `high` | 低 / 中 / 高 |
| `message_sender` | `customer` / `employee` / `bot` | 用户 / 员工 / 机器人 |
| `qa_status` | `enabled` / `disabled` | 启用 / 停用 |
| `document_status` | `processing` / `completed` / `failed` | 处理中 / 已完成 / 失败 |
| `answer_type` | `qa_direct` / `clarification` / `generated` | QA 直接答案 / 反问 / 知识库生成答案 |
| `reference_type` | `qa` / `document` | QA / 文档 |

## 2. 数据对象

### 2.1 User

```json
{
  "id": "user_001",
  "name": "客服一组员工",
  "username": "agent01",
  "created_at": "2026-05-23T09:00:00+08:00"
}
```

### 2.2 TicketSummary

```json
{
  "id": "TK-1005",
  "title": "会员支付后未生效",
  "description": "客户反馈支付宝已扣款，但会员状态未更新。",
  "status": "processing",
  "priority": "high",
  "assignee_id": "user_001",
  "assignee_name": "客服一组员工",
  "customer_name": "张三",
  "created_at": "2026-05-23T14:30:00+08:00",
  "completed_at": null
}
```

### 2.3 TicketDetail

```json
{
  "id": "TK-1005",
  "title": "会员支付后未生效",
  "description": "客户反馈在 APP 内购买年度会员，支付宝已扣款，但账户状态未更新。",
  "status": "processing",
  "priority": "high",
  "assignee_id": "user_001",
  "assignee_name": "客服一组员工",
  "customer": {
    "id": "customer_001",
    "name": "张三",
    "level": "VIP 会员"
  },
  "related_order_id": "20260523001",
  "created_at": "2026-05-23T14:30:00+08:00",
  "completed_at": null
}
```

### 2.4 Message

```json
{
  "id": "msg_001",
  "ticket_id": "TK-1005",
  "sender": "customer",
  "sender_name": "张三",
  "content": "你好，我刚刚购买了年费会员，但是没有生效。",
  "created_at": "2026-05-23T14:32:00+08:00"
}
```

### 2.5 Reference

```json
{
  "type": "qa",
  "source_id": "qa_001",
  "title": "支付状态延迟处理办法",
  "snippet": "支付网关偶发延迟时，可引导用户提供账单流水并等待同步。",
  "score": 0.98
}
```

### 2.6 AssistantAnswer

```json
{
  "answer_id": "answer_001",
  "answer_type": "qa_direct",
  "answer": "正常情况下，退款会在 1-3 个工作日内原路退回您的支付账户。",
  "confidence": 0.98,
  "missing_fields": [],
  "references": [
    {
      "type": "qa",
      "source_id": "qa_001",
      "title": "退款到账时间说明",
      "snippet": "审核通过后，资金将在 1-3 个工作日内原路返回。",
      "score": 0.98
    }
  ],
  "context_messages_used": 3
}
```

### 2.7 QaItem

```json
{
  "id": "qa_001",
  "question": "退款多久到账？",
  "answer": "正常情况下，退款会在 1-3 个工作日内原路退回您的支付账户。",
  "status": "enabled",
  "created_at": "2026-05-23T10:00:00+08:00",
  "updated_at": "2026-05-23T10:00:00+08:00"
}
```

### 2.8 DocumentItem

```json
{
  "id": "doc_001",
  "name": "售后政策及退款流程.pdf",
  "status": "completed",
  "chunk_count": 12,
  "uploaded_by": "客服一组员工",
  "created_at": "2026-05-23T11:00:00+08:00",
  "updated_at": "2026-05-23T11:02:00+08:00"
}
```

## 3. 接口清单

### 3.1 GET /health

用途：后端基础健康检查。

请求体：无

响应（成功 200）：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "status": "ok",
    "service": "customer-service-bot-api",
    "time": "2026-05-23T16:00:00+08:00"
  }
}
```

响应（失败 500）：

```json
{
  "code": 500,
  "message": "服务不可用",
  "data": null
}
```

### 3.2 POST /api/auth/login

用途：员工账号密码登录，对应 P01。

请求体：

```json
{
  "username": "agent01",
  "password": "password123"
}
```

响应（成功 200）：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "access_token": "access_token_demo",
    "token_type": "Bearer",
    "expires_in": 86400,
    "user": {
      "id": "user_001",
      "name": "客服一组员工",
      "username": "agent01",
      "created_at": "2026-05-23T09:00:00+08:00"
    }
  }
}
```

响应（失败 401）：

```json
{
  "code": 401,
  "message": "用户名或密码错误",
  "data": null
}
```

### 3.3 GET /api/auth/me

用途：获取当前登录员工，对应 P01、P10。

请求体：无

响应（成功 200）：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "user": {
      "id": "user_001",
      "name": "客服一组员工",
      "username": "agent01",
      "created_at": "2026-05-23T09:00:00+08:00"
    }
  }
}
```

响应（失败 401）：

```json
{
  "code": 401,
  "message": "登录状态已失效",
  "data": null
}
```

### 3.4 POST /api/auth/logout

用途：退出登录，对应 P01、P10。

请求体：

```json
{
  "access_token": "access_token_demo"
}
```

响应（成功 200）：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "logged_out": true
  }
}
```

响应（失败 401）：

```json
{
  "code": 401,
  "message": "登录状态已失效",
  "data": null
}
```

### 3.5 GET /api/dashboard/summary

用途：客服工作台统计概览，对应 P02。

请求体：无

响应（成功 200）：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "open_ticket_count": 8,
    "processing_ticket_count": 5,
    "completed_ticket_count": 16,
    "qa_count": 42,
    "document_count": 7,
    "latest_knowledge_updated_at": "2026-05-23T11:02:00+08:00"
  }
}
```

响应（失败 401）：

```json
{
  "code": 401,
  "message": "登录状态已失效",
  "data": null
}
```

### 3.6 GET /api/dashboard/tickets

用途：客服工作台待处理工单快捷区，对应 P02。

查询参数：

| 参数 | 类型 | 必填 | 示例 | 说明 |
|---|---|---|---|---|
| `limit` | integer | 否 | `5` | 返回数量 |

请求体：无

响应（成功 200）：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [
      {
        "id": "TK-1005",
        "title": "会员支付后未生效",
        "description": "客户反馈支付宝已扣款，但会员状态未更新。",
        "status": "processing",
        "priority": "high",
        "assignee_id": "user_001",
        "assignee_name": "客服一组员工",
        "customer_name": "张三",
        "created_at": "2026-05-23T14:30:00+08:00",
        "completed_at": null
      }
    ]
  }
}
```

响应（失败 400）：

```json
{
  "code": 400,
  "message": "limit 必须为 1 到 20 的整数",
  "data": null
}
```

### 3.7 GET /api/tickets

用途：查询工单池和我的工单，对应 P03、P04。

查询参数：

| 参数 | 类型 | 必填 | 示例 | 说明 |
|---|---|---|---|---|
| `scope` | string | 否 | `pool` | `pool` 表示工单池，`mine` 表示我的工单 |
| `status` | string | 否 | `open` | `open` / `processing` / `completed` |
| `priority` | string | 否 | `high` | `low` / `medium` / `high` |
| `keyword` | string | 否 | `支付` | 按标题或描述搜索 |
| `page` | integer | 否 | `1` | 页码 |
| `page_size` | integer | 否 | `20` | 每页数量 |

请求体：无

响应（成功 200）：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [
      {
        "id": "TK-1005",
        "title": "会员支付后未生效",
        "description": "客户反馈支付宝已扣款，但会员状态未更新。",
        "status": "processing",
        "priority": "high",
        "assignee_id": "user_001",
        "assignee_name": "客服一组员工",
        "customer_name": "张三",
        "created_at": "2026-05-23T14:30:00+08:00",
        "completed_at": null
      }
    ],
    "total": 1,
    "page": 1,
    "page_size": 20
  }
}
```

响应（失败 400）：

```json
{
  "code": 400,
  "message": "status 参数不合法",
  "data": null
}
```

### 3.8 GET /api/tickets/{ticket_id}

用途：获取工单详情，对应 P05。

路径参数：

| 参数 | 类型 | 示例 |
|---|---|---|
| `ticket_id` | string | `TK-1005` |

请求体：无

响应（成功 200）：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "ticket": {
      "id": "TK-1005",
      "title": "会员支付后未生效",
      "description": "客户反馈在 APP 内购买年度会员，支付宝已扣款，但账户状态未更新。",
      "status": "processing",
      "priority": "high",
      "assignee_id": "user_001",
      "assignee_name": "客服一组员工",
      "customer": {
        "id": "customer_001",
        "name": "张三",
        "level": "VIP 会员"
      },
      "related_order_id": "20260523001",
      "created_at": "2026-05-23T14:30:00+08:00",
      "completed_at": null
    }
  }
}
```

响应（失败 404）：

```json
{
  "code": 404,
  "message": "工单不存在",
  "data": null
}
```

### 3.9 POST /api/tickets/{ticket_id}/claim

用途：接取工单，对应 P03。

路径参数：

| 参数 | 类型 | 示例 |
|---|---|---|
| `ticket_id` | string | `TK-1005` |

请求体：

```json
{
  "employee_id": "user_001"
}
```

响应（成功 200）：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "ticket": {
      "id": "TK-1005",
      "status": "processing",
      "assignee_id": "user_001",
      "assignee_name": "客服一组员工",
      "updated_at": "2026-05-23T14:35:00+08:00"
    }
  }
}
```

响应（失败 400）：

```json
{
  "code": 400,
  "message": "工单已被接取",
  "data": null
}
```

### 3.10 POST /api/tickets/{ticket_id}/complete

用途：完成工单，对应 P05。

路径参数：

| 参数 | 类型 | 示例 |
|---|---|---|
| `ticket_id` | string | `TK-1005` |

请求体：

```json
{
  "employee_id": "user_001",
  "summary": "已告知客户支付状态延迟原因，并提供处理建议。"
}
```

响应（成功 200）：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "ticket": {
      "id": "TK-1005",
      "status": "completed",
      "completed_at": "2026-05-23T15:10:00+08:00"
    }
  }
}
```

响应（失败 403）：

```json
{
  "code": 403,
  "message": "只能完成当前账号已接取的工单",
  "data": null
}
```

### 3.11 GET /api/tickets/{ticket_id}/messages

用途：获取工单会话记录，对应 P05。

路径参数：

| 参数 | 类型 | 示例 |
|---|---|---|
| `ticket_id` | string | `TK-1005` |

请求体：无

响应（成功 200）：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [
      {
        "id": "msg_001",
        "ticket_id": "TK-1005",
        "sender": "customer",
        "sender_name": "张三",
        "content": "你好，我刚刚购买了年费会员，但是没有生效。",
        "created_at": "2026-05-23T14:32:00+08:00"
      },
      {
        "id": "msg_002",
        "ticket_id": "TK-1005",
        "sender": "bot",
        "sender_name": "系统回复",
        "content": "您好，系统可能存在网络延迟，请您提供一下订单号。",
        "created_at": "2026-05-23T14:33:00+08:00"
      }
    ]
  }
}
```

响应（失败 404）：

```json
{
  "code": 404,
  "message": "工单不存在",
  "data": null
}
```

### 3.12 POST /api/tickets/{ticket_id}/messages

用途：员工发送一条工单回复，对应 P05。

路径参数：

| 参数 | 类型 | 示例 |
|---|---|---|
| `ticket_id` | string | `TK-1005` |

请求体：

```json
{
  "content": "您好，已经为您查询到订单状态。系统暂未同步到账状态，请您提供支付宝账单流水截图，我们会继续核实。",
  "used_assistant_answer_id": "answer_001"
}
```

响应（成功 200）：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "message": {
      "id": "msg_003",
      "ticket_id": "TK-1005",
      "sender": "employee",
      "sender_name": "客服一组员工",
      "content": "您好，已经为您查询到订单状态。系统暂未同步到账状态，请您提供支付宝账单流水截图，我们会继续核实。",
      "created_at": "2026-05-23T14:40:00+08:00"
    }
  }
}
```

响应（失败 400）：

```json
{
  "code": 400,
  "message": "回复内容不能为空",
  "data": null
}
```

### 3.13 POST /api/assistant/ask

用途：AI 快速问答、工单建议回复、智能问答调试，对应 P02、P05、P09。

请求体：

```json
{
  "question": "退款多久到账？",
  "scene": "ticket",
  "ticket_id": "TK-1005",
  "conversation_id": "debug_session_001",
  "context_messages": [
    {
      "sender": "customer",
      "content": "订单已经超过 3 天还没到账。"
    }
  ]
}
```

字段说明：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `question` | string | 是 | 员工输入或客户问题 |
| `scene` | string | 是 | `quick` / `ticket` / `debug` |
| `ticket_id` | string | 否 | 工单详情场景传入 |
| `conversation_id` | string | 否 | 调试页多轮上下文标识 |
| `context_messages` | array | 否 | 最近上下文，最多 3 轮 |

响应（成功 200，QA 直接答案）：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "answer": {
      "answer_id": "answer_001",
      "answer_type": "qa_direct",
      "answer": "正常情况下，退款会在 1-3 个工作日内原路退回您的支付账户。",
      "confidence": 0.98,
      "missing_fields": [],
      "references": [
        {
          "type": "qa",
          "source_id": "qa_001",
          "title": "退款到账时间说明",
          "snippet": "审核通过后，资金将在 1-3 个工作日内原路返回。",
          "score": 0.98
        }
      ],
      "context_messages_used": 1
    }
  }
}
```

响应（成功 200，反问）：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "answer": {
      "answer_id": "answer_002",
      "answer_type": "clarification",
      "answer": "请问您是通过哪个渠道支付的？不同渠道的超期处理方式略有不同。",
      "confidence": 0.66,
      "missing_fields": [
        "支付渠道"
      ],
      "references": [],
      "context_messages_used": 2
    }
  }
}
```

响应（失败 500）：

```json
{
  "code": 500,
  "message": "模型服务暂时不可用",
  "data": null
}
```

### 3.14 GET /api/knowledge/overview

用途：知识库总览统计，对应 P06。

请求体：无

响应（成功 200）：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "qa_count": 42,
    "enabled_qa_count": 39,
    "document_count": 7,
    "completed_document_count": 6,
    "latest_updated_at": "2026-05-23T11:02:00+08:00"
  }
}
```

响应（失败 401）：

```json
{
  "code": 401,
  "message": "登录状态已失效",
  "data": null
}
```

### 3.15 GET /api/knowledge/recent

用途：最近知识列表，对应 P06。

查询参数：

| 参数 | 类型 | 必填 | 示例 | 说明 |
|---|---|---|---|---|
| `limit` | integer | 否 | `5` | 返回数量 |

请求体：无

响应（成功 200）：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [
      {
        "type": "qa",
        "id": "qa_001",
        "title": "退款多久到账？",
        "status": "enabled",
        "updated_at": "2026-05-23T10:00:00+08:00"
      },
      {
        "type": "document",
        "id": "doc_001",
        "title": "售后政策及退款流程.pdf",
        "status": "completed",
        "updated_at": "2026-05-23T11:02:00+08:00"
      }
    ]
  }
}
```

响应（失败 400）：

```json
{
  "code": 400,
  "message": "limit 必须为 1 到 20 的整数",
  "data": null
}
```

### 3.16 GET /api/knowledge/qa

用途：查询 QA 列表，对应 P07。

查询参数：

| 参数 | 类型 | 必填 | 示例 | 说明 |
|---|---|---|---|---|
| `keyword` | string | 否 | `退款` | 按问题或答案搜索 |
| `status` | string | 否 | `enabled` | `enabled` / `disabled` |
| `page` | integer | 否 | `1` | 页码 |
| `page_size` | integer | 否 | `20` | 每页数量 |

请求体：无

响应（成功 200）：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [
      {
        "id": "qa_001",
        "question": "退款多久到账？",
        "answer": "正常情况下，退款会在 1-3 个工作日内原路退回您的支付账户。",
        "status": "enabled",
        "created_at": "2026-05-23T10:00:00+08:00",
        "updated_at": "2026-05-23T10:00:00+08:00"
      }
    ],
    "total": 1,
    "page": 1,
    "page_size": 20
  }
}
```

响应（失败 400）：

```json
{
  "code": 400,
  "message": "status 参数不合法",
  "data": null
}
```

### 3.17 POST /api/knowledge/qa

用途：新增 QA，对应 P07。

请求体：

```json
{
  "question": "退款多久到账？",
  "answer": "正常情况下，退款会在 1-3 个工作日内原路退回您的支付账户。",
  "status": "enabled"
}
```

响应（成功 200）：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "qa": {
      "id": "qa_001",
      "question": "退款多久到账？",
      "answer": "正常情况下，退款会在 1-3 个工作日内原路退回您的支付账户。",
      "status": "enabled",
      "created_at": "2026-05-23T10:00:00+08:00",
      "updated_at": "2026-05-23T10:00:00+08:00"
    },
    "embedding_status": "completed"
  }
}
```

响应（失败 400）：

```json
{
  "code": 400,
  "message": "问题和答案不能为空",
  "data": null
}
```

### 3.18 PUT /api/knowledge/qa/{qa_id}

用途：编辑 QA，对应 P07。

路径参数：

| 参数 | 类型 | 示例 |
|---|---|---|
| `qa_id` | string | `qa_001` |

请求体：

```json
{
  "question": "退款一般多久到账？",
  "answer": "正常情况下，退款会在 1-3 个工作日内原路退回您的支付账户；节假日可能顺延。",
  "status": "enabled"
}
```

响应（成功 200）：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "qa": {
      "id": "qa_001",
      "question": "退款一般多久到账？",
      "answer": "正常情况下，退款会在 1-3 个工作日内原路退回您的支付账户；节假日可能顺延。",
      "status": "enabled",
      "created_at": "2026-05-23T10:00:00+08:00",
      "updated_at": "2026-05-23T10:20:00+08:00"
    },
    "embedding_status": "completed"
  }
}
```

响应（失败 404）：

```json
{
  "code": 404,
  "message": "QA 不存在",
  "data": null
}
```

### 3.19 DELETE /api/knowledge/qa/{qa_id}

用途：删除 QA，对应 P07。

路径参数：

| 参数 | 类型 | 示例 |
|---|---|---|
| `qa_id` | string | `qa_001` |

请求体：无

响应（成功 200）：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "deleted": true,
    "qa_id": "qa_001"
  }
}
```

响应（失败 404）：

```json
{
  "code": 404,
  "message": "QA 不存在",
  "data": null
}
```

### 3.20 GET /api/documents

用途：查询文档入库列表，对应 P08。

查询参数：

| 参数 | 类型 | 必填 | 示例 | 说明 |
|---|---|---|---|---|
| `keyword` | string | 否 | `售后` | 按文档名称搜索 |
| `status` | string | 否 | `completed` | `processing` / `completed` / `failed` |
| `page` | integer | 否 | `1` | 页码 |
| `page_size` | integer | 否 | `20` | 每页数量 |

请求体：无

响应（成功 200）：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [
      {
        "id": "doc_001",
        "name": "售后政策及退款流程.pdf",
        "status": "completed",
        "chunk_count": 12,
        "uploaded_by": "客服一组员工",
        "created_at": "2026-05-23T11:00:00+08:00",
        "updated_at": "2026-05-23T11:02:00+08:00"
      }
    ],
    "total": 1,
    "page": 1,
    "page_size": 20
  }
}
```

响应（失败 400）：

```json
{
  "code": 400,
  "message": "status 参数不合法",
  "data": null
}
```

### 3.21 POST /api/documents

用途：上传文档并创建入库任务，对应 P08。

请求体：`multipart/form-data`

| 字段 | 类型 | 必填 | 示例 | 说明 |
|---|---|---|---|---|
| `file` | binary | 是 | `售后政策及退款流程.pdf` | 文档文件 |
| `name` | string | 否 | `售后政策及退款流程.pdf` | 展示名称 |

响应（成功 200）：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "document": {
      "id": "doc_001",
      "name": "售后政策及退款流程.pdf",
      "status": "processing",
      "chunk_count": 0,
      "uploaded_by": "客服一组员工",
      "created_at": "2026-05-23T11:00:00+08:00",
      "updated_at": "2026-05-23T11:00:00+08:00"
    }
  }
}
```

响应（失败 400）：

```json
{
  "code": 400,
  "message": "文件不能为空",
  "data": null
}
```

### 3.22 GET /api/documents/{document_id}

用途：获取单个文档入库状态，对应 P08、P09。

路径参数：

| 参数 | 类型 | 示例 |
|---|---|---|
| `document_id` | string | `doc_001` |

请求体：无

响应（成功 200）：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "document": {
      "id": "doc_001",
      "name": "售后政策及退款流程.pdf",
      "status": "completed",
      "chunk_count": 12,
      "uploaded_by": "客服一组员工",
      "created_at": "2026-05-23T11:00:00+08:00",
      "updated_at": "2026-05-23T11:02:00+08:00"
    }
  }
}
```

响应（失败 404）：

```json
{
  "code": 404,
  "message": "文档不存在",
  "data": null
}
```

### 3.23 DELETE /api/documents/{document_id}

用途：删除文档并使其不再参与检索，对应 P08。

路径参数：

| 参数 | 类型 | 示例 |
|---|---|---|
| `document_id` | string | `doc_001` |

请求体：无

响应（成功 200）：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "deleted": true,
    "document_id": "doc_001"
  }
}
```

响应（失败 404）：

```json
{
  "code": 404,
  "message": "文档不存在",
  "data": null
}
```

### 3.24 GET /api/settings/account

用途：账号与基础设置，对应 P10。

请求体：无

响应（成功 200）：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "user": {
      "id": "user_001",
      "name": "客服一组员工",
      "username": "agent01",
      "created_at": "2026-05-23T09:00:00+08:00"
    },
    "system": {
      "database": "SQLite",
      "model_provider": "百炼",
      "chat_model": "qwen-plus",
      "embedding_model": "text-embedding-v4",
      "embedding_dimensions": 1024,
      "api_key_configured": true
    }
  }
}
```

响应（失败 401）：

```json
{
  "code": 401,
  "message": "登录状态已失效",
  "data": null
}
```

## 4. 页面接口映射

| 页面 | 主要接口 |
|---|---|
| P01 登录页 | `POST /api/auth/login`、`GET /api/auth/me`、`POST /api/auth/logout` |
| P02 客服工作台 | `GET /api/dashboard/summary`、`GET /api/dashboard/tickets`、`POST /api/assistant/ask` |
| P03 工单池 | `GET /api/tickets`、`POST /api/tickets/{ticket_id}/claim` |
| P04 我的工单 | `GET /api/tickets`、`GET /api/tickets/{ticket_id}` |
| P05 工单详情 | `GET /api/tickets/{ticket_id}`、`GET /api/tickets/{ticket_id}/messages`、`POST /api/tickets/{ticket_id}/messages`、`POST /api/tickets/{ticket_id}/complete`、`POST /api/assistant/ask` |
| P06 知识库总览 | `GET /api/knowledge/overview`、`GET /api/knowledge/recent` |
| P07 QA 库管理 | `GET /api/knowledge/qa`、`POST /api/knowledge/qa`、`PUT /api/knowledge/qa/{qa_id}`、`DELETE /api/knowledge/qa/{qa_id}` |
| P08 文档入库 | `GET /api/documents`、`POST /api/documents`、`GET /api/documents/{document_id}`、`DELETE /api/documents/{document_id}` |
| P09 智能问答调试 | `POST /api/assistant/ask`、`GET /api/knowledge/qa`、`GET /api/documents` |
| P10 账号与基础设置 | `GET /api/settings/account`、`POST /api/auth/logout` |

## 5. Mock 数据要求

- 前端 Mock 数据必须集中放在 `frontend/src/mocks/`。
- Mock 字段名、枚举值、嵌套结构必须与本文件一致。
- Mock 中可以使用演示 token，但不得写入真实 API Key、密码或外部平台凭证。
- AI 相关 Mock 只能模拟 `answer_type`、`answer`、`references` 等业务可见字段，不展示模型版本、请求号、原始上下文或内部链路。
