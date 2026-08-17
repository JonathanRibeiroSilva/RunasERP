import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';
import { env } from '@/config/env';
import { tokenService } from '@/services/auth/tokenService';
import { sleep } from '@/utils/errorLogger';
import type { ApiError } from '@/types/common';

// Retry window for the seconds a deploy leaves the gateway unreachable.
const DEPLOY_WINDOW_STATUSES = [502, 503, 504];
const IDEMPOTENT_METHODS = ['get', 'head', 'options'];
const MAX_DEPLOY_RETRIES = 3;

// Criar instância do Axios
export const api = axios.create({
  baseURL: env.apiUrl,
  timeout: env.apiTimeout,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // Importante: envia cookies em requisições cross-origin
});

// Interceptor de Request - Cookies são enviados automaticamente
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // Cookies HTTP-only são enviados automaticamente pelo navegador
    // devido ao withCredentials: true
    // 
    // O header X-Empresa-Id é adicionado pelo API Gateway
    // a partir do token JWT do usuário autenticado
    
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

    // A deploy swaps the gateway container for a few seconds and the edge answers
    // 502/503/504 meanwhile. Idempotent reads wait it out instead of surfacing an
    // error, so a user mid-session sees a slow screen rather than a failure.
    //
    // Narrower than utils/errorLogger's isRetryableError on purpose: that one
    // retries every 500+, and a genuine 500 is an application bug, so retrying it
    // only triples the load and delays the error the user needs to see.
    //
    // Writes are deliberately excluded: the API has no idempotency keys, so a
    // retried POST /vendas is a duplicated sale. Do not widen IDEMPOTENT_METHODS
    // without adding one.
    const retryable = error.config as InternalAxiosRequestConfig & { _deployRetries?: number };
    const method = (retryable?.method ?? 'get').toLowerCase();
    const attempt = (retryable?._deployRetries ?? 0) + 1;

    if (
      DEPLOY_WINDOW_STATUSES.includes(error.response?.status ?? 0) &&
      IDEMPOTENT_METHODS.includes(method) &&
      attempt <= MAX_DEPLOY_RETRIES
    ) {
      retryable._deployRetries = attempt;
      // 1s + 2s + 3s: covers an nginx swap and most gateway boots.
      await sleep(attempt * 1000);
      return api(retryable);
    }

    // Outros erros
    return Promise.reject(error);
  }
);

// Helper para extrair mensagem de erro (com fallback amigável opcional)
export const getErrorMessage = (error: unknown, fallback = 'Erro desconhecido'): string => {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<ApiError>;
    return axiosError.response?.data?.detail || axiosError.message || fallback;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return fallback;
};

// Helper para extrair o status HTTP de um erro (quando disponível)
export const getErrorStatus = (error: unknown): number | undefined => {
  return axios.isAxiosError(error) ? error.response?.status : undefined;
};
