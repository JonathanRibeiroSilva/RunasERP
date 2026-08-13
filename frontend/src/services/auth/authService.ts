import { api } from '@/services/api/axios';
import { tokenService } from './tokenService';
import type { LoginResponse, User } from '@/types/auth';

interface RegisterRequest {
  nome: string;
  email: string;
  senha: string;
}

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

    // Tokens agora são gerenciados via cookies HTTP-only pelo backend
    // Não é necessário salvar manualmente

    return response.data;
  },

  async register(data: RegisterRequest): Promise<User> {
    const response = await api.post<User>('/auth/register', data);
    return response.data;
  },

  async logout(): Promise<void> {
    try {
      // O backend vai limpar os cookies HTTP-only
      await api.post('/auth/logout');
    } catch (error) {
      // Ignorar erros de logout
    } finally {
      // Limpar localStorage legado
      tokenService.clearTokens();
    }
  },

  async getCurrentUser(): Promise<User> {
    const response = await api.get<User>('/auth/me');
    return response.data;
  },

  async refreshToken(_refreshToken: string): Promise<string> {
    // Com cookies HTTP-only, o refresh é automático
    // Este método não é mais necessário mas mantido para compatibilidade
    console.warn('[authService] refreshToken is deprecated with HTTP-only cookies');
    return '';
  },

  async forgotPassword(email: string): Promise<{ message: string; token?: string }> {
    const response = await api.post('/auth/forgot-password', { email });
    return response.data;
  },

  async resetPassword(token: string, nova_senha: string): Promise<{ message: string }> {
    const response = await api.post('/auth/reset-password', { token, nova_senha });
    return response.data;
  },
};
