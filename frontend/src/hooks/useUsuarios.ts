import { useQuery, useMutation, useQueryClient, keepPreviousData } from '@tanstack/react-query';
import { usuariosApi, type ListarUsuariosParams } from '@/services/api/usuariosApi';
import type { UsuarioCreatePayload, UsuarioUpdatePayload } from '@/types/usuario';

export const useUsuarios = (params: ListarUsuariosParams) =>
  useQuery({
    queryKey: ['usuarios', params],
    queryFn: ({ signal }) => usuariosApi.listar(params, { signal }),
    placeholderData: keepPreviousData,
  });

/** Invalida a lista inteira: total e max_usuarios do contador mudam junto com o item. */
const useUsuarioMutation = <TVars>(fn: (vars: TVars) => Promise<unknown>) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: fn,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['usuarios'] }),
  });
};

export const useCriarUsuario = () =>
  useUsuarioMutation((data: UsuarioCreatePayload) => usuariosApi.criar(data));

export const useAtualizarUsuario = () =>
  useUsuarioMutation(({ id, data }: { id: string; data: UsuarioUpdatePayload }) =>
    usuariosApi.atualizar(id, data)
  );

export const useDesativarUsuario = () => useUsuarioMutation((id: string) => usuariosApi.desativar(id));
