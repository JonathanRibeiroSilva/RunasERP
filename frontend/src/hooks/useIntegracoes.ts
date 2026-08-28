import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { integracoesApi } from '@/services/api/integracoesApi';
import type { IntegracaoUpdate, PagamentoUpsert } from '@/types/integracao';

export const useIntegracoes = () =>
  useQuery({
    queryKey: ['integracoes'],
    queryFn: ({ signal }) => integracoesApi.obter({ signal }),
  });

export const useSalvarIntegracoes = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: IntegracaoUpdate) => integracoesApi.salvar(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['integracoes'] }),
  });
};

export const useRemoverIntegracoes = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => integracoesApi.remover(),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['integracoes'] }),
  });
};

export const useStatusPagamento = () =>
  useQuery({
    queryKey: ['pagamento-status'],
    queryFn: ({ signal }) => integracoesApi.obterStatusPagamento({ signal }),
  });

export const useSalvarPagamento = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ data, jaConfigurado }: { data: PagamentoUpsert; jaConfigurado: boolean }) =>
      integracoesApi.salvarPagamento(data, jaConfigurado),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['pagamento-status'] }),
  });
};
