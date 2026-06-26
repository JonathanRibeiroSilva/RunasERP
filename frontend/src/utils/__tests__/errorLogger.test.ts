/**
 * Testes Unitários - errorLogger
 * 
 * Testa funções de logging e tratamento de erros.
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import {
  logCheckoutError,
  isRetryableError,
  extractErrorMessage,
  sleep
} from '../errorLogger';

describe('errorLogger', () => {
  let consoleErrorSpy: any;
  
  beforeEach(() => {
    consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    vi.clearAllMocks();
  });
  
  afterEach(() => {
    consoleErrorSpy.mockRestore();
  });

  describe('logCheckoutError', () => {
    it('deve logar erro com contexto completo', () => {
      const error = new Error('Teste erro');
      const context = {
        component: 'TestComponent',
        action: 'testAction',
        metadata: { userId: '123' }
      };
      
      logCheckoutError(error, context);
      
      expect(consoleErrorSpy).toHaveBeenCalledWith(
        '[TestComponent - testAction]',
        expect.objectContaining({
          component: 'TestComponent',
          action: 'testAction',
          message: 'Teste erro',
          userId: '123'
        })
      );
    });
    
    it('deve incluir timestamp no log', () => {
      const error = new Error('Teste erro');
      const context = {
        component: 'TestComponent',
        action: 'testAction'
      };
      
      logCheckoutError(error, context);
      
      const logData = consoleErrorSpy.mock.calls[0][1];
      expect(logData.timestamp).toBeDefined();
      expect(new Date(logData.timestamp)).toBeInstanceOf(Date);
    });
    
    it('deve incluir status e detail de erro HTTP', () => {
      const error = {
        message: 'HTTP Error',
        response: {
          status: 404,
          data: {
            detail: 'Not found'
          }
        }
      };
      
      const context = {
        component: 'TestComponent',
        action: 'testAction'
      };
      
      logCheckoutError(error, context);
      
      const logData = consoleErrorSpy.mock.calls[0][1];
      expect(logData.status).toBe(404);
      expect(logData.detail).toBe('Not found');
    });
    
    it('deve lidar com erro sem response', () => {
      const error = new Error('Network error');
      const context = {
        component: 'TestComponent',
        action: 'testAction'
      };
      
      logCheckoutError(error, context);
      
      const logData = consoleErrorSpy.mock.calls[0][1];
      expect(logData.message).toBe('Network error');
      expect(logData.status).toBeUndefined();
    });
  });

  describe('isRetryableError', () => {
    it('deve retornar true para erro 500', () => {
      const error = {
        response: { status: 500 }
      };
      
      expect(isRetryableError(error)).toBe(true);
    });
    
    it('deve retornar true para erro 502', () => {
      const error = {
        response: { status: 502 }
      };
      
      expect(isRetryableError(error)).toBe(true);
    });
    
    it('deve retornar true para erro 503', () => {
      const error = {
        response: { status: 503 }
      };
      
      expect(isRetryableError(error)).toBe(true);
    });
    
    it('deve retornar true para timeout (ECONNABORTED)', () => {
      const error = {
        code: 'ECONNABORTED'
      };
      
      expect(isRetryableError(error)).toBe(true);
    });
    
    it('deve retornar true para erro de rede (sem response)', () => {
      const error = {
        message: 'Network error'
      };
      
      expect(isRetryableError(error)).toBe(true);
    });
    
    it('deve retornar true para rate limit (429)', () => {
      const error = {
        response: { status: 429 }
      };
      
      expect(isRetryableError(error)).toBe(true);
    });
    
    it('deve retornar false para erro 400', () => {
      const error = {
        response: { status: 400 }
      };
      
      expect(isRetryableError(error)).toBe(false);
    });
    
    it('deve retornar false para erro 401', () => {
      const error = {
        response: { status: 401 }
      };
      
      expect(isRetryableError(error)).toBe(false);
    });
    
    it('deve retornar false para erro 404', () => {
      const error = {
        response: { status: 404 }
      };
      
      expect(isRetryableError(error)).toBe(false);
    });
    
    it('deve retornar false para erro 409', () => {
      const error = {
        response: { status: 409 }
      };
      
      expect(isRetryableError(error)).toBe(false);
    });
  });

  describe('extractErrorMessage', () => {
    it('deve extrair mensagem de erro string simples', () => {
      const error = {
        response: {
          data: {
            detail: 'Erro simples'
          }
        }
      };
      
      expect(extractErrorMessage(error)).toBe('Erro simples');
    });
    
    it('deve extrair mensagem de array de erros', () => {
      const error = {
        response: {
          data: {
            detail: [
              { msg: 'Erro 1' },
              { message: 'Erro 2' },
              { msg: 'Erro 3' }
            ]
          }
        }
      };
      
      expect(extractErrorMessage(error)).toBe('Erro 1; Erro 2; Erro 3');
    });
    
    it('deve extrair mensagem de objeto com msg', () => {
      const error = {
        response: {
          data: {
            detail: {
              msg: 'Mensagem de erro'
            }
          }
        }
      };
      
      expect(extractErrorMessage(error)).toBe('Mensagem de erro');
    });
    
    it('deve extrair mensagem de objeto com message', () => {
      const error = {
        response: {
          data: {
            detail: {
              message: 'Mensagem de erro'
            }
          }
        }
      };
      
      expect(extractErrorMessage(error)).toBe('Mensagem de erro');
    });
    
    it('deve usar JSON.stringify para objetos complexos', () => {
      const error = {
        response: {
          data: {
            detail: {
              campo: 'valor',
              outro: 'teste'
            }
          }
        }
      };
      
      const result = extractErrorMessage(error);
      expect(result).toContain('campo');
      expect(result).toContain('valor');
    });
    
    it('deve retornar error.message quando não há response.data', () => {
      const error = {
        message: 'Network timeout'
      };
      
      expect(extractErrorMessage(error)).toBe('Network timeout');
    });
    
    it('deve retornar mensagem padrão para erro vazio', () => {
      const error = {};
      
      expect(extractErrorMessage(error)).toBe('Erro desconhecido');
    });
    
    it('deve lidar com array de objetos sem msg/message', () => {
      const error = {
        response: {
          data: {
            detail: [
              { code: 'ERR001' },
              { type: 'validation' }
            ]
          }
        }
      };
      
      const result = extractErrorMessage(error);
      expect(result).toContain('code');
      expect(result).toContain('ERR001');
    });
  });

  describe('sleep', () => {
    beforeEach(() => {
      vi.useFakeTimers();
    });
    
    afterEach(() => {
      vi.useRealTimers();
    });
    
    it('deve aguardar o tempo especificado', async () => {
      const promise = sleep(1000);
      
      vi.advanceTimersByTime(999);
      expect(promise).toBeInstanceOf(Promise);
      
      vi.advanceTimersByTime(1);
      await promise;
      
      // Se chegou aqui, o sleep completou
      expect(true).toBe(true);
    });
    
    it('deve aguardar tempos diferentes', async () => {
      const promise1 = sleep(500);
      const promise2 = sleep(1000);
      
      vi.advanceTimersByTime(500);
      await promise1;
      
      vi.advanceTimersByTime(500);
      await promise2;
      
      expect(true).toBe(true);
    });
    
    it('deve aguardar 0ms', async () => {
      const promise = sleep(0);
      
      vi.advanceTimersByTime(0);
      await promise;
      
      expect(true).toBe(true);
    });
  });
});

describe('errorLogger - Integration Tests', () => {
  let consoleErrorSpy: any;
  
  beforeEach(() => {
    consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
  });
  
  afterEach(() => {
    consoleErrorSpy.mockRestore();
  });
  
  it('deve processar erro completo de requisição HTTP', () => {
    const error = {
      message: 'Request failed',
      response: {
        status: 500,
        data: {
          detail: 'Internal server error'
        }
      },
      stack: 'Error: Request failed\n    at ...'
    };
    
    const context = {
      component: 'CheckoutPage',
      action: 'finalizarCompra',
      metadata: {
        clienteId: 'cliente-123',
        valorTotal: 50.0
      }
    };
    
    // Verificar se é retryable
    expect(isRetryableError(error)).toBe(true);
    
    // Extrair mensagem
    const mensagem = extractErrorMessage(error);
    expect(mensagem).toBe('Internal server error');
    
    // Logar
    logCheckoutError(error, context);
    
    const logData = consoleErrorSpy.mock.calls[0][1];
    expect(logData).toMatchObject({
      component: 'CheckoutPage',
      action: 'finalizarCompra',
      message: 'Request failed',
      status: 500,
      detail: 'Internal server error',
      clienteId: 'cliente-123',
      valorTotal: 50.0
    });
  });
  
  it('deve processar erro de validação (não retryable)', () => {
    const error = {
      message: 'Validation error',
      response: {
        status: 400,
        data: {
          detail: [
            { msg: 'CPF inválido', field: 'cpf' },
            { msg: 'Telefone inválido', field: 'telefone' }
          ]
        }
      }
    };
    
    const context = {
      component: 'CheckoutPage',
      action: 'atualizarCadastro'
    };
    
    // Não deve ser retryable
    expect(isRetryableError(error)).toBe(false);
    
    // Extrair mensagens
    const mensagem = extractErrorMessage(error);
    expect(mensagem).toContain('CPF inválido');
    expect(mensagem).toContain('Telefone inválido');
    
    // Logar
    logCheckoutError(error, context);
    
    expect(consoleErrorSpy).toHaveBeenCalled();
  });
});
