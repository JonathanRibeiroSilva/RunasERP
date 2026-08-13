import type { AxiosRequestConfig } from 'axios';
import { api } from './axios';
import type { EmpresaStoreConfig, EmpresaStoreConfigUpdate } from '@/types/empresa';

/** Camada de serviço de Empresa — único lugar que conhece URLs/params dos endpoints. */
export const empresaApi = {
  obter(id: number, config?: AxiosRequestConfig) {
    return api.get<EmpresaStoreConfig>(`/empresas/${id}`, config).then((r) => r.data);
  },

  atualizar(id: number, data: EmpresaStoreConfigUpdate) {
    return api.put<EmpresaStoreConfig>(`/empresas/${id}`, data).then((r) => r.data);
  },
};
