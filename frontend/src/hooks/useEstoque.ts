import { useMutation, useQuery, useQueryClient, keepPreviousData } from '@tanstack/react-query';
import {
  estoqueApi,
  type ListarEstoqueParams,
  type ListarMovimentacoesParams,
} from '@/services/api/estoqueApi';

/** Raiz da árvore de cache do estoque — invalidá-la atualiza lista, detalhe, relatório e movimentações. */
const ESTOQUE_KEY = ['estoque'] as const;

/**
 * Lista de estoque via React Query.
 * O backend não suporta busca/total no servidor, então a página carrega o conjunto
 * completo (limit alto) e filtra/ordena/pagina no cliente sobre todos os registros.
 */
export const useEstoques = (params: ListarEstoqueParams) =>
  useQuery({
    queryKey: ['estoque', 'list', params],
    queryFn: ({ signal }) => estoqueApi.listar(params, { signal }),
    placeholderData: keepPreviousData,
  });

export const useEstoque = (id: string | undefined) =>
  useQuery({
    queryKey: ['estoque', 'detail', id],
    queryFn: ({ signal }) => estoqueApi.obter(id as string, { signal }),
    enabled: !!id,
  });

export const useRelatorioEstoque = () =>
  useQuery({
    queryKey: ['estoque', 'relatorio'],
    queryFn: ({ signal }) => estoqueApi.relatorioGeral({ signal }),
  });

export const useMovimentacoes = (
  estoqueId: string | undefined,
  params: ListarMovimentacoesParams,
) =>
  useQuery({
    queryKey: ['estoque', 'movimentacoes', estoqueId, params],
    queryFn: ({ signal }) => estoqueApi.movimentacoes(estoqueId as string, params, { signal }),
    enabled: !!estoqueId,
    placeholderData: keepPreviousData,
  });

export const useLotes = (estoqueId: string | undefined) =>
  useQuery({
    queryKey: ['estoque', 'lotes', estoqueId],
    queryFn: ({ signal }) => estoqueApi.lotes(estoqueId as string, { signal }),
    enabled: !!estoqueId,
  });

/** Fábrica de mutações de estoque: toda operação invalida a árvore inteira do estoque. */
const useEstoqueMutation = <TPayload>(mutationFn: (payload: TPayload) => Promise<unknown>) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ESTOQUE_KEY }),
  });
};

export const useEntradaEstoque = () => useEstoqueMutation(estoqueApi.entrada);
export const useSaidaEstoque = () => useEstoqueMutation(estoqueApi.saida);
export const useAjusteEstoque = () => useEstoqueMutation(estoqueApi.ajuste);
export const useReservarEstoque = () => useEstoqueMutation(estoqueApi.reservar);
export const useLiberarReserva = () => useEstoqueMutation(estoqueApi.liberarReserva);
