import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';

// Instância axios pública para o carrinho
const apiPublica = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
});

// Tipos
export interface ItemCarrinho {
  id: string;
  produto_id: string;
  variante_id: string;
  quantidade: number;
  preco_unitario: number;
  subtotal: number;
  produto_nome: string;
  variante_sku: string;
  variante_atributos?: { chave: string; valor: string }[];
}

export interface Carrinho {
  sessao_id: string;
  itens: ItemCarrinho[];
  total: number;
  quantidade_total: number;
}

interface UseCarrinhoReturn {
  carrinho: Carrinho | null;
  loading: boolean;
  erro: string | null;
  adicionarItem: (produtoId: string, varianteId: string, quantidade: number) => Promise<void>;
  removerItem: (itemId: string) => Promise<void>;
  atualizarQuantidade: (itemId: string, quantidade: number) => Promise<void>;
  limparCarrinho: () => Promise<void>;
  carregarCarrinho: () => Promise<void>;
}

export const useCarrinho = (): UseCarrinhoReturn => {
  const [carrinho, setCarrinho] = useState<Carrinho | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [erro, setErro] = useState<string | null>(null);

  // Carregar carrinho ao montar o hook
  useEffect(() => {
    carregarCarrinho();
  }, []);

  /**
   * Carrega o carrinho atual da sessão
   */
  const carregarCarrinho = useCallback(async () => {
    try {
      setLoading(true);
      setErro(null);
      const response = await apiPublica.get('/loja/carrinho');
      setCarrinho(response.data);
    } catch (error: any) {
      if (error.response?.status === 404) {
        // Carrinho vazio
        setCarrinho({ sessao_id: '', itens: [], total: 0, quantidade_total: 0 });
      } else {
        setErro(error.response?.data?.detail || 'Erro ao carregar carrinho');
      }
    } finally {
      setLoading(false);
    }
  }, []);

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
      
      const response = await apiPublica.post('/loja/carrinho/itens', {
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
  const removerItem = async (itemId: string): Promise<void> => {
    try {
      setLoading(true);
      setErro(null);
      
      const response = await apiPublica.delete(`/loja/carrinho/itens/${itemId}`);
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
  const atualizarQuantidade = async (itemId: string, quantidade: number): Promise<void> => {
    try {
      setLoading(true);
      setErro(null);
      
      const response = await apiPublica.put(`/loja/carrinho/itens/${itemId}`, {
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
      
      await apiPublica.delete('/loja/carrinho');
      setCarrinho({ sessao_id: '', itens: [], total: 0, quantidade_total: 0 });
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
