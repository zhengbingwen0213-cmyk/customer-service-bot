import type { ApiResponse } from '@/types/api'
import type {
  AssistantAnswerDto,
  AssistantAskRequest,
  AssistantAskResponseData,
  AssistantReferenceDto,
} from '@/types/assistant'

function wait() {
  return new Promise((resolve) => {
    window.setTimeout(resolve, 180)
  })
}

function toAssistantReferenceDto(reference: AssistantReferenceDto): AssistantReferenceDto {
  return {
    type: reference.type,
    source_id: reference.source_id,
    title: reference.title,
    snippet: reference.snippet,
    score: reference.score,
  }
}

function toAssistantAnswerDto(answer: AssistantAnswerDto): AssistantAnswerDto {
  return {
    answer_id: answer.answer_id,
    answer_type: answer.answer_type,
    answer: answer.answer,
    confidence: answer.confidence,
    missing_fields: [...answer.missing_fields],
    references: answer.references.map(toAssistantReferenceDto),
    context_messages_used: answer.context_messages_used,
  }
}

export function mockGetAssistantIntroAnswer(): AssistantAnswerDto {
  return toAssistantAnswerDto({
    answer_id: 'answer_intro',
    answer_type: 'generated',
    answer: '建议先核对订单状态，并引用相关知识。',
    confidence: 0.72,
    missing_fields: [],
    references: [],
    context_messages_used: 0,
  })
}

export async function mockAskAssistant(
  request: AssistantAskRequest,
): Promise<ApiResponse<AssistantAskResponseData>> {
  await wait()

  if (!request.question.trim()) {
    return {
      code: 400,
      message: '问题不能为空',
      data: null,
    }
  }

  if (request.scene === 'debug') {
    const question = request.question.trim()
    const contextUsed = Math.min(request.context_messages?.length ?? 0, 3)
    const normalizedQuestion = question.toLowerCase()
    const hasRefundContext =
      normalizedQuestion.includes('退款') ||
      (request.context_messages?.some((message) => message.content.includes('退款')) ?? false)

    if (
      normalizedQuestion.includes('超过') ||
      normalizedQuestion.includes('超期') ||
      (hasRefundContext && normalizedQuestion.includes('怎么办'))
    ) {
      const answer = toAssistantAnswerDto({
        answer_id: `answer_debug_${Date.now()}`,
        answer_type: 'clarification',
        answer: '请问您是通过哪个渠道支付的？不同渠道的超期处理方式略有不同。',
        confidence: 0.66,
        missing_fields: ['支付渠道'],
        references: [],
        context_messages_used: contextUsed,
      })

      return {
        code: 200,
        message: 'success',
        data: {
          answer,
        },
      }
    }

    if (
      normalizedQuestion.includes('支付宝') ||
      normalizedQuestion.includes('微信') ||
      normalizedQuestion.includes('渠道') ||
      normalizedQuestion.includes('会员') ||
      normalizedQuestion.includes('发票')
    ) {
      const references: AssistantReferenceDto[] = [
        {
          type: 'document',
          source_id: 'doc_001',
          title: '售后政策说明.pdf',
          snippet: '异常订单核实后可手动补单；无法到账时，款项会在 1-3 个工作日内原路退回。',
          score: 0.91,
        },
      ]
      const answer = toAssistantAnswerDto({
        answer_id: `answer_debug_${Date.now()}`,
        answer_type: 'generated',
        answer:
          '已结合最近上下文，建议先核对支付渠道流水与订单状态。如确认渠道已扣款但系统未同步，可登记流水并转人工补单；无法补单时按退款流程处理。',
        confidence: 0.88,
        missing_fields: [],
        references,
        context_messages_used: contextUsed,
      })

      return {
        code: 200,
        message: 'success',
        data: {
          answer,
        },
      }
    }

    const reference: AssistantReferenceDto = {
      type: 'qa',
      source_id: 'qa_002',
      title: '退款到账时间说明',
      snippet: '审核通过后，资金将在 1-3 个工作日内原路返回。',
      score: 0.98,
    }
    const answer = toAssistantAnswerDto({
      answer_id: `answer_debug_${Date.now()}`,
      answer_type: 'qa_direct',
      answer: '正常情况下，退款会在 1-3 个工作日内原路退回您的支付账户。如遇节假日可能会有顺延。',
      confidence: 0.98,
      missing_fields: [],
      references: [reference],
      context_messages_used: contextUsed,
    })

    return {
      code: 200,
      message: 'success',
      data: {
        answer,
      },
    }
  }

  if (request.scene === 'ticket') {
    const references: AssistantReferenceDto[] = [
      {
        type: 'qa',
        source_id: 'qa_payment_delay',
        title: '问答：支付状态延迟处理办法',
        snippet: '支付渠道已扣款但业务状态未同步时，先核对渠道流水，再进行手动补单或原路退款说明。',
        score: 0.98,
      },
      {
        type: 'document',
        source_id: 'doc_refund_policy',
        title: '文档：售后政策及退款流程.pdf',
        snippet: '异常订单核实后可手动补单；无法到账时，款项会在 1-3 个工作日内原路退回。',
        score: 0.91,
      },
    ]

    const answer = toAssistantAnswerDto({
      answer_id: 'answer_ticket_001',
      answer_type: 'generated',
      answer:
        '您好！已经为您查询到订单 20260523001 的支付状态。目前系统显示支付宝确实已扣款，但由于支付网关的偶发延迟，我们的系统暂未同步到账状态。\n\n建议您核对一下支付宝的账单流水记录截图发送给我们。我们将立刻为您手动补单并激活年费会员。如果一直未到账，款项会在 1-3 个工作日内原路退回。',
      confidence: 0.92,
      missing_fields: [],
      references,
      context_messages_used: Math.min(request.context_messages?.length ?? 0, 3),
    })

    return {
      code: 200,
      message: 'success',
      data: {
        answer,
      },
    }
  }

  const reference: AssistantReferenceDto = {
    type: 'qa',
    source_id: 'qa_001',
    title: '退款到账时间说明',
    snippet: '审核通过后，资金将在 1-3 个工作日内原路返回。',
    score: 0.98,
  }

  const answer = toAssistantAnswerDto({
    answer_id: 'answer_001',
    answer_type: 'qa_direct',
    answer: '正常情况下，退款会在 1-3 个工作日内原路退回您的支付账户。',
    confidence: 0.98,
    missing_fields: [],
    references: [reference],
    context_messages_used: request.context_messages?.length ?? 0,
  })

  return {
    code: 200,
    message: 'success',
    data: {
      answer,
    },
  }
}
