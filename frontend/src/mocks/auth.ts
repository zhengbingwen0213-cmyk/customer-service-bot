import type { ApiResponse } from '@/types/api'
import type {
  AuthMeResponseData,
  LoginRequest,
  LoginResponseData,
  LogoutRequest,
  LogoutResponseData,
  UserDto,
} from '@/types/auth'
import type { SettingsAccountResponseData, SystemSettingsDto } from '@/types/settings'

interface MockSystemEntity {
  database: string
  model_provider: string
  chat_model: string
  embedding_model: string
  embedding_dimensions: number
  api_key_configured: boolean
}

interface MockUserEntity {
  id: string
  name: string
  username: string
  password: string
  created_at: string
  system: MockSystemEntity
}

export const MOCK_ACCESS_TOKEN = 'access_token_demo'

const mockUsers: MockUserEntity[] = [
  {
    id: 'user_001',
    name: '客服一组员工',
    username: 'agent01',
    password: 'password123',
    created_at: '2026-05-23T09:00:00+08:00',
    system: {
      database: 'SQLite',
      model_provider: '百炼',
      chat_model: 'qwen-plus',
      embedding_model: 'text-embedding-v4',
      embedding_dimensions: 1024,
      api_key_configured: true,
    },
  },
]

function wait() {
  return new Promise((resolve) => {
    window.setTimeout(resolve, 120)
  })
}

function toUserDto(user: MockUserEntity): UserDto {
  return {
    id: user.id,
    name: user.name,
    username: user.username,
    created_at: user.created_at,
  }
}

function toSystemSettingsDto(system: MockSystemEntity): SystemSettingsDto {
  return {
    database: system.database,
    model_provider: system.model_provider,
    chat_model: system.chat_model,
    embedding_model: system.embedding_model,
    embedding_dimensions: system.embedding_dimensions,
    api_key_configured: system.api_key_configured,
  }
}

function findUserByToken(accessToken: string | null): MockUserEntity | undefined {
  if (accessToken !== MOCK_ACCESS_TOKEN) return undefined
  return mockUsers[0]
}

export async function mockLogin(
  request: LoginRequest,
): Promise<ApiResponse<LoginResponseData>> {
  await wait()

  const user = mockUsers.find(
    (item) => item.username === request.username && item.password === request.password,
  )

  if (!user) {
    return {
      code: 401,
      message: '用户名或密码错误',
      data: null,
    }
  }

  return {
    code: 200,
    message: 'success',
    data: {
      access_token: MOCK_ACCESS_TOKEN,
      token_type: 'Bearer',
      expires_in: 86400,
      user: toUserDto(user),
    },
  }
}

export async function mockGetCurrentUser(
  accessToken: string | null,
): Promise<ApiResponse<AuthMeResponseData>> {
  await wait()

  const user = findUserByToken(accessToken)
  if (!user) {
    return {
      code: 401,
      message: '登录状态已失效',
      data: null,
    }
  }

  return {
    code: 200,
    message: 'success',
    data: {
      user: toUserDto(user),
    },
  }
}

export async function mockLogout(
  request: LogoutRequest,
): Promise<ApiResponse<LogoutResponseData>> {
  await wait()

  if (!findUserByToken(request.access_token)) {
    return {
      code: 401,
      message: '登录状态已失效',
      data: null,
    }
  }

  return {
    code: 200,
    message: 'success',
    data: {
      logged_out: true,
    },
  }
}

export async function mockGetAccountSettings(
  accessToken: string | null,
): Promise<ApiResponse<SettingsAccountResponseData>> {
  await wait()

  const user = findUserByToken(accessToken)
  if (!user) {
    return {
      code: 401,
      message: '登录状态已失效',
      data: null,
    }
  }

  return {
    code: 200,
    message: 'success',
    data: {
      user: toUserDto(user),
      system: toSystemSettingsDto(user.system),
    },
  }
}
