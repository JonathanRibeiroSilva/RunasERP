import { z } from 'zod';

/**
 * O que o form mostra no lugar de um segredo já gravado. O backend trata
 * segredo vazio/ausente como "manter o atual", então este valor nunca pode
 * ser enviado de volta — devolvê-lo gravaria os bullets como credencial.
 */
export const SEGREDO_PLACEHOLDER = '••••••';

const opcional = z.string().trim().optional().or(z.literal(''));

const exigirPreenchido = (
  ctx: z.RefinementCtx,
  valor: string | undefined,
  path: string,
  message: string
) => {
  if (!valor?.trim()) ctx.addIssue({ code: z.ZodIssueCode.custom, path: [path], message });
};

/** WhatsApp/Evolution + SMTP (PUT /integracoes). Ativar uma integração exige seus campos. */
export const integracoesSchema = z
  .object({
    evolution_url: opcional,
    evolution_api_key: opcional,
    evolution_instance: opcional,
    whatsapp_ativo: z.boolean(),
    smtp_host: opcional,
    smtp_port: z
      .string()
      .trim()
      .regex(/^\d{1,5}$/, 'Porta deve ser um número')
      .refine((v) => Number(v) >= 1 && Number(v) <= 65535, 'Porta deve estar entre 1 e 65535')
      .optional()
      .or(z.literal('')),
    smtp_user: opcional,
    smtp_password: opcional,
    smtp_from_name: opcional,
    email_ativo: z.boolean(),
  })
  .superRefine((data, ctx) => {
    if (data.whatsapp_ativo) {
      exigirPreenchido(ctx, data.evolution_url, 'evolution_url', 'URL é obrigatória para ativar o WhatsApp');
      exigirPreenchido(ctx, data.evolution_instance, 'evolution_instance', 'Instância é obrigatória para ativar o WhatsApp');
    }
    if (data.email_ativo) {
      exigirPreenchido(ctx, data.smtp_host, 'smtp_host', 'Host é obrigatório para ativar o e-mail');
      exigirPreenchido(ctx, data.smtp_port, 'smtp_port', 'Porta é obrigatória para ativar o e-mail');
      exigirPreenchido(ctx, data.smtp_user, 'smtp_user', 'Usuário é obrigatório para ativar o e-mail');
    }
  });

export type IntegracoesFormData = z.infer<typeof integracoesSchema>;

/**
 * Mercado Pago. Espelha ConfiguracaoPagamentoCreate/Update: o backend exige as
 * duas credenciais inteiras em toda escrita — não existe "manter o atual" aqui,
 * trocar uma é reenviar as duas. A assinatura do webhook é a exceção: é
 * opcional e, em branco, o backend mantém a que já está gravada.
 */
export const pagamentoSchema = z.object({
  mercadopago_access_token: z.string().trim().min(20, 'Access Token deve ter no mínimo 20 caracteres'),
  mercadopago_public_key: z.string().trim().min(20, 'Public Key deve ter no mínimo 20 caracteres'),
  mercadopago_webhook_secret: opcional,
  ativo: z.boolean(),
});

export type PagamentoFormData = z.infer<typeof pagamentoSchema>;
