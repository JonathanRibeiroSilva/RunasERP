// Serviço para gerenciamento de tokens JWT
// NOTA: Os tokens agora são armazenados em HTTP-only cookies pelo backend
// Este serviço mantém compatibilidade mas não é mais necessário para armazenamento

const ACCESS_TOKEN_KEY = 'access_token';
const REFRESH_TOKEN_KEY = 'refresh_token';

export const tokenService = {
  // DEPRECATED: Tokens agora vêm de cookies HTTP-only
  // Mantido para compatibilidade com código legado
  getAccessToken(): string | null {
    return null; // Cookies são enviados automaticamente
  },

  // DEPRECATED: Tokens são definidos pelo backend via cookies
  setAccessToken(_token: string): void {
    // Não faz nada - cookies são gerenciados pelo backend
    console.warn('[tokenService] setAccessToken is deprecated - tokens are now managed via HTTP-only cookies');
  },

  // DEPRECATED: Tokens agora vêm de cookies HTTP-only
  getRefreshToken(): string | null {
    return null; // Cookies são enviados automaticamente
  },

  // DEPRECATED: Tokens são definidos pelo backend via cookies
  setRefreshToken(_token: string): void {
    // Não faz nada - cookies são gerenciados pelo backend
    console.warn('[tokenService] setRefreshToken is deprecated - tokens are now managed via HTTP-only cookies');
  },

  // Limpa tokens do localStorage (legado)
  // Os cookies são limpos pelo backend no logout
  clearTokens(): void {
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
  },

  // Verifica se há tokens (sempre retorna true pois cookies são enviados automaticamente)
  hasTokens(): boolean {
    // Não podemos verificar cookies HTTP-only via JavaScript
    // O backend validará na próxima requisição
    return true;
  },
};

