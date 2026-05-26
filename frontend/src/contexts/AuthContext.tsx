import React, { createContext, useState, useEffect, ReactNode } from 'react';
import { authService } from '@/services/auth/authService';
import type { User, UserRole, AuthContextType } from '@/types/auth';
import { toast } from 'react-toastify';

export const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Verificar se usuário está autenticado ao carregar
  useEffect(() => {
    const initAuth = async () => {
      console.log('[AuthContext] Iniciando verificação de autenticação...');
      
      // Com cookies HTTP-only, sempre tentamos buscar o usuário
      // Se houver cookie válido, o backend retornará o usuário
      // Se não houver, retornará 401
      try {
        console.log('[AuthContext] Buscando usuário atual...');
        const currentUser = await authService.getCurrentUser();
        console.log('[AuthContext] Usuário carregado:', currentUser);
        setUser(currentUser);
      } catch (error) {
        console.error('[AuthContext] Erro ao carregar usuário:', error);
        // Usuário não autenticado ou erro na requisição
        // Isso é esperado se não houver cookie válido
      }
      setIsLoading(false);
      console.log('[AuthContext] Verificação concluída, isLoading = false');
    };

    initAuth();
  }, []); // Array vazio para executar apenas uma vez

  const login = async (email: string, password: string): Promise<void> => {
    try {
      const response = await authService.login(email, password);
      setUser(response.user);
      toast.success(`Bem-vindo, ${response.user.nome}!`);
    } catch (error) {
      console.error('Erro ao fazer login:', error);
      throw error;
    }
  };

  const setAuthUser = (userData: User): void => {
    console.log('[AuthContext] setAuthUser chamado com:', userData);
    setUser(userData);
    console.log('[AuthContext] Estado do usuário atualizado');
  };

  const logout = async (): Promise<void> => {
    try {
      await authService.logout();
      setUser(null);
      toast.info('Você saiu do sistema');
    } catch (error) {
      console.error('Erro ao fazer logout:', error);
      // Mesmo com erro, limpar estado local
      setUser(null);
    }
  };

  const hasRole = (role: UserRole): boolean => {
    return user?.role === role;
  };

  const value: AuthContextType = {
    user,
    isAuthenticated: !!user,
    isLoading,
    login,
    logout,
    setAuthUser,
    hasRole,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
