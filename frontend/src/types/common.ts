// Tipos comuns usados em toda a aplicação

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface ListParams {
  page?: number;
  size?: number;
  search?: string;
  sort_by?: string;
  order?: 'asc' | 'desc';
  [key: string]: string | number | boolean | undefined;
}

export interface ApiError {
  detail: string;
  status_code?: number;
}

export interface SelectOption {
  value: string | number;
  label: string;
}

export type Status = 'idle' | 'loading' | 'success' | 'error';

/** Valor monetário serializado como string (Decimal) pelo backend. Use parseFloat ao calcular. */
export type Money = string;

export interface BaseEntity {
  id: string;
  created_at: string;
  updated_at: string;
}
