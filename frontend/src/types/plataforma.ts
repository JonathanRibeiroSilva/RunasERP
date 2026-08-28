// Tipos do painel da plataforma (/plataforma/tenants) — só metadados de tenant, nunca dado de negócio.

import type { EmpresaCadastroUpdate } from './empresa';

/** Espelha EmpresaListItem + usuarios_ativos, que o gateway conta no banco dele. */
export interface Tenant {
  id: number;
  slug: string;
  razao_social: string;
  nome_fantasia: string;
  cnpj: string;
  status: string;
  cidade: string;
  uf: string;
  catalogo_ativo: boolean;
  plano: string;
  ativo: boolean;
  criado_em: string;
  max_usuarios: number;
  max_produtos: number;
  usuarios_ativos: number;
  /** null = tenant ainda não cobrado; a régua só age sobre quem tem assinatura. */
  assinatura: AssinaturaResumo | null;
}

/** Estado da cobrança, lido de gateway.assinaturas pelo próprio gateway. */
export interface AssinaturaResumo {
  empresa_id: number;
  plano: string;
  valor: string;
  status: string;
  vence_em: string | null;
  /** true = escrita bloqueada com 402; leitura continua liberada. */
  somente_leitura: boolean;
}

export interface TenantsListResult {
  items: Tenant[];
  total: number;
}

export interface TenantCreatePayload {
  empresa: EmpresaCadastroUpdate & { plano?: string; max_usuarios?: number };
  admin: { nome: string; email: string; senha: string };
}

/** EmpresaPlanoUpdate: os campos que EmpresaUpdate deixou de aceitar do lojista. */
export interface PlanoPayload {
  plano?: string;
  max_usuarios?: number;
  max_produtos?: number | null;
}

// ===== Fase 3: auditoria, backups e assinatura =====

/** Trilha do middleware: o "quem e quando". Nunca reversível — não tem snapshot. */
export interface AuditoriaRequisicao {
  id: number;
  usuario_id: string | null;
  metodo: string;
  rota: string;
  status_resposta: number;
  criado_em: string;
}

/** Snapshot da trigger: o "o quê". `reversivel` vem do backend, a tela não adivinha. */
export interface AuditoriaRegistro {
  id: number;
  schema_origem: string;
  tabela: string;
  registro_id: string;
  operacao: string;
  /** Estado antes e depois: reverter sobrescreve, e confirmar sem ver é assinar em branco. */
  dados_antes: Record<string, unknown> | null;
  dados_depois: Record<string, unknown> | null;
  revertido_em: string | null;
  criado_em: string;
  reversivel: boolean;
}

export interface AuditoriaResult {
  requisicoes: AuditoriaRequisicao[];
  registros: AuditoriaRegistro[];
}

/** Sempre vazio até a Fase 4. `detalhe` traz o script de restauração manual. */
export interface DumpsResult {
  items: unknown[];
  restauracao: string;
  detalhe: string;
}

export interface AssinaturaPayload {
  plano: string;
  valor: number;
  email_pagador: string;
}

/** `init_point` é o link de adesão que o lojista abre para assinar. */
export interface AssinaturaLink {
  preapproval_id: string;
  init_point: string;
}
