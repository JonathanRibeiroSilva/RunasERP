import { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { FiArrowLeft, FiTrash2, FiMinus, FiPlus, FiShoppingBag } from 'react-icons/fi';
import { useCarrinho } from '@/hooks/useCarrinho';
import './CarrinhoPage.scss';

const CarrinhoPage = () => {
  const { empresaSlug } = useParams<{ empresaSlug: string }>();
  const navigate = useNavigate();
  const { 
    carrinho, 
    loading, 
    erro, 
    removerItem, 
    atualizarQuantidade, 
    limparCarrinho 
  } = useCarrinho({ empresaSlug });

  const [processandoItem, setProcessandoItem] = useState<string | null>(null);

  const formatarPreco = (valor: string | number) => {
    const valorNum = typeof valor === 'string' ? parseFloat(valor) : valor;
    return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(valorNum);
  };

  // Gera chave única para cada item (produto_id + variante_id)
  const getItemKey = (item: any) => {
    return `${item.produto_id}-${item.variante_id || 'null'}`;
  };

  const handleRemoverItem = async (produtoId: string, varianteId: string | null) => {
    try {
      const key = `${produtoId}-${varianteId || 'null'}`;
      setProcessandoItem(key);
      await removerItem(produtoId, varianteId);
    } catch (error) {
      console.error('Erro ao remover item:', error);
    } finally {
      setProcessandoItem(null);
    }
  };

  const handleAtualizarQuantidade = async (produtoId: string, varianteId: string | null, novaQuantidade: number) => {
    if (novaQuantidade < 1) return;
    
    try {
      const key = `${produtoId}-${varianteId || 'null'}`;
      setProcessandoItem(key);
      await atualizarQuantidade(produtoId, varianteId, novaQuantidade);
    } catch (error) {
      console.error('Erro ao atualizar quantidade:', error);
    } finally {
      setProcessandoItem(null);
    }
  };

  const handleLimparCarrinho = async () => {
    if (!window.confirm('Deseja realmente limpar o carrinho?')) return;
    
    try {
      await limparCarrinho();
    } catch (error) {
      console.error('Erro ao limpar carrinho:', error);
    }
  };

  const handleVoltar = () => {
    navigate(`/c/${empresaSlug}`);
  };

  const handleCheckout = () => {
    navigate(`/c/${empresaSlug}/checkout`);
  };

  if (loading && !carrinho) {
    return (
      <div className="carrinho-page">
        <div className="loading">
          <div className="spinner" />
          <p>Carregando carrinho...</p>
        </div>
      </div>
    );
  }

  const carrinhoVazio = !carrinho || carrinho.itens.length === 0;

  return (
    <div className="carrinho-page">
      {/* Header */}
      <header className="carrinho-header">
        <button className="btn-voltar" onClick={handleVoltar}>
          <FiArrowLeft /> Voltar ao catálogo
        </button>
        <h1>
          <FiShoppingBag />
          Seu Carrinho
          {!carrinhoVazio && (
            <span className="badge-quantidade">
              {carrinho.quantidade_itens} {carrinho.quantidade_itens === 1 ? 'item' : 'itens'}
            </span>
          )}
        </h1>
      </header>

      {erro && (
        <div className="erro-mensagem">
          ⚠️ {erro}
        </div>
      )}

      {carrinhoVazio ? (
        <div className="carrinho-vazio">
          <div className="vazio-icon">🛒</div>
          <h2>Seu carrinho está vazio</h2>
          <p>Adicione produtos para continuar comprando</p>
          <button className="btn-continuar-comprando" onClick={handleVoltar}>
            Ver produtos
          </button>
        </div>
      ) : (
        <div className="carrinho-container">
          {/* Lista de Itens */}
          <div className="itens-section">
            <div className="itens-header">
              <h3>Itens no carrinho</h3>
              <button className="btn-limpar" onClick={handleLimparCarrinho}>
                <FiTrash2 /> Limpar carrinho
              </button>
            </div>

            <div className="itens-lista">
              {carrinho.itens.map((item) => {
                const itemKey = getItemKey(item);
                const quantidadeNum = parseFloat(item.quantidade);
                
                return (
                  <div 
                    key={itemKey}
                    className={`item-carrinho ${processandoItem === itemKey ? 'processando' : ''}`}
                  >
                    <div className="item-imagem">
                      <FiShoppingBag />
                    </div>

                    <div className="item-info">
                      <h4 className="item-nome">{item.descricao_produto}</h4>
                      <div className="item-preco-unitario">
                        {formatarPreco(item.preco_unitario)} / unidade
                      </div>
                    </div>

                    <div className="item-acoes">
                      <div className="quantidade-editor">
                        <button
                          className="btn-quantidade"
                          onClick={() => handleAtualizarQuantidade(item.produto_id, item.variante_id, quantidadeNum - 1)}
                          disabled={quantidadeNum <= 1 || processandoItem === itemKey}
                        >
                          <FiMinus />
                        </button>
                        <span className="quantidade-valor">{quantidadeNum}</span>
                        <button
                          className="btn-quantidade"
                          onClick={() => handleAtualizarQuantidade(item.produto_id, item.variante_id, quantidadeNum + 1)}
                          disabled={processandoItem === itemKey}
                        >
                          <FiPlus />
                        </button>
                      </div>

                      <div className="item-subtotal">
                        {formatarPreco(item.subtotal)}
                      </div>

                      <button
                        className="btn-remover"
                        onClick={() => handleRemoverItem(item.produto_id, item.variante_id)}
                        disabled={processandoItem === itemKey}
                        title="Remover item"
                      >
                        <FiTrash2 />
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Resumo */}
          <div className="resumo-section">
            <div className="resumo-card">
              <h3>Resumo do pedido</h3>

              <div className="resumo-linha">
                <span>Subtotal ({carrinho.quantidade_itens} itens)</span>
                <span className="resumo-valor">{formatarPreco(carrinho.subtotal)}</span>
              </div>

              <div className="resumo-info">
                <small>O frete será calculado no checkout</small>
              </div>

              <div className="resumo-total">
                <span>Total</span>
                <span className="total-valor">{formatarPreco(carrinho.subtotal)}</span>
              </div>

              <button 
                className="btn-checkout" 
                onClick={handleCheckout}
                disabled={loading}
              >
                Finalizar compra
              </button>

              <button className="btn-continuar-comprando-secondary" onClick={handleVoltar}>
                Continuar comprando
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Footer */}
      <footer className="loja-online-footer">
        <p>Powered by <strong>Runas ERP</strong></p>
      </footer>
    </div>
  );
};

export default CarrinhoPage;
