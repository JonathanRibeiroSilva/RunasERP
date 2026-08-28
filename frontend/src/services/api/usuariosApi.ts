import type { AxiosRequestConfig } from 'axios';
import { api } from './axios';
import type {
  Usuario,
  UsuariosListResult,
  UsuarioCreatePayload,
  UsuarioUpdatePayload,
} from '@/types/usuario';

export interface ListarUsuariosParams {
  skip?: number;
  limit?: number;
}

/** Camada de serviço de Usuários — único lugar que conhece as URLs de /auth/admin. */
export const usuariosApi = {
  listar(params: ListarUsuariosParams, config?: AxiosRequestConfig) {
    return api
      .get<UsuariosListResult>('/auth/admin/usuarios', { ...config, params })
      .then((r) => r.data);
  },

  criar(data: UsuarioCreatePayload) {
    return api.post<Usuario>('/auth/admin/usuarios', data).then((r) => r.data);
  },

  atualizar(id: string, data: UsuarioUpdatePayload) {
    return api.put<Usuario>(`/auth/admin/usuarios/${id}`, data).then((r) => r.data);
  },

  /** Soft delete: o backend devolve 204 e o usuário perde acesso no request seguinte. */
  desativar(id: string) {
    return api.delete(`/auth/admin/usuarios/${id}`).then(() => undefined);
  },
};
