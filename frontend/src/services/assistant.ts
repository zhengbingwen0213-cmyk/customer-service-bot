import axios, { type AxiosResponse } from 'axios'

import api from '@/services/api'
import type { ApiResponse } from '@/types/api'
import type {
  AssistantAnswerDto,
  AssistantAskRequest,
  AssistantAskResponseData,
} from '@/types/assistant'
import { isMockApiEnabled } from '@/utils/runtime'

export async function getAssistantIntroAnswer(): Promise<AssistantAnswerDto> {
  const { mockGetAssistantIntroAnswer } = await import('@/mocks')
  return mockGetAssistantIntroAnswer()
}

export async function askAssistant(
  payload: AssistantAskRequest,
): Promise<ApiResponse<AssistantAskResponseData>> {
  if (isMockApiEnabled()) {
    const { mockAskAssistant } = await import('@/mocks')
    return mockAskAssistant(payload)
  }

  return unwrapApiResponse(api.post('/assistant/ask', payload))
}

async function unwrapApiResponse<TData>(
  request: Promise<AxiosResponse<ApiResponse<TData>>>,
): Promise<ApiResponse<TData>> {
  try {
    const response = await request
    return response.data
  } catch (error) {
    if (axios.isAxiosError<ApiResponse<TData>>(error) && error.response?.data) {
      return error.response.data
    }
    throw error
  }
}
