import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { FiArrowLeft, FiPackage, FiTag, FiShare2, FiCopy, FiShoppingCart, FiCheck } from 'react-icons/fi';
import { apiPublica } from '@/services/api/apiPublica';
import { getErrorMessage } from '@/services/api/axios';
import { useCarrinho } from '@/hooks/useCarrinho';
import './ProdutoDetalhePage.scss';

interface Variante {
  id: string;
  sku: string;
  preco_custo: number;
  markup_pct: number;
  preco_venda: number;
  ativo: boolean;
  atributos: { chave: string; valor: string }[];
}

interface Produto {
  id: string;
  nome: string;
  descricao?: string;
  categoria_id: string;
  categoria?: { id: string; nome: string };
  ativo: boolean;
  criado_em: string;
  preco: string | number;
  preco_promocional?: string | number | null;
  variantes: Variante[];
}

const ProdutoDetalhePage = () => {
  const { empresaSlug, produtoId } = useParams<{ empresaSlug: string; produtoId: string }>();
  const navigate = useNavigate();
  const { adicionarItem, carrinho } = useCarrinho({ empresaSlug });

  const [produto, setProduto] = useState<Produto | null>(null);
  const [loading, setLoading] = useState(true);
  const [erro, setErro] = useState('');
  const [varianteSelecionada, setVarianteSelecionada] = useState<Variante | null>(null);
  const [linkCopiado, setLinkCopiado] = useState(false);
  const [quantidade, setQuantidade] = useState(1);
  const [adicionandoCarrinho, setAdicionandoCarrinho] = useState(false);
  const [itemAdicionado, setItemAdicionado] = useState(false);

  const carregarProduto = useCallback(async () => {
    try {
      setLoading(true);
      const response = await apiPublica.get(`/loja-online/publico/produto/${produtoId}?empresaSlug=${empresaSlug}`);
      const data = response.data;
      setProduto(data);

      // Selecionar primeira variante ativa por padrão
      const primeiraAtiva = data.variantes?.find((v: Variante) => v.ativo);
      if (primeiraAtiva) setVarianteSelecionada(primeiraAtiva);
    } catch (error) {
      setErro(getErrorMessage(error, 'Produto não encontrado'));
    } finally {
      setLoading(false);
    }
  }, [produtoId, empresaSlug]);

  useEffect(() => {
    if (produtoId) carregarProduto();
  }, [produtoId, carregarProduto]);

  const handleCopiarLink = () => {
    navigator.clipboard.writeText(window.location.href).then(() => {
      setLinkCopiado(true);
      setTimeout(() => setLinkCopiado(false), 2000);
    });
  };

  const handleWhatsApp = () => {
    const url = encodeURIComponent(window.location.href);
    const texto = encodeURIComponent(`Olha esse produto: ${produto?.nome} 🛍️`);
    window.open(`https://wa.me/?text=${texto}%20${url}`, '_blank');
  };

  const formatarPreco = (valor: number) =>
    new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(valor);

  const handleAdicionarCarrinho = async () => {
    const temVariantes = (produto?.variantes || []).some((v) => v.ativo);
    if (temVariantes && !varianteSelecionada) {
      alert('Selecione uma opção do produto');
      return;
    }

    try {
      setAdicionandoCarrinho(true);
      await adicionarItem(produto!.id, varianteSelecionada?.id ?? null, quantidade);
      setItemAdicionado(true);
      navigate(`/c/${empresaSlug}/carrinho`);
    } catch (error) {
      alert(getErrorMessage(error, 'Erro ao adicionar ao carrinho'));
    } finally {
      setAdicionandoCarrinho(false);
    }
  };

  const handleIrParaCarrinho = () => {
    navigate(`/c/${empresaSlug}/carrinho`);
  };

  if (loading) {
    return (
      <div className="produto-detalhe-page">
        <div className="loading">
          <div className="spinner" />
          <p>Carregando produto...</p>
        </div>
      </div>
    );
  }

  if (erro || !produto) {
    return (
      <div className="produto-detalhe-page">
        <div className="erro-state">
          <span className="erro-icon">😕</span>
          <h2>Produto não encontrado</h2>
          <p>{erro}</p>
          <button onClick={() => navigate(`/c/${empresaSlug}`)}>
            <FiArrowLeft /> Voltar ao catálogo
          </button>
        </div>
      </div>
    );
  }

  const variantesAtivas = produto.variantes?.filter((v) => v.ativo) || [];
  const precoProduto = Number(produto.preco) || 0;
  // Produto sem variantes mas com preço próprio: compra direta pelo preço do produto
  const compraDireta = variantesAtivas.length === 0 && precoProduto > 0;
  const menorPreco = variantesAtivas.length > 0
    ? Math.min(...variantesAtivas.map((v) => v.preco_venda))
    : compraDireta
      ? precoProduto
      : null;

  return (
    <div className="produto-detalhe-page">
      {/* Navbar simples */}
      <nav className="detalhe-nav">
        <button className="btn-voltar" onClick={() => navigate(`/c/${empresaSlug}`)}>
          <FiArrowLeft /> Voltar ao catálogo
        </button>
        <div className="nav-actions">
          <button className="btn-share" onClick={handleCopiarLink} title="Copiar link">
            {linkCopiado ? <FiCopy /> : <FiShare2 />}
            {linkCopiado ? 'Copiado!' : 'Compartilhar'}
          </button>
          <button className="btn-whatsapp-sm" onClick={handleWhatsApp} title="WhatsApp">
            <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
              <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/>
            </svg>
          </button>
        </div>
      </nav>

      <div className="detalhe-container">
        {/* Imagem */}
        <div className="produto-imagem-section">
          <div className="produto-imagem-placeholder">
            <FiPackage />
          </div>
        </div>

        {/* Informações */}
        <div className="produto-info-section">
          {produto.categoria && (
            <div className="produto-categoria">
              <FiTag />
              <span>{produto.categoria.nome}</span>
            </div>
          )}

          <h1 className="produto-nome">{produto.nome}</h1>

          {produto.descricao && (
            <p className="produto-descricao">{produto.descricao}</p>
          )}

          {/* Preço */}
          {menorPreco !== null && (
            <div className="produto-preco-section">
              {variantesAtivas.length > 1 ? (
                <span className="produto-preco">
                  A partir de {formatarPreco(menorPreco)}
                </span>
              ) : (
                <span className="produto-preco">{formatarPreco(menorPreco)}</span>
              )}
            </div>
          )}

          {/* Variantes */}
          {variantesAtivas.length > 0 && (
            <div className="variantes-section">
              <h3>Opções disponíveis</h3>
              <div className="variantes-lista">
                {variantesAtivas.map((variante) => (
                  <div
                    key={variante.id}
                    className={`variante-item ${varianteSelecionada?.id === variante.id ? 'selecionada' : ''}`}
                    onClick={() => setVarianteSelecionada(variante)}
                  >
                    <div className="variante-preco">{formatarPreco(variante.preco_venda)}</div>
                    {variante.atributos?.length > 0 && (
                      <div className="variante-atributos">
                        {variante.atributos.map((attr, i) => (
                          <span key={i} className="atributo-badge">
                            {attr.chave}: {attr.valor}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Controle de Quantidade */}
          {(varianteSelecionada || compraDireta) && (
            <div className="quantidade-section">
              <label>Quantidade</label>
              <div className="quantidade-controle">
                <button
                  onClick={() => setQuantidade(Math.max(1, quantidade - 1))}
                  disabled={quantidade <= 1}
                >
                  -
                </button>
                <input
                  type="number"
                  min="1"
                  value={quantidade}
                  onChange={(e) => setQuantidade(Math.max(1, parseInt(e.target.value) || 1))}
                />
                <button onClick={() => setQuantidade(quantidade + 1)}>
                  +
                </button>
              </div>
            </div>
          )}

          {/* Botões de Ação */}
          {(varianteSelecionada || compraDireta) && (
            <div className="acoes-section">
              <button
                className={`btn-adicionar-carrinho ${itemAdicionado ? 'adicionado' : ''}`}
                onClick={handleAdicionarCarrinho}
                disabled={adicionandoCarrinho || itemAdicionado}
              >
                {itemAdicionado ? (
                  <>
                    <FiCheck /> Adicionado!
                  </>
                ) : (
                  <>
                    <FiShoppingCart />
                    {adicionandoCarrinho ? 'Adicionando...' : 'Adicionar ao Carrinho'}
                  </>
                )}
              </button>

              {carrinho && carrinho.itens.length > 0 && (
                <button className="btn-ver-carrinho" onClick={handleIrParaCarrinho}>
                  Ver Carrinho ({carrinho.quantidade_itens})
                </button>
              )}
            </div>
          )}

        </div>
      </div>

      <footer className="loja-online-footer">
        <p>Powered by <strong>Runas ERP</strong></p>
      </footer>
    </div>
  );
};

export default ProdutoDetalhePage;
