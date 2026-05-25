// Tipos relacionados à autenticação

export interface User {
  id: string;
  email: string;
  nome: string;
  role: UserRole;
  ativo: boolean;
  created_at: string;
  updated_at: string;
}

export type UserRole = 'ADMIN' | 'OPERADOR';

export interface LoginRequest {
  username: string; // email
  password: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
}

export interface RefreshTokenRequest {
  refresh_token: string;
}

export interface RefreshTokenResponse {
  access_token: string;
  token_type: string;
}

export interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  hasRole: (role: UserRole) => boolean;
}
