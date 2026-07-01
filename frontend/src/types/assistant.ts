export type AssistantScene = 'quick' | 'ticket' | 'debug'
export type AssistantAnswerType = 'qa_direct' | 'clarification' | 'generated'
export type AssistantReferenceType = 'qa' | 'document'
export type AssistantContextSender = 'customer' | 'employee' | 'bot'

export interface AssistantContextMessage {
  sender: AssistantContextSender
  content: string
}

export interface AssistantAskRequest {
  question: string
  scene: AssistantScene
  ticket_id?: string
  conversation_id?: string
  context_messages?: AssistantContextMessage[]
}

export interface AssistantReferenceDto {
  type: AssistantReferenceType
  source_id: string
  title: string
  snippet: string
  score: number
}

export interface AssistantAnswerDto {
  answer_id: string
  answer_type: AssistantAnswerType
  answer: string
  confidence: number
  missing_fields: string[]
  references: AssistantReferenceDto[]
  context_messages_used: number
}

export interface AssistantAskResponseData {
  answer: AssistantAnswerDto
}
