import { useQuery, useMutation, useQueryClient, keepPreviousData } from '@tanstack/react-query';
import { clientesApi, type ListarClientesParams } from '@/services/api/clientesApi';

/** Lista de clientes via React Query (cache, dedupe, cancelamento via signal). */
export const useClientes = (params: ListarClientesParams) =>
  useQuery({
    queryKey: ['clientes', params],
    queryFn: ({ signal }) => clientesApi.listar(params, { signal }),
    placeholderData: keepPreviousData,
  });

export const useDesativarCliente = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => clientesApi.desativar(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['clientes'] }),
  });
};
