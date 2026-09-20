// Tipos de domínio de Produtos (fonte única — antes redefinidos por página).

/**
 * Unidades de medida aceitas — espelha o Literal `UnidadeMedida` do backend
 * (services/produtos/schemas/produtos.py). Backend rejeita valores fora da lista.
 */
export const UNIDADES_MEDIDA = [
  { codigo: 'UN', label: 'Unidade' },
  { codigo: 'KG', label: 'Quilograma' },
  { codigo: 'G', label: 'Grama' },
  { codigo: 'LT', label: 'Litro' },
  { codigo: 'ML', label: 'Mililitro' },
  { codigo: 'CX', label: 'Caixa' },
  { codigo: 'PCT', label: 'Pacote' },
  { codigo: 'FD', label: 'Fardo' },
  { codigo: 'SC', label: 'Saco' },
  { codigo: 'PAR', label: 'Par' },
  { codigo: 'M', label: 'Metro' },
  { codigo: 'CM', label: 'Centímetro' },
] as const;

export type UnidadeMedida = (typeof UNIDADES_MEDIDA)[number]['codigo'];

export interface Categoria {
  id: string;
  nome: string;
}

export interface AtributoVariante {
  chave: string;
  valor: string;
}

/** Variante de produto. O rótulo humano é o SKU + atributos (não há campo `nome`). */
export interface Variante {
  id: string;
  produto_id: string;
  sku: string;
  preco_venda?: string | number;
  ativo?: boolean;
  atributos: AtributoVariante[];
}

export interface Produto {
  id: string;
  nome: string;
  descricao?: string;
  categoria_id: string;
  categoria?: Categoria;
  ativo: boolean;
  criado_em: string;
  atualizado_em?: string;
  preco?: string | number;
  custo?: string | number;
  preco_promocional?: string | number | null;
  /** O preco que vale hoje, com a promocao ja resolvida pelo backend. */
  preco_efetivo?: string | number | null;
  promocao_fim?: string | null;
  // Campos presentes apenas no payload completo (GET /produtos/{id}); ausentes na listagem simples.
  sku?: string | null;
  codigo_barras?: string | null;
  unidade_medida?: string;
  variantes?: Variante[];
}

/** Envelope de paginação dos endpoints de produtos/categorias (skip/limit). */
export interface PaginatedResult<T> {
  items: T[];
  total: number;
  skip: number;
  limit: number;
}

/** Status de publicação de um produto na loja online (admin) — GET /produtos/loja-online/produtos. */
export interface LojaOnlineProdutoStatus {
  id: string;
  nome: string;
  preco: string | number;
  categoria_id: string;
  ativo: boolean;
  visivel: boolean;
  destaque: boolean;
  ordem_exibicao: number;
}

export interface LojaOnlinePublicarPayload {
  visivel: boolean;
  destaque?: boolean;
}
