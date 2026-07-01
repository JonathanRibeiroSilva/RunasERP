import type { AxiosRequestConfig } from 'axios';
import { api } from './axios';
import type { Cliente, Endereco, HistoricoCredito, ClientesListResult } from '@/types/clientes';

export interface ListarClientesParams {
  skip?: number;
  limit?: number;
  nome?: string;
  ativo?: boolean;
  bloqueado?: boolean;
}

export interface CreditoPayload {
  limite_credito?: number;
  dia_vencimento?: number;
}

/** Camada de serviço de Clientes — único lugar que conhece URLs/params dos endpoints. */
export const clientesApi = {
  listar(params: ListarClientesParams, config?: AxiosRequestConfig) {
    return api.get<ClientesListResult>('/clientes', { params, ...config }).then((r) => r.data);
  },

  obter(id: string) {
    return api.get<Cliente>(`/clientes/${id}`).then((r) => r.data);
  },

  criar(data: Partial<Cliente>) {
    return api.post<Cliente>('/clientes', data).then((r) => r.data);
  },

  atualizar(id: string, data: Partial<Cliente>) {
    return api.patch<Cliente>(`/clientes/${id}`, data).then((r) => r.data);
  },

  desativar(id: string) {
    return api.delete(`/clientes/${id}`).then(() => undefined);
  },

  listarEnderecos(id: string) {
    return api.get<Endereco[]>(`/clientes/${id}/enderecos`).then((r) => r.data);
  },

  criarEndereco(id: string, data: Partial<Endereco>) {
    return api.post<Endereco>(`/clientes/${id}/enderecos`, data).then((r) => r.data);
  },

  atualizarEndereco(id: string, enderecoId: string, data: Partial<Endereco>) {
    return api.patch<Endereco>(`/clientes/${id}/enderecos/${enderecoId}`, data).then((r) => r.data);
  },

  removerEndereco(id: string, enderecoId: string) {
    return api.delete(`/clientes/${id}/enderecos/${enderecoId}`).then(() => undefined);
  },

  obterHistoricoCredito(id: string) {
    return api.get<HistoricoCredito[]>(`/clientes/${id}/historico-credito`).then((r) => r.data);
  },

  atualizarCredito(id: string, data: CreditoPayload) {
    return api.put(`/clientes/${id}/credito`, data).then((r) => r.data);
  },

  executarAcao(id: string, acao: 'bloquear' | 'desbloquear') {
    return api.post(`/clientes/${id}/${acao}`).then((r) => r.data);
  },
};
