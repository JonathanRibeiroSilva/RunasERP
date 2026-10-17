/// <reference types="vitest" />
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    // O vitest troca todo .scss por string vazia — inclusive com `?raw`. O teste
    // do Modal lê o texto do SCSS (jsdom não enxerga o cascade do Bootstrap, que é
    // a causa do bug), então só esse arquivo é liberado, para não compilar sass em
    // todos os testes.
    css: { include: [/Modal\.scss/] },
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: [
        'node_modules/',
        'src/test/',
        '**/*.d.ts',
        '**/*.config.*',
        '**/mockData.ts',
        'dist/',
        'build/',
        'coverage/'
      ],
      thresholds: {
        statements: 70,
        branches: 65,
        functions: 70,
        lines: 70
      }
    },
    include: ['**/*.{test,spec}.{ts,tsx}'],
    exclude: ['node_modules', 'dist', 'build', '.idea', '.git', '.cache']
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src')
    }
  }
});
