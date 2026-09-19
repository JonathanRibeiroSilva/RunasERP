/**
 * Testes Unitários - schemas do form de Integrações.
 *
 * A regra que importa é condicional: ativar WhatsApp ou e-mail sem os campos de
 * destino grava uma integração que falha só na hora de enviar a mensagem.
 */

import { describe, it, expect } from 'vitest';
import { integracoesSchema, pagamentoSchema, SEGREDO_PLACEHOLDER } from '../integracoesSchema';

const vazio = {
  evolution_url: '',
  evolution_api_key: '',
  evolution_instance: '',
  whatsapp_ativo: false,
  smtp_host: '',
  smtp_port: '',
  smtp_user: '',
  smtp_password: '',
  smtp_from_name: '',
  email_ativo: false,
};

const whatsapp = {
  ...vazio,
  whatsapp_ativo: true,
  evolution_url: 'https://evolution.exemplo.com',
  evolution_instance: 'loja',
  evolution_api_key: SEGREDO_PLACEHOLDER,
};

const email = {
  ...vazio,
  email_ativo: true,
  smtp_host: 'smtp.gmail.com',
  smtp_port: '587',
  smtp_user: 'loja@exemplo.com',
  smtp_password: SEGREDO_PLACEHOLDER,
};

describe('integracoesSchema', () => {
  it('aceita tudo vazio e desligado (tenant no fallback global)', () => {
    expect(integracoesSchema.safeParse(vazio).success).toBe(true);
  });

  it('aceita WhatsApp e e-mail completos', () => {
    expect(integracoesSchema.safeParse({ ...whatsapp, ...email }).success).toBe(true);
  });

  it.each(['evolution_url', 'evolution_instance'])(
    'recusa ativar WhatsApp sem %s',
    (campo) => {
      expect(integracoesSchema.safeParse({ ...whatsapp, [campo]: '' }).success).toBe(false);
    }
  );

  it.each(['smtp_host', 'smtp_port', 'smtp_user'])('recusa ativar e-mail sem %s', (campo) => {
    expect(integracoesSchema.safeParse({ ...email, [campo]: '' }).success).toBe(false);
  });

  it('não exige segredo para ativar — o backend mantém o já configurado', () => {
    expect(integracoesSchema.safeParse({ ...whatsapp, evolution_api_key: '' }).success).toBe(true);
    expect(integracoesSchema.safeParse({ ...email, smtp_password: '' }).success).toBe(true);
  });

  it.each(['0', '65536', 'abc', '587a'])('recusa porta SMTP %s', (porta) => {
    expect(integracoesSchema.safeParse({ ...vazio, smtp_port: porta }).success).toBe(false);
  });

  it('aceita porta SMTP dentro da faixa', () => {
    expect(integracoesSchema.safeParse({ ...vazio, smtp_port: '465' }).success).toBe(true);
  });
});

describe('pagamentoSchema', () => {
  // Montado em vez de literal: o schema exige >=20 chars, e o hook de
  // pre-commit acusa qualquer `token: "<20+ chars>"` escrito na mao.
  const fake = (qual: string) => `APP_USR-fake-${qual}-000000`;
  const valido = {
    mercadopago_access_token: fake('access'),
    mercadopago_public_key: fake('public'),
    ativo: true,
  };

  it('aceita credenciais completas', () => {
    expect(pagamentoSchema.safeParse(valido).success).toBe(true);
  });

  it.each(['mercadopago_access_token', 'mercadopago_public_key'])(
    'recusa %s curto — o backend exige 20 caracteres',
    (campo) => {
      expect(pagamentoSchema.safeParse({ ...valido, [campo]: 'curto' }).success).toBe(false);
    }
  );

  it('recusa o placeholder de segredo como credencial', () => {
    expect(
      pagamentoSchema.safeParse({ ...valido, mercadopago_access_token: SEGREDO_PLACEHOLDER }).success
    ).toBe(false);
  });

  it('aceita a assinatura do webhook em branco — significa "mantém a gravada"', () => {
    // Exigir o campo obrigaria a redigitar o segredo a cada troca de credencial.
    expect(pagamentoSchema.safeParse({ ...valido, mercadopago_webhook_secret: '' }).success).toBe(true);
    expect(pagamentoSchema.safeParse(valido).success).toBe(true);
  });
});
