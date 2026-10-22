import type { AxiosRequestConfig } from 'axios';
import { api } from './axios';
import type {
  Estoque,
  Movimentacao,
  Lote,
  Disponibilidade,
  RelatorioEstoque,
  TipoMovimentacao,
  EntradaEstoquePayload,
  EntradaNfePayload,
  SaidaEstoquePayload,
  AjustePayload,
  ReservaPayload,
  LiberarReservaPayload,
  AtualizarEstoquePayload,
  CriarEstoquePayload,
  ConferenciaVisualPayload,
  ConferenciaVisualResumo,
} from '@/types/estoque';

export interface ListarEstoqueParams {
  skip?: number;
  limit?: number;
  apenas_baixo?: boolean;
  apenas_zerado?: boolean;
}

export interface ListarMovimentacoesParams {
  tipo?: TipoMovimentacao;
  skip?: number;
  limit?: number;
}

/**
 * Camada de serviço de Estoque — único lugar que conhece URLs/params dos endpoints.
 * Nota: os endpoints de lista retornam um array puro (sem envelope de total).
 */
export const estoqueApi = {
  listar(params: ListarEstoqueParams, config?: AxiosRequestConfig) {
    return api.get<Estoque[]>('/estoque', { params, ...config }).then((r) => r.data);
  },

  obter(id: string, config?: AxiosRequestConfig) {
    return api.get<Estoque>(`/estoque/${id}`, config).then((r) => r.data);
  },

  /** Só valida e resume o que o modelo do navegador detectou; não escreve no estoque. */
  conferenciaVisual(data: ConferenciaVisualPayload) {
    return api.post<ConferenciaVisualResumo>('/estoque/conferencia-visual', data).then((r) => r.data);
  },

  criar(data: CriarEstoquePayload) {
    return api.post<Estoque>('/estoque', data).then((r) => r.data);
  },

  atualizar(id: string, data: AtualizarEstoquePayload) {
    return api.put<Estoque>(`/estoque/${id}`, data).then((r) => r.data);
  },

  relatorioGeral(config?: AxiosRequestConfig) {
    return api.get<RelatorioEstoque>('/estoque/relatorios/geral', config).then((r) => r.data);
  },

  movimentacoes(estoqueId: string, params: ListarMovimentacoesParams, config?: AxiosRequestConfig) {
    return api
      .get<Movimentacao[]>(`/estoque/${estoqueId}/movimentacoes`, { params, ...config })
      .then((r) => r.data);
  },

  lotes(estoqueId: string, config?: AxiosRequestConfig) {
    return api.get<Lote[]>(`/estoque/${estoqueId}/lotes`, config).then((r) => r.data);
  },

  disponibilidade(produtoId: string, varianteId?: string, config?: AxiosRequestConfig) {
    return api
      .get<Disponibilidade>('/estoque/disponibilidade', {
        params: { produto_id: produtoId, variante_id: varianteId },
        ...config,
      })
      .then((r) => r.data);
  },

  entrada(data: EntradaEstoquePayload) {
    return api.post<Estoque>('/estoque/entrada', data).then((r) => r.data);
  },

  entradaNfe(data: EntradaNfePayload) {
    return api.post<Estoque[]>('/estoque/entrada-nfe', data).then((r) => r.data);
  },

  saida(data: SaidaEstoquePayload) {
    return api.post<Estoque>('/estoque/saida', data).then((r) => r.data);
  },

  ajuste(data: AjustePayload) {
    return api.post<Estoque>('/estoque/ajuste', data).then((r) => r.data);
  },

  reservar(data: ReservaPayload) {
    return api.post<Estoque>('/estoque/reservar', data).then((r) => r.data);
  },

  liberarReserva(data: LiberarReservaPayload) {
    return api.post<Estoque>('/estoque/liberar-reserva', data).then((r) => r.data);
  },
};
