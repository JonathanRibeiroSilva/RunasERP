// Tipos de gestão de usuários do tenant (GET/POST/PUT/DELETE /auth/admin/usuarios).

import type { UserRole } from './auth';

/** Papéis que um ADMIN de tenant pode atribuir — SUPER_ADMIN é da plataforma e o backend rejeita com 403. */
export type RoleTenant = 'ADMIN' | 'OPERADOR';

export interface Usuario {
  id: string;
  nome: string;
  email: string;
  role: UserRole;
  ativo: boolean;
  empresa_id: number | null;
  empresa_slug?: string | null;
  criado_em: string;
}

export interface UsuariosListResult {
  items: Usuario[];
  total: number;
  /** Ativos do tenant — é este número que o limite do plano conta. */
  ativos: number;
  skip: number;
  limit: number;
  /** Limite do plano. null = limite desconhecido (o serviço empresas não respondeu). */
  max_usuarios: number | null;
}

export interface UsuarioCreatePayload {
  nome: string;
  email: string;
  senha: string;
  role: RoleTenant;
  /** O router sobrescreve com o tenant do admin, mas UsuarioCreate exige o campo. */
  empresa_id: number;
}

export interface UsuarioUpdatePayload {
  nome?: string;
  email?: string;
  role?: RoleTenant;
  ativo?: boolean;
}
