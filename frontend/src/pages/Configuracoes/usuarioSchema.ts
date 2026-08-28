import { z } from 'zod';

/**
 * Mesmas regras de UsuarioCreate.validate_senha no gateway.
 * Duplicar aqui é o que evita descobrir a política de senha só no 422.
 */
export const senhaSchema = z
  .string()
  .min(8, 'Senha deve ter no mínimo 8 caracteres')
  .max(20, 'Senha deve ter no máximo 20 caracteres')
  .regex(/[A-Z]/, 'Senha deve conter ao menos uma letra maiúscula')
  .regex(/[a-z]/, 'Senha deve conter ao menos uma letra minúscula')
  .regex(/\d/, 'Senha deve conter ao menos um número')
  .regex(/[!@#$%^&*()_+\-=[\]{}|;:,.<>?]/, 'Senha deve conter ao menos um caractere especial');

/**
 * `criando` alterna só a senha: o PUT não aceita senha (UsuarioUpdate não tem o campo),
 * então na edição o valor viaja vazio e é descartado antes do envio.
 */
export const usuarioSchema = (criando: boolean) =>
  z.object({
    nome: z.string().trim().min(3, 'Nome deve ter no mínimo 3 caracteres'),
    email: z.string().email('E-mail inválido'),
    senha: criando ? senhaSchema : z.union([senhaSchema, z.literal('')]),
    role: z.enum(['ADMIN', 'OPERADOR']),
    ativo: z.boolean(),
  });

export type UsuarioFormData = z.infer<ReturnType<typeof usuarioSchema>>;
