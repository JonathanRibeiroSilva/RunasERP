import { api } from '@/services/api/axios';
import { tokenService } from './tokenService';
import type { LoginRequest, LoginResponse, User } from '@/types/auth';

export const authService = {
  async login(email: string, password: string): Promise<LoginResponse> {
    // API espera form data para OAuth2
    const formData = new URLSearchParams();
    formData.append('username', email);
    formData.append('password', password);

    const response = await api.post<LoginResponse>('/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });

    const { access_token, refresh_token } = response.data;

    // Salvar tokens
    tokenService.setAccessToken(access_token);
    tokenService.setRefreshToken(refresh_token);

    return response.data;
  },

  async logout(): Promise<void> {
    try {
      await api.post('/auth/logout');
    } catch (error) {
      // Ignorar erros de logout
      console.error('Erro ao fazer logout:', error);
    } finally {
      // Sempre limpar tokens localmente
      tokenService.clearTokens();
    }
  },

  async getCurrentUser(): Promise<User> {
    const response = await api.get<User>('/auth/me');
    return response.data;
  },

  async refreshToken(refreshToken: string): Promise<string> {
    const response = await api.post<{ access_token: string }>('/auth/refresh', {
      refresh_token: refreshToken,
    });

    const { access_token } = response.data;
    tokenService.setAccessToken(access_token);

    return access_token;
  },
};
