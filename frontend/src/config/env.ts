export const env = {
  // API URL - usar variável de ambiente diretamente
  apiUrl: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  apiTimeout: parseInt(import.meta.env.VITE_API_TIMEOUT || '30000'),
  appName: import.meta.env.VITE_APP_NAME || 'Runas',
  appVersion: import.meta.env.VITE_APP_VERSION || '1.0.0',
  enableDevtools: import.meta.env.VITE_ENABLE_DEVTOOLS === 'true',
  enableAnalytics: import.meta.env.VITE_ENABLE_ANALYTICS === 'true',
  tokenRefreshThreshold: parseInt(import.meta.env.VITE_TOKEN_REFRESH_THRESHOLD || '300000'),
  oauth: {
    googleClientId: import.meta.env.VITE_GOOGLE_CLIENT_ID || '',
    microsoftClientId: import.meta.env.VITE_MICROSOFT_CLIENT_ID || '',
    microsoftTenantId: import.meta.env.VITE_MICROSOFT_TENANT_ID || 'common',
    redirectUri: import.meta.env.VITE_OAUTH_REDIRECT_URI || 'http://localhost:3000/auth/callback',
  },
} as const;
