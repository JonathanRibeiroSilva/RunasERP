/**
 * Setup Global para Testes com Vitest
 * 
 * Configura ambiente de testes, mocks globais e utilities.
 */

import { expect, afterEach, vi } from 'vitest';
import { cleanup } from '@testing-library/react';
import '@testing-library/jest-dom/vitest';

// Cleanup após cada teste
afterEach(() => {
  cleanup();
});

// Mock de localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {};

  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => {
      store[key] = value.toString();
    },
    removeItem: (key: string) => {
      delete store[key];
    },
    clear: () => {
      store = {};
    },
    get length() {
      return Object.keys(store).length;
    },
    key: (index: number) => {
      const keys = Object.keys(store);
      return keys[index] || null;
    }
  };
})();

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock
});

// Mock de window.matchMedia (para testes responsivos)
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation((query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn()
  }))
});

// Mock de console.error para evitar poluir output dos testes
const originalError = console.error;
beforeAll(() => {
  console.error = (...args: any[]) => {
    // Ignorar warnings de React Testing Library
    if (
      typeof args[0] === 'string' &&
      (args[0].includes('Warning: ReactDOM.render') ||
        args[0].includes('Not implemented: HTMLFormElement.prototype.submit'))
    ) {
      return;
    }
    originalError.call(console, ...args);
  };
});

afterAll(() => {
  console.error = originalError;
});

// Utility para criar token JWT mock
export const createMockToken = (clienteId = 'cliente-123', expiresIn = 3600) => {
  const payload = {
    sub: clienteId,
    exp: Math.floor(Date.now() / 1000) + expiresIn,
    iat: Math.floor(Date.now() / 1000)
  };
  const base64Payload = btoa(JSON.stringify(payload));
  return `mock-header.${base64Payload}.mock-signature`;
};

// Utility para criar mock de cliente
export const createMockCliente = (overrides = {}) => ({
  id: 'cliente-123',
  empresa_id: 1,
  nome: 'João Silva',
  cpf: '12345678901',
  telefone: '11987654321',
  email: 'joao@test.com',
  limite_credito: 0,
  credito_disponivel: 0,
  bloqueado: false,
  ativo: true,
  criado_em: '2024-01-01T00:00:00Z',
  ...overrides
});

// Utility para criar mock de carrinho
export const createMockCarrinho = (overrides = {}) => ({
  sessao_id: 'sessao-123',
  empresa_id: 1,
  itens: [
    {
      produto_id: 'prod-1',
      variante_id: null,
      quantidade: '2',
      codigo_produto: 'PROD001',
      descricao_produto: 'Produto Teste',
      preco_unitario: '10.00',
      subtotal: '20.00',
      estoque_disponivel: true
    }
  ],
  subtotal: '20.00',
  quantidade_itens: 2,
  criado_em: '2024-01-01T00:00:00Z',
  atualizado_em: '2024-01-01T00:00:00Z',
  ...overrides
});

// Exportar matchers customizados (se houver no futuro)
export {};
