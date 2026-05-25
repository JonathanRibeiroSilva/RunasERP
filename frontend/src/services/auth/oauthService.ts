import { env } from '@/config/env';
import { api } from '@/services/api/axios';
import { tokenService } from './tokenService';
import type { LoginResponse } from '@/types/auth';

export type OAuthProvider = 'google' | 'microsoft';

interface OAuthConfig {
  clientId: string;
  redirectUri: string;
  scope: string;
  authUrl: string;
}

// Configurações OAuth por provider
const oauthConfigs: Record<OAuthProvider, OAuthConfig> = {
  google: {
    clientId: env.oauth.googleClientId,
    redirectUri: env.oauth.redirectUri,
    scope: 'openid profile email',
    authUrl: 'https://accounts.google.com/o/oauth2/v2/auth',
  },
  microsoft: {
    clientId: env.oauth.microsoftClientId,
    redirectUri: env.oauth.redirectUri,
    scope: 'openid profile email User.Read',
    authUrl: `https://login.microsoftonline.com/${env.oauth.microsoftTenantId}/oauth2/v2.0/authorize`,
  },
};

export const oauthService = {
  /**
   * Inicia o fluxo OAuth redirecionando para o provider
   */
  initiateOAuth(provider: OAuthProvider): void {
    const config = oauthConfigs[provider];

    if (!config.clientId) {
      throw new Error(`${provider} OAuth não está configurado. Configure VITE_${provider.toUpperCase()}_CLIENT_ID`);
    }

    // Gerar state para CSRF protection
    const state = this.generateState();
    sessionStorage.setItem('oauth_state', state);
    sessionStorage.setItem('oauth_provider', provider);

    // Construir URL de autorização
    const params = new URLSearchParams({
      client_id: config.clientId,
      redirect_uri: config.redirectUri,
      response_type: 'code',
      scope: config.scope,
      state,
      ...(provider === 'google' && {
        access_type: 'offline',
        prompt: 'consent',
      }),
    });

    const authUrl = `${config.authUrl}?${params.toString()}`;

    // Redirecionar para o provider
    window.location.href = authUrl;
  },

  /**
   * Processa o callback do OAuth
   */
  async handleOAuthCallback(code: string, state: string): Promise<LoginResponse> {
    // Verificar state (CSRF protection)
    const savedState = sessionStorage.getItem('oauth_state');
    const provider = sessionStorage.getItem('oauth_provider') as OAuthProvider;

    if (!savedState || savedState !== state) {
      throw new Error('Estado OAuth inválido. Possível ataque CSRF.');
    }

    if (!provider) {
      throw new Error('Provider OAuth não encontrado.');
    }

    // Limpar state do sessionStorage
    sessionStorage.removeItem('oauth_state');
    sessionStorage.removeItem('oauth_provider');

    // Enviar code para o backend
    const response = await api.post<LoginResponse>(`/auth/oauth/${provider}`, {
      code,
      redirect_uri: env.oauth.redirectUri,
    });

    const { access_token, refresh_token } = response.data;

    // Salvar tokens
    tokenService.setAccessToken(access_token);
    tokenService.setRefreshToken(refresh_token);

    return response.data;
  },

  /**
   * Gera um state aleatório para CSRF protection
   */
  generateState(): string {
    const array = new Uint8Array(32);
    crypto.getRandomValues(array);
    return Array.from(array, (byte) => byte.toString(16).padStart(2, '0')).join('');
  },

  /**
   * Verifica se OAuth está configurado para um provider
   */
  isConfigured(provider: OAuthProvider): boolean {
    return !!oauthConfigs[provider].clientId;
  },

  /**
   * Retorna os providers configurados
   */
  getConfiguredProviders(): OAuthProvider[] {
    return (Object.keys(oauthConfigs) as OAuthProvider[]).filter((provider) =>
      this.isConfigured(provider)
    );
  },
};
