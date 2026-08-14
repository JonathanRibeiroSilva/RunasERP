import { useState, useEffect, useCallback } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { FiSearch, FiShare2, FiCopy, FiShoppingCart, FiUser, FiPhone, FiMapPin, FiGrid, FiTag } from 'react-icons/fi';
import { apiPublica } from '@/services/api/apiPublica';
import { getErrorStatus } from '@/services/api/axios';
import ProdutoCard from './components/ProdutoCard';
import { useCarrinho } from '@/hooks/useCarrinho';
import './LojaOnlinePublicoPage.scss';

interface Produto {
  id: string;
  nome: string;
  descricao?: string;
  categoria_id: string;
  ativo: boolean;
  criado_em: string;
  preco?: string | number;
  preco_promocional?: string | number | null;
}

interface Categoria {
  id: string;
  nome: string;
}

// Espelha EmpresaPublicInfo do backend (GET /empresas/publico/{slug})
interface EmpresaInfo {
  nome_fantasia: string;
  logo_url?: string | null;
  catalogo_ativo?: boolean;
  catalogo_titulo?: string | null;
  catalogo_descricao?: string | null;
  catalogo_whatsapp?: string | null;
  cidade?: string | null;
  uf?: string | null;
}

const LojaOnlinePublicoPage = () => {
  const navigate = useNavigate();
  const { empresaSlug } = useParams<{ empresaSlug: string }>();
  const { carrinho, adicionarItem } = useCarrinho({ empresaSlug });

  const [produtos, setProdutos] = useState<Produto[]>([]);
  const [categorias, setCategorias] = useState<Categoria[]>([]);
  const [empresaInfo, setEmpresaInfo] = useState<EmpresaInfo | null>(null);
  const [lojaNaoEncontrada, setLojaNaoEncontrada] = useState(false);
  const [loading, setLoading] = useState(true);
  const [linkCopiado, setLinkCopiado] = useState(false);

  // Filtros
  const [busca, setBusca] = useState('');
  const [categoriaFiltro, setCategoriaFiltro] = useState('');
  const [ordenacao, setOrdenacao] = useState('nome');

  const carregarDados = useCallback(async (buscaParam?: string) => {
    try {
      setLoading(true);
      setLojaNaoEncontrada(false);

      // Carregar dados da empresa primeiro — slug inexistente = loja não existe
      try {
        const empresaRes = await apiPublica.get(`/empresas/publico/${empresaSlug}`);
        setEmpresaInfo(empresaRes.data);
      } catch (err) {
        if (getErrorStatus(err) === 404) {
          setLojaNaoEncontrada(true);
          return;
        }
        // Outros erros (rede etc.): segue e tenta carregar o catálogo
      }

      // Carregar produtos e categorias (agora usando empresaSlug como query param)
      const params = new URLSearchParams({
        empresaSlug: empresaSlug!,
        limit: '100',
        ordenar: ordenacao
      });
      if (categoriaFiltro) params.append('categoria_id', categoriaFiltro);
      if (buscaParam && buscaParam.length >= 2) params.append('busca', buscaParam);

      const [produtosRes, categoriasRes] = await Promise.all([
        apiPublica.get(`/loja-online/publico/produtos?${params}`).catch(() => {
          return { data: { items: [] } };
        }),
        apiPublica.get(`/loja-online/publico/categorias?empresaSlug=${empresaSlug}`).catch(() => {
          return { data: { items: [] } };
        }),
      ]);

      setProdutos(produtosRes.data.items || []);
      setCategorias(categoriasRes.data.items || []);
    } catch {
      // Erro ao carregar catálogo
    } finally {
      setLoading(false);
    }
  }, [categoriaFiltro, ordenacao, empresaSlug]);

  useEffect(() => {
    carregarDados();
  }, [carregarDados]);

  const handleLimparBusca = () => {
    setBusca('');
    carregarDados();
  };

  const handleCopiarLink = () => {
    const url = window.location.href;
    navigator.clipboard.writeText(url).then(() => {
      setLinkCopiado(true);
      setTimeout(() => setLinkCopiado(false), 2000);
    });
  };

  const handleWhatsApp = () => {
    const url = encodeURIComponent(window.location.href);
    const texto = encodeURIComponent('Confira nosso catálogo de produtos! 🛍️');
    window.open(`https://wa.me/?text=${texto}%20${url}`, '_blank');
  };

  const handleAdicionarAoCarrinho = async (produtoId: string) => {
    try {
      // Buscar detalhes do produto para verificar variantes/preço
      const response = await apiPublica.get(`/loja-online/publico/produto/${produtoId}?empresaSlug=${empresaSlug}`);
      const produto = response.data;

      if (!produto.ativo) {
        navigate(`/c/${empresaSlug}/produto/${produtoId}`);
        return;
      }

      const variantesAtivas = (produto.variantes || []).filter(
        (variante: { id: string; ativo: boolean }) => variante.ativo
      );

      // Múltiplas variantes: precisa escolher na página de detalhes
      if (variantesAtivas.length > 1) {
        navigate(`/c/${empresaSlug}/produto/${produtoId}`);
        return;
      }

      // Sem variantes e sem preço: só resta o contato via detalhes
      if (variantesAtivas.length === 0 && Number(produto.preco) <= 0) {
        navigate(`/c/${empresaSlug}/produto/${produtoId}`);
        return;
      }

      // 1 variante ou produto com preço próprio: adicionar e ir pro carrinho/checkout
      await adicionarItem(produtoId, variantesAtivas[0]?.id ?? null, 1);
      navigate(`/c/${empresaSlug}/carrinho`);
    } catch {
      alert('Erro ao adicionar produto ao carrinho');
    }
  };

  const handleBuscar = () => {
    carregarDados(busca);
  };

  // Slug não corresponde a nenhuma loja: não renderizar o shell do storefront
  if (lojaNaoEncontrada) {
    return (
      <div className="store-page-wrapper">
        <div className="loja-manutencao">
          <h1>Loja não encontrada</h1>
          <p>O endereço /c/{empresaSlug} não corresponde a nenhuma loja ativa.</p>
        </div>
      </div>
    );
  }

  // Loja desabilitada pelo lojista: branding continua público, storefront não.
  if (empresaInfo && empresaInfo.catalogo_ativo === false) {
    return (
      <div className="store-page-wrapper">
        <div className="loja-manutencao">
          {empresaInfo.logo_url && (
            <img src={empresaInfo.logo_url} alt={empresaInfo.nome_fantasia} className="loja-manutencao__logo" />
          )}
          <h1>{empresaInfo.catalogo_titulo || empresaInfo.nome_fantasia}</h1>
          <p>Esta loja não está disponível no momento. Volte em breve!</p>
        </div>
      </div>
    );
  }

  const nomeLoja = empresaInfo?.catalogo_titulo || empresaInfo?.nome_fantasia || 'Loja Online';
  const subtitulo = empresaInfo?.catalogo_descricao || 'Confira nossos produtos disponíveis';
  const localizacao = [empresaInfo?.cidade, empresaInfo?.uf].filter(Boolean).join(' - ');

  return (
    <div className="store-page-wrapper">
      <header className="store-header">
        <div className="header-top">
          <div className="brand">
            <div className="brand-logo">
              {empresaInfo?.logo_url ? (
                <img src={empresaInfo.logo_url} alt={nomeLoja} />
              ) : (
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
                  <polyline points="9 22 9 12 15 12 15 22" />
                </svg>
              )}
            </div>
            <div className="brand-text">
              <div className="brand-title">
                <h1>{nomeLoja}</h1>
                <span className="badge-aberto">• Aberto agora</span>
              </div>
              <p className="brand-subtitle">{subtitulo}</p>
            </div>
          </div>

          <div className="header-actions">
            <button className="btn-action-dark" onClick={() => navigate(`/c/${empresaSlug}/login`)} title="Entrar na sua conta">
              <FiUser /> Entrar
            </button>
            <button className="btn-action-dark btn-cart" onClick={() => navigate(`/c/${empresaSlug}/carrinho`)} title="Ver carrinho">
              <FiShoppingCart /> Carrinho
              {carrinho && carrinho.quantidade_itens > 0 && (
                <span className="carrinho-badge">{carrinho.quantidade_itens}</span>
              )}
            </button>
            <button className="btn-action-dark" onClick={handleCopiarLink} title="Copiar link do catálogo">
              {linkCopiado ? <FiCopy /> : <FiShare2 />}
              {linkCopiado ? 'Link copiado!' : 'Compartilhar'}
            </button>
            <button className="btn-action-green" onClick={handleWhatsApp} title="Compartilhar no WhatsApp">
              <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
                <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z" />
              </svg>
              WhatsApp
            </button>
          </div>
        </div>

        {/* Só renderiza a faixa se a empresa preencheu algum desses campos */}
        {(localizacao || empresaInfo?.catalogo_whatsapp) && (
          <div className="header-bottom">
            {empresaInfo?.catalogo_whatsapp && (
              <div className="info-item">
                <FiPhone />
                <span className="info-muted">{empresaInfo.catalogo_whatsapp}</span>
              </div>
            )}
            {localizacao && (
              <div className="info-item">
                <FiMapPin />
                <span className="info-muted">{localizacao}</span>
              </div>
            )}
          </div>
        )}
      </header>

      <div className="store-main-container">
        <aside className="store-sidebar">
          <div className="categorias-widget">
            <h3>Categorias</h3>
            <ul className="cat-list">
              <li
                className={categoriaFiltro === '' ? 'active' : ''}
                onClick={() => setCategoriaFiltro('')}
              >
                <span className="cat-label"><FiGrid className="cat-icon" /> Todas</span>
                <span className="count">{produtos.length}</span>
              </li>
              {categorias.map((categoria) => (
                <li
                  key={categoria.id}
                  className={categoriaFiltro === categoria.id ? 'active' : ''}
                  onClick={() => setCategoriaFiltro(categoria.id)}
                >
                  <span className="cat-label"><FiTag className="cat-icon" /> {categoria.nome}</span>
                </li>
              ))}
            </ul>
          </div>
        </aside>

        <main className="store-content">
          <div className="search-bar-row">
            <div className="search-input-wrapper">
              <FiSearch className="search-icon" />
              <input
                type="text"
                placeholder="Buscar produtos..."
                value={busca}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setBusca(e.target.value)}
                onKeyDown={(e: React.KeyboardEvent) => e.key === 'Enter' && handleBuscar()}
              />
              {busca && <button className="clear-search" onClick={handleLimparBusca}>✕</button>}
            </div>
            <button className="btn-buscar-primary" onClick={handleBuscar}>Buscar</button>
          </div>

          <div className="products-section">
            <div className="products-header">
              <span className="products-count">
                <strong>{produtos.length}</strong> produto{produtos.length !== 1 ? 's' : ''}
              </span>
              <div className="sort-dropdown">
                <select
                  value={ordenacao}
                  onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setOrdenacao(e.target.value)}
                >
                  <option value="nome">Nome (A-Z)</option>
                  <option value="recentes">Mais recentes</option>
                </select>
              </div>
            </div>

            {loading ? (
              <div className="loading-state">
                <div className="spinner" />
                <p>Carregando catálogo...</p>
              </div>
            ) : produtos.length === 0 ? (
              <div className="empty-state">
                <FiSearch size={48} />
                <h3>Nenhum produto encontrado</h3>
                <p>Tente buscar por outros termos ou remover filtros.</p>
                {busca && (
                  <button className="btn-limpar-busca" onClick={handleLimparBusca}>
                    Limpar busca
                  </button>
                )}
              </div>
            ) : (
              <div className="products-grid">
                {produtos.map((produto) => (
                  <ProdutoCard
                    key={produto.id}
                    produto={produto}
                    onClick={() => navigate(`/c/${empresaSlug}/produto/${produto.id}`)}
                    onAddToCart={() => handleAdicionarAoCarrinho(produto.id)}
                  />
                ))}
              </div>
            )}
          </div>
        </main>
      </div>

      <footer className="store-footer">
        <p>Powered by <strong>Runas ERP</strong></p>
      </footer>
    </div>
  );
};

export default LojaOnlinePublicoPage;
