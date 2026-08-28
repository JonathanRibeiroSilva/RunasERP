import type { AxiosRequestConfig } from 'axios';
import { api } from './axios';
import type {
  EmpresaCadastro,
  EmpresaCadastroUpdate,
  EmpresaStoreConfig,
  EmpresaStoreConfigUpdate,
} from '@/types/empresa';

/** A API sempre devolve o registro inteiro; os dois subsets só recortam o que cada tela usa. */
type EmpresaCompleta = EmpresaCadastro & EmpresaStoreConfig;

/** Camada de serviço de Empresa — único lugar que conhece URLs/params dos endpoints. */
export const empresaApi = {
  obter(id: number, config?: AxiosRequestConfig) {
    return api.get<EmpresaCompleta>(`/empresas/${id}`, config).then((r) => r.data);
  },

  atualizar(id: number, data: EmpresaStoreConfigUpdate | EmpresaCadastroUpdate) {
    return api.put<EmpresaCompleta>(`/empresas/${id}`, data).then((r) => r.data);
  },
};
