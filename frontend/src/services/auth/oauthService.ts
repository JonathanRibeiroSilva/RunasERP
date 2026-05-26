import { env } from '@/config/env';
import { api } from '@/services/api/axios';
import { tokenService } from './tokenService';
import type { LoginResponse } from '@/types/auth';

export type OAuthProvider = 'google' | 'microsoft';

interface OAuthInitResponse {
  auth_url: string;
  state: string;
}

export const oauthService = {
  /**
   * Inicia o fluxo OAuth através do backend
   */
  async initiateOAuth(provider: OAuthProvider): Promise<void> {
    try {
      // Chamar backend para obter URL de autorização
      const response = await api.post<OAuthInitResponse>(`/auth/oauth/${provider}`, {
        redirect_uri: env.oauth.redirectUri,
      });

      const { auth_url, state } = response.data;

      // Salvar state no sessionStorage para validação posterior
      sessionStorage.setItem('oauth_state', state);
      sessionStorage.setItem('oauth_provider', provider);

      // Redirecionar para o provider
      window.location.href = auth_url;
    } catch (error) {
      console.error('[OAuth] Erro ao iniciar OAuth:', error);
      throw new Error(`Erro ao iniciar autenticação com ${provider}`);
    }
  },

  /**
   * Processa o callback do OAuth
   */
  async handleOAuthCallback(code: string, state: string): Promise<LoginResponse> {
    // Obter provider do sessionStorage
    const provider = sessionStorage.getItem('oauth_provider') as OAuthProvider;

    // Se não tiver provider no sessionStorage, usar 'google' como padrão
    const finalProvider = provider || 'google';

    // Limpar sessionStorage
    sessionStorage.removeItem('oauth_state');
    sessionStorage.removeItem('oauth_provider');

    try {
      // Enviar code e state para o backend processar
      // O backend vai validar o state no Redis e definir cookies HTTP-only
      const response = await api.post<LoginResponse>(`/auth/oauth/${finalProvider}/callback`, {
        code,
        state,
      });

      const { user } = response.data;

      if (!user) {
        throw new Error('Dados do usuário não retornados pelo servidor');
      }

      // Tokens agora são gerenciados via cookies HTTP-only pelo backend
      // Não é necessário salvar manualmente no localStorage

      return response.data;
    } catch (error) {
      console.error('[OAuth] Erro ao processar callback:', error);
      throw error;
    }
  },

  /**
   * Verifica se OAuth está configurado para um provider
   */
  isConfigured(provider: OAuthProvider): boolean {
    if (provider === 'google') {
      return !!env.oauth.googleClientId;
    }
    if (provider === 'microsoft') {
      return !!env.oauth.microsoftClientId;
    }
    return false;
  },

  /**
   * Retorna os providers configurados
   */
  getConfiguredProviders(): OAuthProvider[] {
    const providers: OAuthProvider[] = [];
    if (this.isConfigured('google')) providers.push('google');
    if (this.isConfigured('microsoft')) providers.push('microsoft');
    return providers;
  },
};
