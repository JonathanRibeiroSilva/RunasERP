/**
 * Testes Unitários - retry da janela de deploy
 *
 * O interceptor reenvia leituras idempotentes quando o gateway está sendo
 * trocado (502/503/504). Escritas nunca são reenviadas: a API não tem
 * idempotency key, então um POST repetido é uma venda duplicada.
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { AxiosError, type AxiosAdapter, type AxiosResponse } from 'axios';
import { api } from '../axios';

/** Adapter de teste: responde a fila de status, repetindo o último. */
function stubAdapter(statuses: number[]): { calls: string[] } {
  const queue = [...statuses];
  const calls: string[] = [];

  api.defaults.adapter = (async (config) => {
    calls.push(`${config.method}`);
    const status = queue.length > 1 ? (queue.shift() as number) : queue[0];
    const response = {
      data: {},
      status,
      statusText: '',
      headers: {},
      config,
    } as AxiosResponse;

    // Adapters do axios são responsáveis por rejeitar status de erro.
    if (status >= 400) {
      throw new AxiosError('stub', String(status), config, null, response);
    }
    return response;
  }) as AxiosAdapter;

  return { calls };
}

describe('api - retry da janela de deploy', () => {
  const originalAdapter = api.defaults.adapter;

  beforeEach(() => {
    // sleep() real deixaria cada teste esperando 6s.
    vi.stubGlobal('setTimeout', (fn: () => void) => {
      fn();
      return 0;
    });
  });

  afterEach(() => {
    api.defaults.adapter = originalAdapter;
    vi.unstubAllGlobals();
  });

  it('deve reenviar GET em 502 e devolver a resposta quando o gateway volta', async () => {
    const { calls } = stubAdapter([502, 200]);

    const response = await api.get('/clientes');

    expect(response.status).toBe(200);
    expect(calls).toHaveLength(2);
  });

  it('deve desistir apos MAX_DEPLOY_RETRIES tentativas', async () => {
    const { calls } = stubAdapter([503]);

    await expect(api.get('/clientes')).rejects.toMatchObject({
      response: { status: 503 },
    });
    expect(calls).toHaveLength(4); // 1 original + 3 retries
  });

  it('NAO deve reenviar POST - reenviar escrita duplicaria a venda', async () => {
    const { calls } = stubAdapter([502]);

    await expect(api.post('/vendas', { total: 100 })).rejects.toMatchObject({
      response: { status: 502 },
    });
    expect(calls).toHaveLength(1);
  });

  it('NAO deve reenviar 500 - erro de aplicacao, nao janela de deploy', async () => {
    const { calls } = stubAdapter([500]);

    await expect(api.get('/clientes')).rejects.toMatchObject({
      response: { status: 500 },
    });
    expect(calls).toHaveLength(1);
  });
});
