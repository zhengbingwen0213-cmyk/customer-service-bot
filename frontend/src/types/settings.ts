import type { UserDto } from './auth'

export interface SystemSettingsDto {
  database: string
  model_provider: string
  chat_model: string
  embedding_model: string
  embedding_dimensions: number
  api_key_configured: boolean
}

export interface SettingsAccountResponseData {
  user: UserDto
  system: SystemSettingsDto
}
