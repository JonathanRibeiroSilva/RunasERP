import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { empresaApi } from '@/services/api/empresaApi';
import type { EmpresaCadastroUpdate } from '@/types/empresa';

// Mesma queryKey de useEmpresa (useLojaOnline.ts): as duas telas leem o mesmo registro,
// então salvar em uma invalida a outra sem trabalho extra.
export const useEmpresaCadastro = (empresaId: number | undefined) =>
  useQuery({
    queryKey: ['empresa', empresaId],
    queryFn: ({ signal }) => empresaApi.obter(empresaId as number, { signal }),
    enabled: !!empresaId,
  });

export const useAtualizarEmpresaCadastro = (empresaId: number | undefined) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: EmpresaCadastroUpdate) => empresaApi.atualizar(empresaId as number, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['empresa', empresaId] }),
  });
};
