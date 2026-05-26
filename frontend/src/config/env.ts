export const env = {
  // API URL - detecta automaticamente se está via ngrok
  apiUrl: (() => {
    const host = window.location.hostname;
    const protocol = window.location.protocol;
    
    // Se está via ngrok (*.ngrok-free.dev ou *.ngrok.io)
    if (host.includes('ngrok-free.dev') || host.includes('ngrok.io')) {
      // Usar a mesma URL do ngrok para a API
      return `${protocol}//${host}/api`;
    }
    
    // Caso contrário, usar a variável de ambiente ou localhost
    return import.meta.env.VITE_API_URL || 'http://localhost:8000';
  })(),
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
    redirectUri: (() => {
      // Usar a variável de ambiente se disponível (para produção)
      if (import.meta.env.VITE_OAUTH_REDIRECT_URI) {
        return import.meta.env.VITE_OAUTH_REDIRECT_URI;
      }

      const host = window.location.hostname;
      const protocol = window.location.protocol;
      
      // Se está via ngrok, usar a URL do ngrok
      if (host.includes('ngrok-free.dev') || host.includes('ngrok.io')) {
        return `${protocol}//${host}/auth/callback`;
      }
      
      // Caso contrário, usar localhost
      return `http://localhost:3000/auth/callback`;
    })(),
  },
} as const;
