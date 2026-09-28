/**
 * O resumo é dinheiro na tela: um MRR que conta assinatura não paga faz você
 * achar que faturou o que não entrou. É a única parte da página que calcula.
 */

import { describe, it, expect } from 'vitest';
import { resumirTenants } from '../PlataformaDashboard';
import type { Tenant } from '@/types/plataforma';

const tenant = (id: number, ativo: boolean, assinatura: Tenant['assinatura']): Tenant =>
  ({ id, ativo, assinatura, usuarios_ativos: 0 }) as Tenant;

const assinatura = (status: string, valor: string) =>
  ({ status, valor }) as NonNullable<Tenant['assinatura']>;

describe('resumirTenants', () => {
  it('soma no MRR só o que está ATIVA', () => {
    const { mrr } = resumirTenants([
      tenant(1, true, assinatura('ATIVA', '99.90')),
      tenant(2, true, assinatura('ATIVA', '149.90')),
      tenant(3, true, assinatura('PENDENTE', '500.00')),
      tenant(4, false, assinatura('INADIMPLENTE', '300.00')),
      tenant(5, true, null),
    ]);
    expect(mrr).toBeCloseTo(249.8, 2);
  });

  it('aceita valor com vírgula, como o form em pt-BR grava', () => {
    expect(resumirTenants([tenant(1, true, assinatura('ATIVA', '99,90'))]).mrr).toBeCloseTo(99.9, 2);
  });

  it('junta inadimplente e suspenso, que dão o mesmo trabalho', () => {
    const r = resumirTenants([
      tenant(1, false, assinatura('INADIMPLENTE', '10.00')),
      tenant(2, false, assinatura('SUSPENSA', '10.00')),
      tenant(3, true, assinatura('ATIVA', '10.00')),
    ]);
    expect(r.aCobrar).toBe(2);
  });

  it('conta lojistas, quem tem acesso e quem nunca foi cobrado', () => {
    const r = resumirTenants([
      tenant(1, true, assinatura('ATIVA', '10.00')),
      tenant(2, false, null),
      tenant(3, true, null),
    ]);
    expect(r).toMatchObject({ lojistas: 3, ativos: 2, semAssinatura: 2 });
  });

  it('lista vazia não vira NaN', () => {
    expect(resumirTenants([])).toMatchObject({ lojistas: 0, ativos: 0, mrr: 0, aCobrar: 0 });
  });
});
