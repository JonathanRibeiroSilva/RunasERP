import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { plataformaApi } from '@/services/api/plataformaApi';
import type { TenantCreatePayload, PlanoPayload, AssinaturaPayload } from '@/types/plataforma';

export const useTenants = () =>
  useQuery({
    queryKey: ['plataforma-tenants'],
    queryFn: ({ signal }) => plataformaApi.listarTenants({ signal }),
  });

const useTenantMutation = <TVars, TData>(fn: (vars: TVars) => Promise<TData>) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: fn,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['plataforma-tenants'] }),
  });
};

export const useCriarTenant = () =>
  useTenantMutation((data: TenantCreatePayload) => plataformaApi.criarTenant(data));

export const useDefinirAcessoTenant = () =>
  useTenantMutation(({ id, acao }: { id: number; acao: 'suspender' | 'reativar' }) =>
    plataformaApi.definirAcesso(id, acao)
  );

export const useAlterarPlano = () =>
  useTenantMutation(({ id, data }: { id: number; data: PlanoPayload }) =>
    plataformaApi.alterarPlano(id, data)
  );

// ===== Fase 3 =====

/** `enabled` porque as abas só carregam quando o detalhe do tenant abre. */
export const useAuditoria = (id: number | null) =>
  useQuery({
    queryKey: ['plataforma-auditoria', id],
    queryFn: ({ signal }) => plataformaApi.auditoria(id as number, { signal }),
    enabled: id !== null,
  });

export const useDumps = (id: number | null) =>
  useQuery({
    queryKey: ['plataforma-dumps', id],
    queryFn: ({ signal }) => plataformaApi.dumps(id as number, { signal }),
    enabled: id !== null,
  });

/** Reverter é uma escrita auditada: a própria trilha ganha uma linha nova. */
export const useReverterRegistro = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (registroId: number) => plataformaApi.reverter(registroId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['plataforma-auditoria'] }),
  });
};

export const useCriarAssinatura = () =>
  useTenantMutation(({ id, data }: { id: number; data: AssinaturaPayload }) =>
    plataformaApi.criarAssinatura(id, data)
  );

export const useCancelarAssinatura = () =>
  useTenantMutation((id: number) => plataformaApi.cancelarAssinatura(id));
