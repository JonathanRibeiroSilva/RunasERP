import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { FiPlus, FiSearch, FiEdit2, FiEye, FiTrash2, FiShare2, FiCopy } from 'react-icons/fi';
import { toast } from 'react-toastify';
import { api } from '@/services/api/axios';
import './ProdutosPage.scss';

interface Categoria {
  id: string;
  nome: string;
}

interface Produto {
  id: string;
  nome: string;
  descricao?: string;
  categoria_id: string;
  categoria?: Categoria;
  ativo: boolean;
  criado_em: string;
  atualizado_em?: string;
}

interface ProdutosResponse {
  items: Produto[];
  total: number;
  skip: number;
  limit: number;
}

const ProdutosPage = () => {
  const navigate = useNavigate();
  const [produtos, setProdutos] = useState<Produto[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [categoriaFilter, setCategoriaFilter] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<'todos' | 'excluidos'>('todos');
  const [categorias, setCategorias] = useState<Categoria[]>([]);
  const [linkCopiado, setLinkCopiado] = useState(false);

  // Paginação
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const limit = 10;

  const catalogoUrl = `${window.location.origin}/c/default`;

  useEffect(() => {
    carregarCategorias();
  }, []);

  useEffect(() => {
    carregarProdutos();
  }, [currentPage, searchTerm, categoriaFilter, statusFilter]);

  const carregarCategorias = async () => {
    try {
      const response = await api.get('/categorias?limit=100');
      setCategorias(response.data.items || []);
    } catch (error) {
      console.error('Erro ao carregar categorias:', error);
    }
  };

  const carregarProdutos = async () => {
    try {
      setLoading(true);
      
      const params: Record<string, string | number | boolean> = {
        skip: (currentPage - 1) * limit,
        limit,
        apenas_deletados: statusFilter === 'excluidos',
      };

      const response = await api.get<ProdutosResponse>('/produtos', { params });
      
      const items = response.data.items || [];
      const totalItems = response.data.total || 0;

      // Filtro por categoria e busca feitos no cliente (backend não suporta ainda)
      let filtered = items;
      if (searchTerm) {
        filtered = filtered.filter((p) =>
          p.nome.toLowerCase().includes(searchTerm.toLowerCase())
        );
      }
      if (categoriaFilter) {
        filtered = filtered.filter((p) => p.categoria_id === categoriaFilter);
      }

      setProdutos(filtered);
      setTotal(totalItems);
      setTotalPages(Math.ceil(totalItems / limit) || 1);
    } catch (error) {
      toast.error('Erro ao carregar produtos');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (value: string) => {
    setSearchTerm(value);
    setCurrentPage(1);
  };

  const handleCategoriaFilter = (categoriaId: string) => {
    setCategoriaFilter(categoriaId);
    setCurrentPage(1);
  };

  const handleStatusFilter = (status: 'todos' | 'excluidos') => {
    setStatusFilter(status);
    setCurrentPage(1);
  };

  const handleDelete = async (id: string, nome: string) => {
    if (!confirm(`Tem certeza que deseja excluir o produto "${nome}"?`)) {
      return;
    }

    try {
      await api.delete(`/produtos/${id}`);
      toast.success('Produto excluído com sucesso');
      carregarProdutos();
    } catch (error: any) {
      const message = error.response?.data?.detail || 'Erro ao excluir produto';
      toast.error(message);
      console.error(error);
    }
  };

  const handleRestore = async (id: string, nome: string) => {
    if (!confirm(`Tem certeza que deseja restaurar o produto "${nome}"?`)) {
      return;
    }

    try {
      await api.patch(`/produtos/${id}/restaurar`);
      toast.success('Produto restaurado com sucesso');
      carregarProdutos();
    } catch (error: any) {
      const message = error.response?.data?.detail || 'Erro ao restaurar produto';
      toast.error(message);
      console.error(error);
    }
  };

  const handleCopiarLink = () => {
    navigator.clipboard.writeText(catalogoUrl).then(() => {
      setLinkCopiado(true);
      toast.success('Link do catálogo copiado!');
      setTimeout(() => setLinkCopiado(false), 2000);
    });
  };

  return (
    <div className="produtos-page">
      <div className="page-header">
        <div className="header-content">
          <h1>Produtos</h1>
          <p>Gerencie o catálogo de produtos</p>
        </div>
        <div className="header-actions">
          <button
            className="btn btn-catalogo"
            onClick={handleCopiarLink}
            title={catalogoUrl}
          >
            {linkCopiado ? <FiCopy /> : <FiShare2 />}
            {linkCopiado ? 'Link copiado!' : 'Compartilhar Catálogo'}
          </button>
          <button className="btn btn-primary" onClick={() => navigate('/produtos/novo')}>
            <FiPlus /> Novo Produto
          </button>
        </div>
      </div>

      <div className="filters-section">
        <div className="search-box">
          <FiSearch className="search-icon" />
          <input
            type="text"
            placeholder="Buscar por nome..."
            value={searchTerm}
            onChange={(e) => handleSearch(e.target.value)}
          />
        </div>

        <div className="filter-buttons">
          <select
            className="filter-select"
            value={categoriaFilter}
            onChange={(e) => handleCategoriaFilter(e.target.value)}
          >
            <option value="">Todas as categorias</option>
            {categorias.map((cat) => (
              <option key={cat.id} value={cat.id}>
                {cat.nome}
              </option>
            ))}
          </select>

          <button
            className={`filter-btn ${statusFilter === 'todos' ? 'active' : ''}`}
            onClick={() => handleStatusFilter('todos')}
          >
            Todos
          </button>
          <button
            className={`filter-btn ${statusFilter === 'excluidos' ? 'active' : ''}`}
            onClick={() => handleStatusFilter('excluidos')}
          >
            Excluídos
          </button>
        </div>
      </div>

      {loading ? (
        <div className="loading">
          <div className="spinner-border text-primary" role="status">
            <span className="visually-hidden">Carregando...</span>
          </div>
        </div>
      ) : produtos.length === 0 ? (
        <div className="empty-state">
          <p>Nenhum produto encontrado</p>
        </div>
      ) : (
        <>
          <div className="table-responsive">
            <table className="produtos-table">
              <thead>
                <tr>
                  <th>Nome</th>
                  <th>Categoria</th>
                  <th>Descrição</th>
                  <th>Status</th>
                  <th>Ações</th>
                </tr>
              </thead>
              <tbody>
                {produtos.map((produto) => (
                  <tr key={produto.id}>
                    <td className="nome">{produto.nome}</td>
                    <td>{produto.categoria?.nome || '-'}</td>
                    <td className="descricao">
                      {produto.descricao ? (
                        <span title={produto.descricao}>
                          {produto.descricao.length > 50
                            ? `${produto.descricao.substring(0, 50)}...`
                            : produto.descricao}
                        </span>
                      ) : (
                        '-'
                      )}
                    </td>
                    <td>
                      <div className="status-badges">
                        {statusFilter === 'excluidos' ? (
                          <span className="badge badge-danger">Excluído</span>
                        ) : (
                          <span className={`badge ${produto.ativo ? 'badge-success' : 'badge-warning'}`}>
                            {produto.ativo ? 'Ativo' : 'Inativo'}
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="acoes">
                      {statusFilter === 'excluidos' ? (
                        <button
                          className="btn-icon btn-success"
                          onClick={() => handleRestore(produto.id, produto.nome)}
                          title="Restaurar"
                        >
                          <FiPlus />
                        </button>
                      ) : (
                        <>
                          <button
                            className="btn-icon btn-info"
                            onClick={() => navigate(`/produtos/${produto.id}`)}
                            title="Ver detalhes"
                          >
                            <FiEye />
                          </button>
                          <button
                            className="btn-icon btn-warning"
                            onClick={() => navigate(`/produtos/${produto.id}/editar`)}
                            title="Editar"
                          >
                            <FiEdit2 />
                          </button>
                          <button
                            className="btn-icon btn-danger"
                            onClick={() => handleDelete(produto.id, produto.nome)}
                            title="Excluir"
                          >
                            <FiTrash2 />
                          </button>
                        </>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="pagination">
            <button
              className="btn btn-outline-secondary"
              onClick={() => setCurrentPage((prev) => Math.max(1, prev - 1))}
              disabled={currentPage === 1}
            >
              Anterior
            </button>
            <span className="page-info">
              Página {currentPage} de {totalPages} ({total} produtos)
            </span>
            <button
              className="btn btn-outline-secondary"
              onClick={() => setCurrentPage((prev) => Math.min(totalPages, prev + 1))}
              disabled={currentPage === totalPages}
            >
              Próxima
            </button>
          </div>
        </>
      )}
    </div>
  );
};

export default ProdutosPage;
