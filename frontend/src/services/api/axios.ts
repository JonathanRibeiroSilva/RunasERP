import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';
import { env } from '@/config/env';
import { tokenService } from '@/services/auth/tokenService';
import type { ApiError, RefreshTokenResponse } from '@/types/auth';

// Criar instância do Axios
export const api = axios.create({
  baseURL: env.apiUrl,
  timeout: env.apiTimeout,
  headers: {
    'Content-Type': 'application/json',
    // Necessário para bypassar o aviso de browser do ngrok em ambiente de dev
    'ngrok-skip-browser-warning': 'true',
  },
  withCredentials: true, // Importante: envia cookies em requisições cross-origin
});

// Flag para evitar múltiplas tentativas de refresh
// DEPRECATED: Com cookies HTTP-only, não é mais necessário
let isRefreshing = false;
let failedQueue: Array<{
  resolve: (value?: unknown) => void;
  reject: (reason?: unknown) => void;
}> = [];

const processQueue = (error: Error | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve();
    }
  });

  failedQueue = [];
};

// Interceptor de Request - Cookies são enviados automaticamente
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // Não precisa mais adicionar token manualmente
    // Os cookies HTTP-only são enviados automaticamente pelo navegador
    // devido ao withCredentials: true
    return config;
  },
  (error: AxiosError) => {
    return Promise.reject(error);
  }
);

// Interceptor de Response - Refresh token automático via cookies
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<ApiError>) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    // Se erro 401 e não é tentativa de refresh
    if (error.response?.status === 401 && !originalRequest._retry) {
      // Não fazer refresh se for requisição de login/register/me
      // /auth/me é chamado durante inicialização e pode retornar 401 legitimamente
      if (
        originalRequest.url?.includes('/auth/login') ||
        originalRequest.url?.includes('/auth/register') ||
        originalRequest.url?.includes('/auth/me')
      ) {
        return Promise.reject(error);
      }

      // Com cookies HTTP-only, o refresh é automático
      // Se chegou aqui com 401, significa que o refresh também falhou
      // Redirecionar para login APENAS se não estamos já na página de login
      tokenService.clearTokens(); // Limpar localStorage legado
      
      // Evitar redirect infinito: só redirecionar se não estamos em /login
      if (!window.location.pathname.includes('/login')) {
        window.location.href = '/login';
      }
      
      return Promise.reject(error);
    }

    // Outros erros
    return Promise.reject(error);
  }
);

// Helper para extrair mensagem de erro
export const getErrorMessage = (error: unknown): string => {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<ApiError>;
    return axiosError.response?.data?.detail || axiosError.message || 'Erro desconhecido';
  }
  if (error instanceof Error) {
    return error.message;
  }
  return 'Erro desconhecido';
};
