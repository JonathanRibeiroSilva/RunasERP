import { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { FiArrowLeft, FiTrash2, FiMinus, FiPlus, FiShoppingBag, FiBox } from 'react-icons/fi';
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
    } catch {
      // useCarrinho já publicou a mensagem em `erro`, renderizada acima. Só
      // engolimos o rethrow para não virar unhandled rejection.
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
    } catch {
      // idem: a mensagem já está em `erro`.
    } finally {
      setProcessandoItem(null);
    }
  };

  const handleLimparCarrinho = async () => {
    if (!window.confirm('Deseja realmente limpar o carrinho?')) return;

    try {
      await limparCarrinho();
    } catch {
      // idem: a mensagem já está em `erro`.
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
      <div className="store-page-wrapper carrinho-page-modern">
        <div className="loading-state">
          <div className="spinner" />
          <p>Carregando carrinho...</p>
        </div>
      </div>
    );
  }

  const carrinhoVazio = !carrinho || carrinho.itens.length === 0;

  return (
    <div className="store-page-wrapper carrinho-page-modern">
      {/* Header */}
      <header className="store-header-simple">
        <div className="header-simple-content">
          <button className="btn-voltar-modern" onClick={handleVoltar}>
            <FiArrowLeft /> Voltar ao catálogo
          </button>

          <div className="cart-title-area">
            <h1>
              <FiShoppingBag className="title-icon" /> Seu Carrinho
            </h1>
            {!carrinhoVazio && (
              <span className="badge-quantidade-modern">
                {carrinho.quantidade_itens} {carrinho.quantidade_itens === 1 ? 'item' : 'itens'}
              </span>
            )}
          </div>
        </div>
      </header>

      {erro && (
        <div className="erro-mensagem-modern">
          ⚠️ {erro}
        </div>
      )}

      {carrinhoVazio ? (
        <div className="carrinho-vazio-modern">
          <div className="vazio-icon-wrapper">
            <FiShoppingBag className="vazio-icon" />
          </div>
          <h2>Seu carrinho está vazio</h2>
          <p>Adicione produtos no catálogo para continuar com suas compras</p>
          <button className="btn-buscar-produtos" onClick={handleVoltar}>
            Ver produtos
          </button>
        </div>
      ) : (
        <div className="carrinho-container-modern">
          {/* Lista de Itens */}
          <div className="itens-section-modern">
            <div className="itens-header-modern">
              <h3>Itens no carrinho</h3>
              <button className="btn-limpar-modern" onClick={handleLimparCarrinho}>
                <FiTrash2 /> Limpar carrinho
              </button>
            </div>

            <div className="itens-lista-modern">
              {carrinho.itens.map((item) => {
                const itemKey = getItemKey(item);
                const quantidadeNum = parseFloat(item.quantidade);

                return (
                  <div
                    key={itemKey}
                    className={`item-carrinho-modern ${processandoItem === itemKey ? 'processando' : ''}`}
                  >
                    <div className="item-imagem-modern">
                      <FiBox className="placeholder-icon" />
                    </div>

                    <div className="item-info-modern">
                      <h4 className="item-nome-modern">{item.descricao_produto}</h4>
                      <div className="item-preco-unitario-modern">
                        {formatarPreco(item.preco_unitario)} / unidade
                      </div>
                    </div>

                    <div className="item-acoes-modern">
                      <div className="quantidade-editor-modern">
                        <button
                          className="btn-quantidade-modern"
                          onClick={() => handleAtualizarQuantidade(item.produto_id, item.variante_id, quantidadeNum - 1)}
                          disabled={quantidadeNum <= 1 || processandoItem === itemKey}
                        >
                          <FiMinus />
                        </button>
                        <span className="quantidade-valor-modern">{quantidadeNum}</span>
                        <button
                          className="btn-quantidade-modern"
                          onClick={() => handleAtualizarQuantidade(item.produto_id, item.variante_id, quantidadeNum + 1)}
                          disabled={processandoItem === itemKey}
                        >
                          <FiPlus />
                        </button>
                      </div>

                      <div className="item-subtotal-modern">
                        {formatarPreco(item.subtotal)}
                      </div>

                      <button
                        className="btn-remover-modern"
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
          <div className="resumo-section-modern">
            <div className="resumo-card-modern">
              <h3>Resumo do pedido</h3>

              <div className="resumo-linha-modern">
                <span>Subtotal ({carrinho.quantidade_itens} itens)</span>
                <span className="resumo-valor-modern">{formatarPreco(carrinho.subtotal)}</span>
              </div>

              <div className="resumo-info-modern">
                <small>O frete será calculado no checkout</small>
              </div>

              <div className="resumo-total-modern">
                <span>Total</span>
                <span className="total-valor-modern">{formatarPreco(carrinho.subtotal)}</span>
              </div>

              <button
                className="btn-checkout-modern"
                onClick={handleCheckout}
                disabled={loading}
              >
                Finalizar compra
              </button>

              <button className="btn-continuar-comprando-secondary-modern" onClick={handleVoltar}>
                Continuar comprando
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Footer */}
      <footer className="store-footer-simple">
        <p>Powered by <strong>Runas ERP</strong></p>
      </footer>
    </div>
  );
};

export default CarrinhoPage;
