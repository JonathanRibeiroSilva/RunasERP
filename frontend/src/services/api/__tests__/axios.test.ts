/**
 * Testes Unitários - retry da janela de deploy e Idempotency-Key
 *
 * O interceptor reenvia leituras idempotentes quando o gateway está sendo
 * trocado (502/503/504). Escritas não são reenviadas aqui, mas carregam uma
 * Idempotency-Key: o gateway reserva a chave antes de encaminhar, então o
 * duplo-clique do usuário recebe a primeira venda em vez de criar a segunda.
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { AxiosError, type AxiosAdapter, type AxiosResponse } from 'axios';
import { api } from '../axios';

/** Adapter de teste: responde a fila de status, repetindo o último. */
function stubAdapter(statuses: number[]): { calls: string[]; chaves: (string | undefined)[] } {
  const queue = [...statuses];
  const calls: string[] = [];
  const chaves: (string | undefined)[] = [];

  api.defaults.adapter = (async (config) => {
    calls.push(`${config.method}`);
    chaves.push(config.headers?.['Idempotency-Key'] as string | undefined);
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

  return { calls, chaves };
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

describe('api - Idempotency-Key', () => {
  const originalAdapter = api.defaults.adapter;

  afterEach(() => {
    api.defaults.adapter = originalAdapter;
  });

  it('deve mandar Idempotency-Key em escrita - sem ela o duplo-clique vira 2 vendas', async () => {
    const { chaves } = stubAdapter([201]);

    await api.post('/vendas', { total: 100 });

    expect(chaves[0]).toBeTruthy();
  });

  it('NAO deve mandar Idempotency-Key em leitura - GET repetido nao duplica nada', async () => {
    const { chaves } = stubAdapter([200]);

    await api.get('/clientes');

    expect(chaves[0]).toBeUndefined();
  });

  it('deve usar chave diferente por venda - senao a 2a venda legitima vira replay da 1a', async () => {
    const { chaves } = stubAdapter([201]);

    await api.post('/vendas', { total: 100 });
    await api.post('/vendas', { total: 200 });

    expect(chaves[0]).not.toBe(chaves[1]);
  });

  it('NAO deve sobrescrever chave existente - e o que mantem o reenvio sendo o mesmo pedido', async () => {
    const { chaves } = stubAdapter([201]);

    await api.post('/vendas', { total: 100 }, { headers: { 'Idempotency-Key': 'chave-fixa' } });

    expect(chaves[0]).toBe('chave-fixa');
  });
});
