import type { AxiosRequestConfig } from 'axios';
import { api } from './axios';
import type { Categoria, Produto, PaginatedResult } from '@/types/produtos';

export interface ListarProdutosParams {
  skip?: number;
  limit?: number;
  apenas_deletados?: boolean;
  busca?: string;
  categoria_id?: string;
}

/** Camada de serviço de Produtos — único lugar que conhece URLs/params dos endpoints. */
export const produtosApi = {
  listar(params: ListarProdutosParams, config?: AxiosRequestConfig) {
    return api
      .get<PaginatedResult<Produto>>('/produtos', { params, ...config })
      .then((response) => response.data);
  },

  /** Produto completo (inclui sku, codigo_barras e variantes) — usado para resolver identidade. */
  obter(id: string, config?: AxiosRequestConfig) {
    return api.get<Produto>(`/produtos/${id}`, config).then((response) => response.data);
  },

  excluir(id: string) {
    return api.delete(`/produtos/${id}`).then((response) => response.data);
  },

  restaurar(id: string) {
    return api.patch(`/produtos/${id}/restaurar`).then((response) => response.data);
  },
};

export const categoriasApi = {
  listar(config?: AxiosRequestConfig) {
    return api
      .get<PaginatedResult<Categoria>>('/categorias', { params: { limit: 100 }, ...config })
      .then((response) => response.data);
  },
};
