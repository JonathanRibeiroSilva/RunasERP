// Tipos de domínio de Empresa/Loja Online (subset dos campos usados pela tela de configurações da loja).

export interface EmpresaStoreConfig {
  id: number;
  slug: string;
  catalogo_ativo: boolean;
  catalogo_titulo?: string | null;
  catalogo_descricao?: string | null;
  catalogo_whatsapp?: string | null;
  logo_url?: string | null;
  cor_primaria?: string | null;
  cor_secundaria?: string | null;
}

export interface EmpresaStoreConfigUpdate {
  slug?: string;
  catalogo_ativo?: boolean;
  catalogo_titulo?: string;
  catalogo_descricao?: string;
  catalogo_whatsapp?: string;
  logo_url?: string;
  cor_primaria?: string;
  cor_secundaria?: string;
}
