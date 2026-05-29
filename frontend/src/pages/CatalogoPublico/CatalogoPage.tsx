import { useState, useEffect, useCallback } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { FiSearch, FiFilter, FiShare2, FiCopy } from 'react-icons/fi';
import axios from 'axios';
import ProdutoCard from './components/ProdutoCard';
import './CatalogoPage.scss';

// Instância axios pública (sem autenticação, sem interceptors de redirect)
const apiPublica = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
});

interface Produto {
  id: string;
  nome: string;
  descricao?: string;
  categoria_id: string;
  ativo: boolean;
  criado_em: string;
}

interface Categoria {
  id: string;
  nome: string;
}

const CatalogoPage = () => {
  const navigate = useNavigate();
  const { empresaSlug } = useParams<{ empresaSlug: string }>();

  const [produtos, setProdutos] = useState<Produto[]>([]);
  const [categorias, setCategorias] = useState<Categoria[]>([]);
  const [loading, setLoading] = useState(true);
  const [linkCopiado, setLinkCopiado] = useState(false);

  // Filtros
  const [busca, setBusca] = useState('');
  const [categoriaFiltro, setCategoriaFiltro] = useState('');
  const [ordenacao, setOrdenacao] = useState('nome');

  const carregarDados = useCallback(async (buscaParam?: string) => {
    try {
      setLoading(true);

      const params = new URLSearchParams({ limit: '100', ordenar: ordenacao });
      if (categoriaFiltro) params.append('categoria_id', categoriaFiltro);
      if (buscaParam && buscaParam.length >= 2) params.append('busca', buscaParam);

      const [produtosRes, categoriasRes] = await Promise.all([
        apiPublica.get(`/catalogo/publico/produtos?${params}`),
        apiPublica.get('/catalogo/publico/categorias'),
      ]);

      setProdutos(produtosRes.data.items || []);
      setCategorias(categoriasRes.data.items || []);
    } catch (error) {
      console.error('Erro ao carregar catálogo:', error);
    } finally {
      setLoading(false);
    }
  }, [categoriaFiltro, ordenacao]);

  useEffect(() => {
    carregarDados();
  }, [carregarDados]);

  const handleBuscar = () => {
    carregarDados(busca);
  };

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

  return (
    <div className="catalogo-page">
      {/* Header */}
      <header className="catalogo-header">
        <div className="header-content">
          <div className="header-info">
            <h1>🏪 Catálogo de Produtos</h1>
            <p>Confira nossos produtos disponíveis</p>
          </div>
          <div className="header-actions">
            <button
              className="btn-compartilhar"
              onClick={handleCopiarLink}
              title="Copiar link do catálogo"
            >
              {linkCopiado ? <FiCopy /> : <FiShare2 />}
              {linkCopiado ? 'Link copiado!' : 'Compartilhar'}
            </button>
            <button
              className="btn-whatsapp"
              onClick={handleWhatsApp}
              title="Compartilhar no WhatsApp"
            >
              <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
                <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/>
              </svg>
              WhatsApp
            </button>
          </div>
        </div>
      </header>

      {/* Filtros */}
      <div className="filtros-section">
        <div className="busca-container">
          <FiSearch className="search-icon" />
          <input
            type="text"
            placeholder="Buscar produtos..."
            value={busca}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) => setBusca(e.target.value)}
            onKeyPress={(e: React.KeyboardEvent) => e.key === 'Enter' && handleBuscar()}
          />
          {busca && (
            <button className="btn-limpar" onClick={handleLimparBusca}>✕</button>
          )}
          <button onClick={handleBuscar} className="btn-buscar">Buscar</button>
        </div>

        <div className="filtros-container">
          <div className="filtro-item">
            <FiFilter />
            <select
              value={categoriaFiltro}
              onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setCategoriaFiltro(e.target.value)}
            >
              <option value="">Todas as categorias</option>
              {categorias.map((cat) => (
                <option key={cat.id} value={cat.id}>{cat.nome}</option>
              ))}
            </select>
          </div>

          <div className="filtro-item">
            <select
              value={ordenacao}
              onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setOrdenacao(e.target.value)}
            >
              <option value="nome">Nome (A-Z)</option>
              <option value="recentes">Mais recentes</option>
            </select>
          </div>
        </div>
      </div>

      {/* Conteúdo */}
      {loading ? (
        <div className="loading">
          <div className="spinner" />
          <p>Carregando produtos...</p>
        </div>
      ) : produtos.length === 0 ? (
        <div className="empty-state">
          <span className="empty-icon">📦</span>
          <p>Nenhum produto encontrado</p>
          {busca && (
            <button className="btn-limpar-busca" onClick={handleLimparBusca}>
              Limpar busca
            </button>
          )}
        </div>
      ) : (
        <>
          <div className="resultados-info">
            <span>{produtos.length} produto{produtos.length !== 1 ? 's' : ''} encontrado{produtos.length !== 1 ? 's' : ''}</span>
          </div>
          <div className="produtos-grid">
            {produtos.map((produto) => (
              <ProdutoCard
                key={produto.id}
                produto={produto}
                onClick={() => navigate(`/c/${empresaSlug}/produto/${produto.id}`)}
              />
            ))}
          </div>
        </>
      )}

      {/* Footer */}
      <footer className="catalogo-footer">
        <p>Powered by <strong>Runas ERP</strong></p>
      </footer>
    </div>
  );
};

export default CatalogoPage;
