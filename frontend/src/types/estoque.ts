// Tipos de domínio de Estoque (fonte única — espelha os schemas do backend).

export type TipoMovimentacao =
  | 'ENTRADA'
  | 'SAIDA'
  | 'AJUSTE'
  | 'DEVOLUCAO'
  | 'PERDA'
  | 'TRANSFERENCIA';

export type StatusLote = 'ATIVO' | 'VENCIDO' | 'BLOQUEADO';

/** Registro de estoque de um produto/variante (backend EstoqueComAlerta). */
export interface Estoque {
  id: string;
  empresa_id: number;
  produto_id: string;
  variante_id: string | null;
  quantidade: number;
  quantidade_reservada: number;
  quantidade_disponivel: number;
  estoque_minimo: number;
  estoque_maximo: number | null;
  localizacao: string | null;
  ativo: boolean;
  created_at: string;
  updated_at: string;
  alerta_estoque_baixo: boolean;
  alerta_estoque_zerado: boolean;
}

/** Lançamento no livro-razão de movimentações (backend MovimentacaoResponse). */
export interface Movimentacao {
  id: string;
  estoque_id: string;
  lote_id: string | null;
  tipo: TipoMovimentacao;
  quantidade: number;
  quantidade_anterior: number;
  quantidade_posterior: number;
  motivo: string | null;
  observacao: string | null;
  documento: string | null;
  custo_unitario: number | null;
  custo_total: number | null;
  usuario_id: string | null;
  created_at: string;
}

/** Lote de um estoque com alertas de validade (backend LoteComAlerta). */
export interface Lote {
  id: string;
  estoque_id: string;
  empresa_id: number;
  codigo: string;
  quantidade: number;
  quantidade_inicial: number;
  data_fabricacao: string | null;
  data_validade: string | null;
  fornecedor: string | null;
  nota_fiscal: string | null;
  custo_unitario: number | null;
  status: StatusLote;
  created_at: string;
  updated_at: string;
  dias_para_vencer: number | null;
  alerta_vencimento: boolean;
  vencido: boolean;
}

/** Disponibilidade real (física/reservada) de um produto (backend DisponibilidadeResponse). */
export interface Disponibilidade {
  produto_id: string;
  variante_id: string | null;
  quantidade: number;
  quantidade_reservada: number;
  quantidade_disponivel: number;
  existe: boolean;
}

/** Agregado geral do estoque para os KPIs (backend RelatorioEstoque). */
export interface RelatorioEstoque {
  total_produtos: number;
  total_em_estoque: number;
  produtos_estoque_baixo: number;
  produtos_sem_estoque: number;
  valor_total_estoque: number | null;
}

// ==================== Payloads de operações ====================

/** Criação explícita de registro de estoque (backend EstoqueCreate) — usado p/ estoque mínimo sem entrada. */
export interface CriarEstoquePayload {
  empresa_id: number;
  produto_id: string;
  variante_id?: string | null;
  quantidade?: number;
  estoque_minimo?: number;
  estoque_maximo?: number | null;
  localizacao?: string | null;
}

export interface EntradaEstoquePayload {
  empresa_id: number;
  produto_id: string;
  variante_id?: string | null;
  quantidade: number;
  motivo?: string;
  observacao?: string;
  documento?: string;
  custo_unitario?: number;
}

export interface SaidaEstoquePayload {
  empresa_id: number;
  produto_id: string;
  variante_id?: string | null;
  quantidade: number;
  motivo?: string;
  observacao?: string;
  documento?: string;
}

export interface AjustePayload {
  estoque_id: string;
  quantidade_nova: number;
  motivo: string;
  observacao?: string;
}

export interface ReservaPayload {
  empresa_id: number;
  produto_id: string;
  variante_id?: string | null;
  quantidade: number;
  documento?: string;
}

export interface LiberarReservaPayload {
  empresa_id: number;
  produto_id: string;
  variante_id?: string | null;
  quantidade: number;
  documento?: string;
}

export interface AtualizarEstoquePayload {
  estoque_minimo?: number;
  estoque_maximo?: number | null;
  localizacao?: string | null;
  ativo?: boolean;
}
