import { z } from 'zod';

/**
 * POST /plataforma/tenants/{id}/assinatura — {plano, valor, email_pagador}.
 *
 * `valor` fica string no form e vira número só no submit: o MP recusa
 * transaction_amount zerado, e um preapproval criado errado só se conserta
 * cancelando na conta do dono da plataforma.
 */
export const assinaturaSchema = z.object({
  plano: z.string().trim().min(1, 'Plano é obrigatório'),
  valor: z
    .string()
    .trim()
    .regex(/^\d+([.,]\d{1,2})?$/, 'Informe um valor como 99,90')
    .refine((v) => Number(v.replace(',', '.')) > 0, 'O valor deve ser maior que zero'),
  email_pagador: z.string().trim().email('E-mail do pagador inválido'),
});

export type AssinaturaFormData = z.infer<typeof assinaturaSchema>;

/** Aceita vírgula porque o campo é digitado em pt-BR. */
export const valorParaNumero = (valor: string) => Number(valor.replace(',', '.'));
