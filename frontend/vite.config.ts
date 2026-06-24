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
      // HMR via nginx/ngrok:
      // - Vite faz bind em 0.0.0.0:3000 (padrão quando host não é especificado)
      // - Browser conecta em wss://ngrok:443/@vite/client
      // - Nginx faz proxy reverso para ws://frontend:3000
      // NÃO especificar host/port aqui — deixar o Vite usar defaults locais
      timeout: 60000,
      overlay: false,
    },
    middlewareMode: false,
    // Proxy condicional - apenas para desenvolvimento local (sem Nginx)
    // Quando VITE_USE_PROXY=false (Docker + Nginx), o Nginx faz o proxy de /api
    // Quando VITE_USE_PROXY=true (local sem Docker), o Vite faz o proxy de /api
    ...(process.env.VITE_USE_PROXY !== 'false' && {
      proxy: {
        '/api': {
          target: 'http://localhost:8000',
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
