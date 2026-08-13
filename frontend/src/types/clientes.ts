// Tipos de domínio de Clientes (fonte única — antes redefinidos por página).

export interface Cliente {
  id: string;
  empresa_id: number;
  nome: string;
  cpf: string | null; // Opcional para clientes OAuth/loja online
  telefone: string | null; // Opcional para clientes OAuth/loja online
  email?: string;
  data_nasc?: string;
  limite_credito: number;
  credito_disponivel: number;
  dia_vencimento?: number;
  bloqueado: boolean;
  ativo: boolean;
}

export interface Endereco {
  id: string;
  cliente_id: string;
  cep: string;
  logradouro: string;
  numero: string;
  complemento?: string;
  bairro: string;
  cidade: string;
  uf: string;
  principal: boolean;
}

export interface HistoricoCredito {
  id: string;
  data: string;
  tipo: 'AJUSTE_LIMITE' | 'BLOQUEIO' | 'DESBLOQUEIO' | 'VENDA' | 'PAGAMENTO';
  descricao: string;
  valor_anterior?: number;
  valor_novo?: number;
  usuario: string;
}

/** Envelope de paginação do endpoint de clientes (difere de produtos: usa `clientes`). */
export interface ClientesListResult {
  clientes: Cliente[];
  total: number;
}
