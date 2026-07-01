export interface UserDto {
  id: string
  name: string
  username: string
  created_at: string
}

export interface LoginRequest {
  username: string
  password: string
}

export interface LoginResponseData {
  access_token: string
  token_type: 'Bearer'
  expires_in: number
  user: UserDto
}

export interface AuthMeResponseData {
  user: UserDto
}

export interface LogoutRequest {
  access_token: string
}

export interface LogoutResponseData {
  logged_out: boolean
}
