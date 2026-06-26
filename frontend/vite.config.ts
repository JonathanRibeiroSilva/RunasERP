import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  css: {
    preprocessorOptions: {
      scss: {
        // Silenciar deprecation warnings do Sass (darken, @import legado)
        // que causam recompilação em loop no Vite
        silenceDeprecations: ['color-functions', 'import', 'global-builtin', 'legacy-js-api'],
      },
    },
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@/components': path.resolve(__dirname, './src/components'),
      '@/pages': path.resolve(__dirname, './src/pages'),
      '@/services': path.resolve(__dirname, './src/services'),
      '@/hooks': path.resolve(__dirname, './src/hooks'),
      '@/contexts': path.resolve(__dirname, './src/contexts'),
      '@/types': path.resolve(__dirname, './src/types'),
      '@/utils': path.resolve(__dirname, './src/utils'),
      '@/config': path.resolve(__dirname, './src/config'),
      '@/styles': path.resolve(__dirname, './src/styles'),
    },
  },
  server: {
    port: 3000,
    host: '0.0.0.0',
    strictPort: false,
    allowedHosts: [
      'localhost',
      '127.0.0.1',
      '.ngrok-free.dev',
      '.ngrok.io',
      'runaserp.com.br',
      '.runaserp.com.br',
      'www.runaserp.com.br',
    ],
    watch: {
      usePolling: true,
      interval: 1000, // Aumentado de 50ms para 1s — reduz falsos positivos no Windows/Docker
      binaryInterval: 300,
      ignored: [
        '**/node_modules/**',
        '**/.git/**',
        '**/dist/**',
        '**/.vscode/**',
        '**/.idea/**',
        '**/coverage/**',
        '**/*.log',
        // Ignorar arquivos temporários do Windows que causam reload falso
        '**/*~',
        '**/*.swp',
        '**/*.swo',
        '**/.DS_Store',
        '**/Thumbs.db',
      ],
    },
    hmr: {
      // HMR configuração otimizada para Docker
      // - Vite faz bind em 0.0.0.0:3000
      // - Cloudflare Tunnel faz proxy reverso quando necessário
      timeout: 60000,
      overlay: false,
    },
    middlewareMode: false,
    // Proxy condicional - funciona tanto em Docker quanto local
    // Quando VITE_USE_PROXY=false, não cria proxy (útil quando há proxy externo como nginx/cloudflare)
    // Quando VITE_USE_PROXY=true (padrão Docker), o Vite faz proxy de /api para api-gateway:8000
    ...(process.env.VITE_USE_PROXY !== 'false' && {
      proxy: {
        '/api': {
          target: process.env.VITE_API_GATEWAY_TARGET || 'http://api-gateway:8000',
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api/, ''),
        },
      },
    }),
  },
  preview: {
    host: '0.0.0.0',
    port: 3000,
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
  },
});
