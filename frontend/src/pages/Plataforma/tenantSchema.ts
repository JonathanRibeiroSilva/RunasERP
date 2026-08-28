import { z } from 'zod';
import { empresaSchema } from '@/pages/Configuracoes/empresaSchema';
import { senhaSchema } from '@/pages/Configuracoes/usuarioSchema';

/** Inteiro como texto: z.coerce faria o tipo de entrada do form divergir do de saída. */
const inteiro = (msg: string) => z.string().trim().regex(/^\d+$/, msg);

/**
 * Provisionar = EmpresaCreate + o ADMIN inicial, no mesmo POST.
 * Reusa o schema da tela de Empresa: os dois batem no mesmo cadastro no serviço empresas.
 */
export const tenantSchema = empresaSchema.extend({
  plano: z.string().trim().min(1, 'Plano é obrigatório'),
  max_usuarios: inteiro('Informe um número de usuários'),
  admin_nome: z.string().trim().min(3, 'Nome do admin deve ter no mínimo 3 caracteres'),
  admin_email: z.string().email('E-mail do admin inválido'),
  admin_senha: senhaSchema,
});

export type TenantFormData = z.infer<typeof tenantSchema>;

/** EmpresaPlanoUpdate. max_produtos vazio = sem limite (null no backend). */
export const planoSchema = z.object({
  plano: z.string().trim().min(1, 'Plano é obrigatório'),
  max_usuarios: inteiro('Informe um número de usuários'),
  max_produtos: z.union([inteiro('Informe um número de produtos'), z.literal('')]),
});

export type PlanoFormData = z.infer<typeof planoSchema>;
