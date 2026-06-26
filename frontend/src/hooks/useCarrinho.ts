import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';

// Instância axios pública para o carrinho
const apiPublica = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
  withCredentials: true,  // ✅ CRITICAL: Envia cookies HTTP-only em todas as requisições
});

// Tipos (alinhados com o backend)
export interface ItemCarrinho {
  produto_id: string;
  variante_id: string | null;
  quantidade: string; // Backend retorna como string (Decimal serializado)
  codigo_produto: string | null;
  descricao_produto: string;
  preco_unitario: string; // Backend retorna como string (Decimal serializado)
  subtotal: string; // Backend retorna como string (Decimal serializado)
  estoque_disponivel: boolean;
}

export interface Carrinho {
  sessao_id: string;
  empresa_id: number;
  itens: ItemCarrinho[];
  subtotal: string; // Backend retorna como string (Decimal serializado)
  quantidade_itens: number;
  criado_em: string;
  atualizado_em: string;
}

interface UseCarrinhoReturn {
  carrinho: Carrinho | null;
  loading: boolean;
  erro: string | null;
  adicionarItem: (produtoId: string, varianteId: string, quantidade: number) => Promise<void>;
  removerItem: (produtoId: string, varianteId: string | null) => Promise<void>;
  atualizarQuantidade: (produtoId: string, varianteId: string | null, quantidade: number) => Promise<void>;
  limparCarrinho: () => Promise<void>;
  carregarCarrinho: () => Promise<void>;
}

interface UseCarrinhoProps {
  empresaSlug?: string;
}

export const useCarrinho = (props?: UseCarrinhoProps): UseCarrinhoReturn => {
  const [carrinho, setCarrinho] = useState<Carrinho | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [erro, setErro] = useState<string | null>(null);

  const empresaSlug = props?.empresaSlug;

  // Carregar carrinho ao montar o hook
  useEffect(() => {
    carregarCarrinho();
  }, [empresaSlug]);

  /**
   * Carrega o carrinho atual da sessão
   */
  const carregarCarrinho = useCallback(async () => {
    try {
      setLoading(true);
      setErro(null);
      
      // 🔍 DEBUG: Verificar cookies
      console.log('🔍 DEBUG [useCarrinho]: Carregando carrinho');
      console.log('🔍 DEBUG [useCarrinho]: Cookies:', document.cookie);
      
      // Montar query params
      const params = new URLSearchParams();
      if (empresaSlug) {
        params.append('empresaSlug', empresaSlug);
      }
      
      const url = `/loja/carrinho${params.toString() ? `?${params.toString()}` : ''}`;
      console.log('🔍 DEBUG [useCarrinho]: URL da requisição:', url);
      
      const response = await apiPublica.get(url);
      console.log('🔍 DEBUG [useCarrinho]: Carrinho carregado:', {
        quantidade_itens: response.data.quantidade_itens,
        subtotal: response.data.subtotal,
        sessao_id: response.data.sessao_id
      });
      
      setCarrinho(response.data);
    } catch (error: any) {
      console.error('🔍 DEBUG [useCarrinho]: Erro ao carregar carrinho:', error);
      if (error.response?.status === 404) {
        // Carrinho vazio
        setCarrinho({ 
          sessao_id: '', 
          empresa_id: 0,
          itens: [], 
          subtotal: '0.0', 
          quantidade_itens: 0,
          criado_em: new Date().toISOString(),
          atualizado_em: new Date().toISOString()
        });
      } else {
        setErro(error.response?.data?.detail || 'Erro ao carregar carrinho');
      }
    } finally {
      setLoading(false);
    }
  }, [empresaSlug]);

  /**
   * Adiciona um item ao carrinho
   */
  const adicionarItem = async (
    produtoId: string,
    varianteId: string,
    quantidade: number
  ): Promise<void> => {
    try {
      setLoading(true);
      setErro(null);
      
      // Montar query params
      const params = new URLSearchParams();
      if (empresaSlug) {
        params.append('empresaSlug', empresaSlug);
      }
      
      const url = `/loja/carrinho/itens${params.toString() ? `?${params.toString()}` : ''}`;
      const response = await apiPublica.post(url, {
        produto_id: produtoId,
        variante_id: varianteId,
        quantidade,
      });

      setCarrinho(response.data);
    } catch (error: any) {
      const mensagemErro = error.response?.data?.detail || 'Erro ao adicionar item';
      setErro(mensagemErro);
      throw new Error(mensagemErro);
    } finally {
      setLoading(false);
    }
  };

  /**
   * Remove um item do carrinho
   */
  const removerItem = async (produtoId: string, varianteId: string | null): Promise<void> => {
    try {
      setLoading(true);
      setErro(null);
      
      // Montar query params
      const params = new URLSearchParams();
      if (empresaSlug) {
        params.append('empresaSlug', empresaSlug);
      }
      if (varianteId) {
        params.append('variante_id', varianteId);
      }
      
      const url = `/loja/carrinho/itens/${produtoId}${params.toString() ? `?${params.toString()}` : ''}`;
      const response = await apiPublica.delete(url);
      setCarrinho(response.data);
    } catch (error: any) {
      const mensagemErro = error.response?.data?.detail || 'Erro ao remover item';
      setErro(mensagemErro);
      throw new Error(mensagemErro);
    } finally {
      setLoading(false);
    }
  };

  /**
   * Atualiza a quantidade de um item
   */
  const atualizarQuantidade = async (produtoId: string, varianteId: string | null, quantidade: number): Promise<void> => {
    try {
      setLoading(true);
      setErro(null);
      
      // Montar query params
      const params = new URLSearchParams();
      if (empresaSlug) {
        params.append('empresaSlug', empresaSlug);
      }
      if (varianteId) {
        params.append('variante_id', varianteId);
      }
      
      const url = `/loja/carrinho/itens/${produtoId}${params.toString() ? `?${params.toString()}` : ''}`;
      const response = await apiPublica.put(url, {
        quantidade,
      });
      
      setCarrinho(response.data);
    } catch (error: any) {
      const mensagemErro = error.response?.data?.detail || 'Erro ao atualizar quantidade';
      setErro(mensagemErro);
      throw new Error(mensagemErro);
    } finally {
      setLoading(false);
    }
  };

  /**
   * Limpa o carrinho
   */
  const limparCarrinho = async (): Promise<void> => {
    try {
      setLoading(true);
      setErro(null);
      
      // Montar query params
      const params = new URLSearchParams();
      if (empresaSlug) {
        params.append('empresaSlug', empresaSlug);
      }
      
      const url = `/loja/carrinho${params.toString() ? `?${params.toString()}` : ''}`;
      await apiPublica.delete(url);
      setCarrinho({ 
        sessao_id: '', 
        empresa_id: 0,
        itens: [], 
        subtotal: '0.0', 
        quantidade_itens: 0,
        criado_em: new Date().toISOString(),
        atualizado_em: new Date().toISOString()
      });
    } catch (error: any) {
      const mensagemErro = error.response?.data?.detail || 'Erro ao limpar carrinho';
      setErro(mensagemErro);
      throw new Error(mensagemErro);
    } finally {
      setLoading(false);
    }
  };

  return {
    carrinho,
    loading,
    erro,
    adicionarItem,
    removerItem,
    atualizarQuantidade,
    limparCarrinho,
    carregarCarrinho,
  };
};
