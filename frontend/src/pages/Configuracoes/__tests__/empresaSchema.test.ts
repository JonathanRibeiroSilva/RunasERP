/**
 * Testes Unitários - schema do form de Dados da Empresa.
 *
 * O backend recusa CNPJ/CEP fora do formato mascarado e slug fora do kebab-case;
 * o schema é o que evita descobrir isso só no 422.
 */

import { describe, it, expect } from 'vitest';
import { empresaSchema } from '../empresaSchema';

const valido = {
  razao_social: 'Runas Comercio LTDA',
  nome_fantasia: 'Runas',
  slug: 'runas-loja',
  cnpj: '11.222.333/0001-81',
  inscricao_estadual: '',
  inscricao_municipal: '',
  regime_tributario: 'SIMPLES_NACIONAL' as const,
  cep: '87020-000',
  logradouro: 'Avenida Brasil',
  numero: '123',
  complemento: '',
  bairro: 'Centro',
  cidade: 'Maringa',
  uf: 'PR',
  telefone: '',
  celular: '',
  email: '',
  site: '',
};

describe('empresaSchema', () => {
  it('aceita um cadastro completo', () => {
    expect(empresaSchema.safeParse(valido).success).toBe(true);
  });

  it('exige CNPJ mascarado', () => {
    expect(empresaSchema.safeParse({ ...valido, cnpj: '11222333000181' }).success).toBe(false);
  });

  it('exige CEP mascarado', () => {
    expect(empresaSchema.safeParse({ ...valido, cep: '87020000' }).success).toBe(false);
  });

  it.each(['Runas Loja', 'runas--loja', '-runas', 'runas-'])('recusa slug %s', (slug) => {
    expect(empresaSchema.safeParse({ ...valido, slug }).success).toBe(false);
  });

  it('recusa UF com tamanho diferente de 2', () => {
    expect(empresaSchema.safeParse({ ...valido, uf: 'PRR' }).success).toBe(false);
  });

  it('recusa regime tributário desconhecido', () => {
    expect(empresaSchema.safeParse({ ...valido, regime_tributario: 'LUCRO_ARBITRADO' }).success).toBe(false);
  });

  it('aceita e-mail vazio mas recusa e-mail inválido', () => {
    expect(empresaSchema.safeParse({ ...valido, email: '' }).success).toBe(true);
    expect(empresaSchema.safeParse({ ...valido, email: 'nao-e-email' }).success).toBe(false);
  });

  it('exige os campos obrigatórios de identificação e endereço', () => {
    expect(empresaSchema.safeParse({ ...valido, razao_social: 'ab' }).success).toBe(false);
    expect(empresaSchema.safeParse({ ...valido, numero: '' }).success).toBe(false);
  });
});
