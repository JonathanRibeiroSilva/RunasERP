/**
 * O default do menu é invertido de propósito: item sem requiredRole é item de
 * tenant, e o SUPER_ADMIN não tem tenant. É a regra que regride em silêncio
 * quando alguém acrescenta um item novo sem pensar no painel de plataforma.
 */

import { describe, it, expect } from 'vitest';
import { podeVer } from '../Sidebar';

describe('podeVer', () => {
  it('esconde item sem requiredRole do SUPER_ADMIN', () => {
    expect(podeVer('SUPER_ADMIN')).toBe(false);
    expect(podeVer('SUPER_ADMIN', [])).toBe(false);
  });

  it('mostra item sem requiredRole para quem tem tenant', () => {
    expect(podeVer('ADMIN')).toBe(true);
    expect(podeVer('OPERADOR')).toBe(true);
  });

  it('respeita a lista quando ela existe', () => {
    expect(podeVer('SUPER_ADMIN', ['SUPER_ADMIN'])).toBe(true);
    expect(podeVer('ADMIN', ['SUPER_ADMIN'])).toBe(false);
    expect(podeVer('OPERADOR', ['ADMIN'])).toBe(false);
  });

  it('sem usuário, nada aparece', () => {
    expect(podeVer(undefined)).toBe(false);
    expect(podeVer(undefined, ['ADMIN'])).toBe(false);
  });
});
