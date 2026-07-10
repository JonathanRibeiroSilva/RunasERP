import { useQuery, useMutation, useQueryClient, keepPreviousData } from '@tanstack/react-query';
import { empresaApi } from '@/services/api/empresaApi';
import { lojaOnlineApi, type ListarProdutosLojaParams } from '@/services/api/lojaOnlineApi';
import type { EmpresaStoreConfigUpdate } from '@/types/empresa';
import type { LojaOnlinePublicarPayload } from '@/types/produtos';

export const useEmpresa = (empresaId: number | undefined) =>
  useQuery({
    queryKey: ['empresa', empresaId],
    queryFn: ({ signal }) => empresaApi.obter(empresaId as number, { signal }),
    enabled: !!empresaId,
  });

export const useAtualizarEmpresa = (empresaId: number | undefined) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: EmpresaStoreConfigUpdate) => empresaApi.atualizar(empresaId as number, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['empresa', empresaId] }),
  });
};

export const useProdutosLoja = (params: ListarProdutosLojaParams) =>
  useQuery({
    queryKey: ['loja-online-produtos', params],
    queryFn: ({ signal }) => lojaOnlineApi.listarProdutos(params, { signal }),
    placeholderData: keepPreviousData,
  });

export const usePublicarProduto = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ produtoId, data }: { produtoId: string; data: LojaOnlinePublicarPayload }) =>
      lojaOnlineApi.publicarProduto(produtoId, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['loja-online-produtos'] }),
  });
};
