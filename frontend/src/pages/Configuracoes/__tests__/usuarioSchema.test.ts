/**
 * Testes Unitários - schema do form de Usuários.
 *
 * A política de senha do gateway é a parte que só falharia no 422; e a senha
 * precisa ser obrigatória na criação e opcional na edição (o PUT não a aceita).
 */

import { describe, it, expect } from 'vitest';
import { usuarioSchema } from '../usuarioSchema';

const valido = {
  nome: 'Maria Souza',
  email: 'maria@loja.com',
  senha: 'Senha@123',
  role: 'OPERADOR' as const,
  ativo: true,
};

describe('usuarioSchema', () => {
  it('aceita um usuário completo na criação', () => {
    expect(usuarioSchema(true).safeParse(valido).success).toBe(true);
  });

  it('exige nome com no mínimo 3 caracteres', () => {
    expect(usuarioSchema(true).safeParse({ ...valido, nome: 'Jo' }).success).toBe(false);
  });

  it('recusa e-mail inválido', () => {
    expect(usuarioSchema(true).safeParse({ ...valido, email: 'maria' }).success).toBe(false);
  });

  it.each([
    ['curta demais', 'Ab@1'],
    ['sem maiúscula', 'senha@123'],
    ['sem minúscula', 'SENHA@123'],
    ['sem número', 'Senha@abc'],
    ['sem caractere especial', 'Senha1234'],
  ])('recusa senha %s', (_caso, senha) => {
    expect(usuarioSchema(true).safeParse({ ...valido, senha }).success).toBe(false);
  });

  it('exige senha na criação', () => {
    expect(usuarioSchema(true).safeParse({ ...valido, senha: '' }).success).toBe(false);
  });

  it('aceita senha vazia na edição', () => {
    expect(usuarioSchema(false).safeParse({ ...valido, senha: '' }).success).toBe(true);
  });

  it('ainda valida a força quando a senha é digitada na edição', () => {
    expect(usuarioSchema(false).safeParse({ ...valido, senha: 'fraca' }).success).toBe(false);
  });

  it('não aceita SUPER_ADMIN como papel de tenant', () => {
    expect(usuarioSchema(true).safeParse({ ...valido, role: 'SUPER_ADMIN' }).success).toBe(false);
  });
});
