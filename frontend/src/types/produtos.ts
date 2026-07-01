// Tipos de domínio de Produtos (fonte única — antes redefinidos por página).

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
