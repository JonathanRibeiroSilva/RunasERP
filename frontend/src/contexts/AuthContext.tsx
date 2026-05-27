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
  const initAuthRef = React.useRef(false);

  useEffect(() => {
    if (initAuthRef.current) return;
    initAuthRef.current = true;

    const initAuth = async () => {
      try {
        const currentUser = await authService.getCurrentUser();
        setUser(currentUser);
      } catch (error) {
        // Usuário não autenticado — esperado quando não há cookie válido
      } finally {
        setIsLoading(false);
      }
    };

    initAuth();
  }, []);

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
    setUser(userData);
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
