import type { AxiosRequestConfig } from 'axios';
import { api } from './axios';
import type {
  Integracao,
  IntegracaoUpdate,
  PagamentoStatus,
  PagamentoUpsert,
} from '@/types/integracao';

/** Camada de serviço de Integrações — único lugar que conhece URLs/params dos endpoints. */
export const integracoesApi = {
  obter(config?: AxiosRequestConfig) {
    return api.get<Integracao>('/integracoes', config).then((r) => r.data);
  },

  salvar(data: IntegracaoUpdate) {
    return api.put<Integracao>('/integracoes', data).then((r) => r.data);
  },

  remover() {
    return api.delete('/integracoes').then(() => undefined);
  },

  obterStatusPagamento(config?: AxiosRequestConfig) {
    return api.get<PagamentoStatus>('/pagamentos/admin/status', config).then((r) => r.data);
  },

  // POST cria e devolve 409 se já existe; PUT exige registro existente. Quem sabe qual
  // usar é o status, então ele decide aqui em vez de espalhar o if pela tela.
  salvarPagamento(data: PagamentoUpsert, jaConfigurado: boolean) {
    const url = '/pagamentos/admin/configuracao';
    const request = jaConfigurado ? api.put(url, data) : api.post(url, data);
    return request.then((r) => r.data);
  },
};
