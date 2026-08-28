import { z } from 'zod';

const opcional = z.string().trim().optional().or(z.literal(''));

/** Espelha EmpresaUpdate do backend: CNPJ e CEP viajam mascarados, sem campos de plano. */
export const empresaSchema = z.object({
  razao_social: z.string().trim().min(3, 'Razão social deve ter no mínimo 3 caracteres'),
  nome_fantasia: z.string().trim().min(3, 'Nome fantasia deve ter no mínimo 3 caracteres'),
  slug: z
    .string()
    .trim()
    .min(3, 'Slug deve ter no mínimo 3 caracteres')
    .regex(/^[a-z0-9]+(-[a-z0-9]+)*$/, 'Use apenas letras minúsculas, números e hífen'),
  cnpj: z.string().regex(/^\d{2}\.\d{3}\.\d{3}\/\d{4}-\d{2}$/, 'CNPJ deve estar no formato 00.000.000/0000-00'),
  inscricao_estadual: opcional,
  inscricao_municipal: opcional,
  regime_tributario: z.enum(['SIMPLES_NACIONAL', 'LUCRO_PRESUMIDO', 'LUCRO_REAL', 'MEI']),
  cep: z.string().regex(/^\d{5}-\d{3}$/, 'CEP deve estar no formato 00000-000'),
  logradouro: z.string().trim().min(3, 'Logradouro deve ter no mínimo 3 caracteres'),
  numero: z.string().trim().min(1, 'Número é obrigatório'),
  complemento: opcional,
  bairro: z.string().trim().min(3, 'Bairro deve ter no mínimo 3 caracteres'),
  cidade: z.string().trim().min(3, 'Cidade deve ter no mínimo 3 caracteres'),
  uf: z.string().trim().length(2, 'UF deve ter 2 caracteres'),
  telefone: opcional,
  celular: opcional,
  email: z.string().email('E-mail inválido').optional().or(z.literal('')),
  site: opcional,
});

export type EmpresaFormData = z.infer<typeof empresaSchema>;
