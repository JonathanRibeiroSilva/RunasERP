/**
 * Error Logging Utility
 * 
 * Fornece logging estruturado de erros para facilitar debugging e monitoramento.
 * Futuramente pode ser integrado com Sentry ou similar.
 */

export interface ErrorLogContext {
  component: string;
  action: string;
  metadata?: Record<string, any>;
}

export interface ErrorLogData {
  timestamp: string;
  component: string;
  action: string;
  message: string;
  status?: number;
  detail?: any;
  stack?: string;
  [key: string]: any;
}

/**
 * Loga erro de forma estruturada no console.
 * 
 * @param error - Erro capturado (pode ser Error, AxiosError, ou any)
 * @param context - Contexto do erro (componente, ação, metadata)
 */
export function logCheckoutError(
  error: any,
  context: ErrorLogContext
): void {
  const errorData: ErrorLogData = {
    timestamp: new Date().toISOString(),
    component: context.component,
    action: context.action,
    message: error.message || 'Erro desconhecido',
    status: error.response?.status,
    detail: error.response?.data?.detail,
    stack: error.stack,
    ...context.metadata
  };

  console.error(`[${context.component} - ${context.action}]`, errorData);

  // Futuro: Enviar para Sentry ou outro serviço de monitoramento
  // if (window.Sentry) {
  //   window.Sentry.captureException(error, { extra: errorData });
  // }
}

/**
 * Determina se um erro é retryable (vale a pena tentar novamente).
 * 
 * @param error - Erro capturado
 * @returns true se o erro for retryable (500+, timeout, network)
 */
export function isRetryableError(error: any): boolean {
  // Erros de servidor (500+)
  if (error.response?.status >= 500) return true;

  // Timeout ou erro de rede
  if (error.code === 'ECONNABORTED' || !error.response) return true;

  // Erros 4xx não são retryable (exceto 429 - rate limit)
  if (error.response?.status === 429) return true;

  return false;
}

/**
 * Extrai mensagem de erro amigável do objeto de erro da API.
 * 
 * @param error - Erro capturado
 * @returns Mensagem de erro formatada para o usuário
 */
export function extractErrorMessage(error: any): string {
  if (!error.response?.data) {
    return error.message || 'Erro desconhecido';
  }

  const { detail } = error.response.data;

  // Array de erros de validação
  if (Array.isArray(detail)) {
    return detail
      .map((err: any) => err.msg || err.message || JSON.stringify(err))
      .join('; ');
  }

  // String simples
  if (typeof detail === 'string') {
    return detail;
  }

  // Objeto com msg ou message
  if (typeof detail === 'object' && detail) {
    return detail.msg || detail.message || JSON.stringify(detail);
  }

  return error.message || 'Erro ao processar requisição';
}

/**
 * Sleep/delay utility para exponential backoff.
 * 
 * @param ms - Milissegundos para aguardar
 */
export function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}
