import type { AxiosRequestConfig } from 'axios';
import { api } from './axios';
import type {
  PaginatedResult,
  LojaOnlineProdutoStatus,
  LojaOnlinePublicarPayload,
} from '@/types/produtos';

export interface ListarProdutosLojaParams {
  skip?: number;
  limit?: number;
}

/** Camada de serviço da administração da Loja Online — único lugar que conhece URLs/params dos endpoints. */
export const lojaOnlineApi = {
  listarProdutos(params: ListarProdutosLojaParams, config?: AxiosRequestConfig) {
    return api
      .get<PaginatedResult<LojaOnlineProdutoStatus>>('/loja-online/produtos', {
        params,
        ...config,
      })
      .then((r) => r.data);
  },

  publicarProduto(produtoId: string, data: LojaOnlinePublicarPayload) {
    return api.put(`/loja-online/produtos/${produtoId}/publicar`, data).then((r) => r.data);
  },
};
