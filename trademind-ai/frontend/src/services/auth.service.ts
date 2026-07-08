/**
 * services/auth.service.ts
 * T16.2 ✅  Authentication API calls.
 */
import { api } from '@/lib/api'
import type { ApiResponse, LoginResponse, User } from '@/types'

export const authService = {
  register: (data: {
    email: string; username: string; password: string
    confirm_password: string; first_name?: string; last_name?: string
  }) => api.post<ApiResponse<{ user_id: string; email: string }>>('/auth/register/', data),

  verifyEmail: (token: string) =>
    api.post<ApiResponse>('/auth/verify-email/', { token }),

  login: (email: string, password: string, totp_code?: string) =>
    api.post<ApiResponse<LoginResponse>>('/auth/login/', { email, password, totp_code }),

  logout: (refresh_token: string) =>
    api.post('/auth/logout/', { refresh_token }),

  forgotPassword: (email: string) =>
    api.post('/auth/forgot-password/', { email }),

  resetPassword: (token: string, password: string, confirm_password: string) =>
    api.post('/auth/reset-password/', { token, password, confirm_password }),

  changePassword: (current_password: string, new_password: string, confirm_password: string) =>
    api.post('/auth/change-password/', { current_password, new_password, confirm_password }),

  enable2FA: () =>
    api.post<ApiResponse<{ secret: string; qr_code_url: string }>>('/auth/enable-2fa/'),

  confirm2FA: (totp_code: string) =>
    api.post<ApiResponse<{ recovery_codes: string[] }>>('/auth/confirm-2fa/', { totp_code }),

  disable2FA: (password: string, totp_code: string) =>
    api.post('/auth/disable-2fa/', { password, totp_code }),

  getProfile: () =>
    api.get<ApiResponse<User>>('/auth/profile/'),

  updateProfile: (data: Partial<User>) =>
    api.patch<ApiResponse<User>>('/auth/profile/', data),
}
