/**
 * Testes Unitários - schema do form de assinatura da plataforma.
 *
 * O preapproval nasce na conta MP do dono da plataforma: valor zerado ou
 * e-mail errado vira uma assinatura que só se desfaz cancelando no MP.
 */

import { describe, it, expect } from 'vitest';
import { assinaturaSchema, valorParaNumero } from '../assinaturaSchema';

const valido = { plano: 'BASICO', valor: '99,90', email_pagador: 'dono@lojadobairro.com' };

describe('assinaturaSchema', () => {
  it('aceita uma assinatura completa', () => {
    expect(assinaturaSchema.safeParse(valido).success).toBe(true);
  });

  it('aceita valor com ponto decimal', () => {
    expect(assinaturaSchema.safeParse({ ...valido, valor: '99.90' }).success).toBe(true);
  });

  it('recusa valor zerado', () => {
    expect(assinaturaSchema.safeParse({ ...valido, valor: '0' }).success).toBe(false);
  });

  it('recusa valor não numérico', () => {
    expect(assinaturaSchema.safeParse({ ...valido, valor: 'cem reais' }).success).toBe(false);
  });

  it('recusa mais de duas casas decimais', () => {
    expect(assinaturaSchema.safeParse({ ...valido, valor: '99,905' }).success).toBe(false);
  });

  it('exige plano', () => {
    expect(assinaturaSchema.safeParse({ ...valido, plano: '  ' }).success).toBe(false);
  });

  it('exige e-mail válido do pagador', () => {
    expect(assinaturaSchema.safeParse({ ...valido, email_pagador: 'dono' }).success).toBe(false);
  });
});

describe('valorParaNumero', () => {
  it('converte o decimal em pt-BR para o número que vai ao Mercado Pago', () => {
    expect(valorParaNumero('99,90')).toBe(99.9);
  });
});
