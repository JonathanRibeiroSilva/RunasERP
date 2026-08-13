import { useQuery, useMutation, useQueryClient, keepPreviousData } from '@tanstack/react-query';
import {
  produtosApi,
  categoriasApi,
  type ListarProdutosParams,
} from '@/services/api/produtosApi';

/**
 * Lista de produtos via React Query.
 * - cache + dedupe + refetch em background (config global em main.tsx)
 * - cancelamento automático: o `signal` é repassado ao Axios
 * - keepPreviousData: mantém a página atual visível durante a troca de filtros
 */
export const useProdutos = (params: ListarProdutosParams) =>
  useQuery({
    queryKey: ['produtos', params],
    queryFn: ({ signal }) => produtosApi.listar(params, { signal }),
    placeholderData: keepPreviousData,
  });

export const useCategorias = () =>
  useQuery({
    queryKey: ['categorias'],
    queryFn: ({ signal }) => categoriasApi.listar({ signal }),
  });

/**
 * Mapa produto_id → Produto, para resolver nomes em telas que só carregam o id
 * (ex.: Estoque, cujos registros não trazem o nome do produto).
 */
export const useProdutosLookup = () =>
  useQuery({
    queryKey: ['produtos', 'lookup'],
    // ponytail: o endpoint /produtos limita limit a 100 (le=100); pedir mais retorna 422 e
    // esvazia o lookup. 100 cobre o catálogo atual; paginar se passar de 100 SKUs.
    queryFn: ({ signal }) => produtosApi.listar({ limit: 100 }, { signal }),
    select: (data) => new Map(data.items.map((produto) => [produto.id, produto] as const)),
    staleTime: 5 * 60 * 1000,
  });

/** Produto completo por id (inclui variantes e sku) — 1 chamada cacheada, sem N+1. */
export const useProduto = (id: string | undefined) =>
  useQuery({
    queryKey: ['produtos', 'detail', id],
    queryFn: ({ signal }) => produtosApi.obter(id as string, { signal }),
    enabled: !!id,
  });

/**
 * Camada única de resolução de identidade de produto: id → nome humano.
 * Nunca expõe o id cru — durante o carregamento devolve um placeholder e, se o produto
 * não existir no cache, um rótulo neutro.
 */
export const useProdutoResolver = () => {
  const { data: mapa, isLoading } = useProdutosLookup();
  const nome = (id: string): string => {
    if (isLoading) return 'Carregando…';
    return mapa?.get(id)?.nome ?? 'Produto sem cadastro';
  };
  return { isLoading, mapa, nome };
};

export const useExcluirProduto = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => produtosApi.excluir(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['produtos'] }),
  });
};

export const useRestaurarProduto = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => produtosApi.restaurar(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['produtos'] }),
  });
};
