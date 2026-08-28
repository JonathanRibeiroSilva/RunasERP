/**
 * Testes Unitários - schemas do painel da plataforma.
 *
 * Provisionar cria empresa + admin num POST só: os dois lados precisam estar
 * válidos antes de sair, porque uma falha do admin dispara a compensação que
 * apaga a empresa recém-criada no backend.
 */

import { describe, it, expect } from 'vitest';
import { tenantSchema, planoSchema } from '../tenantSchema';

const valido = {
  razao_social: 'Loja do Bairro LTDA',
  nome_fantasia: 'Loja do Bairro',
  slug: 'loja-do-bairro',
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
  plano: 'BASICO',
  max_usuarios: '5',
  admin_nome: 'Joao Admin',
  admin_email: 'joao@lojadobairro.com',
  admin_senha: 'Senha@123',
};

describe('tenantSchema', () => {
  it('aceita um provisionamento completo', () => {
    expect(tenantSchema.safeParse(valido).success).toBe(true);
  });

  it('herda a validação de CNPJ mascarado do schema de empresa', () => {
    expect(tenantSchema.safeParse({ ...valido, cnpj: '11222333000181' }).success).toBe(false);
  });

  it('exige e-mail válido para o admin inicial', () => {
    expect(tenantSchema.safeParse({ ...valido, admin_email: 'joao' }).success).toBe(false);
  });

  it('aplica a política de senha do gateway no admin inicial', () => {
    expect(tenantSchema.safeParse({ ...valido, admin_senha: 'senha' }).success).toBe(false);
  });

  it('recusa max_usuarios não numérico', () => {
    expect(tenantSchema.safeParse({ ...valido, max_usuarios: 'cinco' }).success).toBe(false);
  });
});

describe('planoSchema', () => {
  const plano = { plano: 'PRO', max_usuarios: '10', max_produtos: '500' };

  it('aceita plano com limites', () => {
    expect(planoSchema.safeParse(plano).success).toBe(true);
  });

  it('aceita max_produtos vazio (sem limite)', () => {
    expect(planoSchema.safeParse({ ...plano, max_produtos: '' }).success).toBe(true);
  });

  it('recusa max_usuarios vazio', () => {
    expect(planoSchema.safeParse({ ...plano, max_usuarios: '' }).success).toBe(false);
  });
});
