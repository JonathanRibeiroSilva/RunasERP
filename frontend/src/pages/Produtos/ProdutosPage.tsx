import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { FiPlus, FiSearch, FiEdit2, FiEye, FiTrash2, FiPackage } from 'react-icons/fi';
import { toast } from 'react-toastify';
import { getErrorMessage } from '@/services/api/axios';
import { useAuth } from '@/hooks/useAuth';
import {
  useProdutos,
  useCategorias,
  useExcluirProduto,
  useRestaurarProduto,
} from '@/hooks/useProdutos';
import ProdutoFormPage from './ProdutoFormPage';
import './ProdutosPage.scss';

const ProdutosPage = () => {
  const navigate = useNavigate();
  const { user } = useAuth();

  const [searchTerm, setSearchTerm] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [categoriaFilter, setCategoriaFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState<'todos' | 'excluidos'>('todos');
  const [currentPage, setCurrentPage] = useState(1);
  const limit = 10;

  // Modal State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedProdutoId, setSelectedProdutoId] = useState<string | null>(null);



  // Debounce da busca (300ms) — evita refetch a cada tecla
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(searchTerm);
      setCurrentPage(1);
    }, 300);
    return () => clearTimeout(timer);
  }, [searchTerm]);

  const { data: produtosData, isLoading, isError } = useProdutos({
    skip: (currentPage - 1) * limit,
    limit,
    apenas_deletados: statusFilter === 'excluidos',
    busca: debouncedSearch || undefined,
    categoria_id: categoriaFilter || undefined,
  });
  const { data: categoriasData } = useCategorias();
  const excluirProduto = useExcluirProduto();
  const restaurarProduto = useRestaurarProduto();

  const produtos = produtosData?.items ?? [];
  const total = produtosData?.total ?? 0;
  const totalPages = Math.max(1, Math.ceil(total / limit));
  const categorias = categoriasData?.items ?? [];

  useEffect(() => {
    if (isError) {
      toast.error('Erro ao carregar produtos');
    }
  }, [isError]);

  const handleSearch = (value: string) => {
    setSearchTerm(value);
    // Reset de página tratado no debounce de busca
  };

  const handleCategoriaFilter = (categoriaId: string) => {
    setCategoriaFilter(categoriaId);
    setCurrentPage(1);
  };

  const handleStatusFilter = (status: 'todos' | 'excluidos') => {
    setStatusFilter(status);
    setCurrentPage(1);
  };

  const handleDelete = (id: string, nome: string) => {
    if (!confirm(`Tem certeza que deseja excluir o produto "${nome}"?`)) {
      return;
    }
    excluirProduto.mutate(id, {
      onSuccess: () => toast.success('Produto excluído com sucesso'),
      onError: (error) => toast.error(getErrorMessage(error)),
    });
  };

  const handleRestore = (id: string, nome: string) => {
    if (!confirm(`Tem certeza que deseja restaurar o produto "${nome}"?`)) {
      return;
    }
    restaurarProduto.mutate(id, {
      onSuccess: () => toast.success('Produto restaurado com sucesso'),
      onError: (error) => toast.error(getErrorMessage(error)),
    });
  };

  const handleNovoProduto = () => {
    setSelectedProdutoId(null);
    setIsModalOpen(true);
  };

  const handleEditarProduto = (id: string) => {
    setSelectedProdutoId(id);
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setSelectedProdutoId(null);
  };

  return (
    <div className="produtos-page">
      <div className="page-header">
        <div className="header-content">
          <h1><FiPackage className="title-icon" /> Produtos</h1>
          <p>Gerencie o catálogo de produtos</p>
        </div>
        <div className="header-actions">

          <button className="btn btn-primary" onClick={handleNovoProduto}>
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

      {isLoading ? (
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
                    <td data-label="Nome" className="nome">{produto.nome}</td>
                    <td data-label="Categoria">{produto.categoria?.nome || categorias.find(c => c.id === produto.categoria_id)?.nome || '-'}</td>
                    <td data-label="Descrição" className="descricao">
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
                    <td data-label="Status">
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
                    <td data-label="Ações" className="acoes">
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
                            onClick={() => handleEditarProduto(produto.id)}
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
      {/* MODAL PRODUTO FORM */}
      {isModalOpen && (
        <ProdutoFormPage
          isModal={true}
          produtoId={selectedProdutoId}
          onClose={handleCloseModal}
        />
      )}
    </div>
  );
};

export default ProdutosPage;
