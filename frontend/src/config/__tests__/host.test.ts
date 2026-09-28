/**
 * A regra de porta tem duas pontas que se olham: se o super admin for mandado
 * para /plataforma num host que não serve /plataforma, e de lá de volta para
 * /dashboard, o navegador fica em laço de redirect e mostra tela branca. Estes
 * casos existem para que 'porta-errada' continue cortando o laço.
 */

import { describe, it, expect } from 'vitest';
import { escolherPorta } from '../host';

const NO_PAINEL = true;
const NO_APP = false;

describe('escolherPorta', () => {
  it('super admin no painel circula pelo painel', () => {
    expect(escolherPorta('SUPER_ADMIN', NO_PAINEL, '/plataforma')).toBe('ok');
    expect(escolherPorta('SUPER_ADMIN', NO_PAINEL, '/plataforma/tenants')).toBe('ok');
    expect(escolherPorta('SUPER_ADMIN', NO_PAINEL, '/perfil')).toBe('ok');
  });

  it('super admin no painel não alcança tela de tenant', () => {
    expect(escolherPorta('SUPER_ADMIN', NO_PAINEL, '/vendas')).toBe('para-plataforma');
    expect(escolherPorta('SUPER_ADMIN', NO_PAINEL, '/dashboard')).toBe('para-plataforma');
  });

  it('cada conta no host do outro para numa tela, não num laço', () => {
    expect(escolherPorta('SUPER_ADMIN', NO_APP, '/dashboard')).toBe('porta-errada');
    expect(escolherPorta('SUPER_ADMIN', NO_APP, '/plataforma')).toBe('porta-errada');
    expect(escolherPorta('ADMIN', NO_PAINEL, '/plataforma')).toBe('porta-errada');
    expect(escolherPorta('OPERADOR', NO_PAINEL, '/dashboard')).toBe('porta-errada');
  });

  it('lojista no host dele usa o ERP e não vê a plataforma', () => {
    expect(escolherPorta('ADMIN', NO_APP, '/vendas')).toBe('ok');
    expect(escolherPorta('OPERADOR', NO_APP, '/perfil')).toBe('ok');
    expect(escolherPorta('ADMIN', NO_APP, '/plataforma')).toBe('para-dashboard');
  });

  it('sem separar (dev num host só), os dois convivem e ninguém bate em porta errada', () => {
    expect(escolherPorta('SUPER_ADMIN', NO_APP, '/plataforma', false)).toBe('ok');
    expect(escolherPorta('SUPER_ADMIN', NO_APP, '/vendas', false)).toBe('para-plataforma');
    expect(escolherPorta('ADMIN', NO_APP, '/vendas', false)).toBe('ok');
    expect(escolherPorta('ADMIN', NO_APP, '/plataforma', false)).toBe('para-dashboard');
  });

  it('sem usuário carregado, nada de porta errada no host do app', () => {
    expect(escolherPorta(undefined, NO_APP, '/dashboard')).toBe('ok');
  });
});
