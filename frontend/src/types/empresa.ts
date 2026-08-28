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

export type RegimeTributario = 'SIMPLES_NACIONAL' | 'LUCRO_PRESUMIDO' | 'LUCRO_REAL' | 'MEI';

/** Registro cadastral/fiscal completo (GET /empresas/{id}). Catálogo fica em EmpresaStoreConfig. */
export interface EmpresaCadastro {
  id: number;
  slug: string;
  razao_social: string;
  nome_fantasia: string;
  cnpj: string;
  inscricao_estadual?: string | null;
  inscricao_municipal?: string | null;
  regime_tributario: RegimeTributario;
  cep: string;
  logradouro: string;
  numero: string;
  complemento?: string | null;
  bairro: string;
  cidade: string;
  uf: string;
  telefone?: string | null;
  celular?: string | null;
  email?: string | null;
  site?: string | null;
  // Plano e limites: exibição pura — EmpresaUpdate do backend rejeita esses campos.
  plano: string;
  status: string;
  ativo: boolean;
  max_usuarios: number;
  max_produtos?: number | null;
}

/** Só o que PUT /empresas/{id} aceita do lojista — sem plano, limites, status, tipo. */
export type EmpresaCadastroUpdate = Partial<
  Omit<EmpresaCadastro, 'id' | 'plano' | 'status' | 'ativo' | 'max_usuarios' | 'max_produtos'>
>;
