// Tipos de Integrações do tenant (WhatsApp/Evolution, SMTP e Mercado Pago).

/** GET /integracoes — nunca traz segredo, só os booleanos *_configurado. */
export interface Integracao {
  id?: string | null;
  empresa_id: number;
  evolution_url?: string | null;
  evolution_instance?: string | null;
  evolution_api_key_configurado: boolean;
  whatsapp_ativo: boolean;
  smtp_host?: string | null;
  smtp_port?: number | null;
  smtp_user?: string | null;
  smtp_from_name?: string | null;
  smtp_password_configurado: boolean;
  email_ativo: boolean;
  updated_at?: string | null;
}

/**
 * PUT /integracoes. Segredo ausente = "manter o atual": o backend só grava
 * quando vem valor, então o placeholder •••••• nunca pode voltar no payload.
 */
export interface IntegracaoUpdate {
  evolution_url?: string;
  evolution_api_key?: string;
  evolution_instance?: string;
  whatsapp_ativo?: boolean;
  smtp_host?: string;
  smtp_port?: number;
  smtp_user?: string;
  smtp_password?: string;
  smtp_from_name?: string;
  email_ativo?: boolean;
}

/** GET /pagamentos/admin/status — Mercado Pago, sem credencial. */
export interface PagamentoStatus {
  configurado: boolean;
  ativo: boolean;
  /** False = a rota de webhook aceita notificação não assinada. */
  webhook_assinatura_configurada: boolean;
  ultima_atualizacao?: string | null;
}

export interface PagamentoUpsert {
  mercadopago_access_token: string;
  mercadopago_public_key: string;
  /** Ausente = "mantém o gravado"; o backend recusa string vazia. */
  mercadopago_webhook_secret?: string;
  ativo: boolean;
}
