import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { FiArrowLeft, FiEdit2, FiTrash2, FiPackage } from 'react-icons/fi';
import { toast } from 'react-toastify';
import { api } from '@/services/api/axios';
import './ProdutoDetalhesPage.scss';

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

const ProdutoDetalhesPage = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const [produto, setProduto] = useState<Produto | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (id) {
      carregarProduto();
    }
  }, [id]);

  const carregarProduto = async () => {
    try {
      setLoading(true);
      const response = await api.get(`/produtos/${id}`);
      setProduto(response.data);
    } catch (error) {
      toast.error('Erro ao carregar produto');
      console.error(error);
      navigate('/produtos');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!produto) return;

    if (!confirm(`Tem certeza que deseja desativar o produto "${produto.nome}"?`)) {
      return;
    }

    try {
      await api.delete(`/produtos/${id}`);
      toast.success('Produto desativado com sucesso');
      navigate('/produtos');
    } catch (error: any) {
      const message = error.response?.data?.detail || 'Erro ao desativar produto';
      toast.error(message);
      console.error(error);
    }
  };

  if (loading) {
    return (
      <div className="produto-detalhes-page">
        <div className="loading">
          <div className="spinner-border text-primary" role="status">
            <span className="visually-hidden">Carregando...</span>
          </div>
        </div>
      </div>
    );
  }

  if (!produto) {
    return (
      <div className="produto-detalhes-page">
        <div className="empty-state">
          <p>Produto não encontrado</p>
        </div>
      </div>
    );
  }

  return (
    <div className="produto-detalhes-page">
      <div className="page-header">
        <button className="btn-back" onClick={() => navigate('/produtos')}>
          <FiArrowLeft /> Voltar
        </button>
        <div className="header-actions">
          {produto.ativo && (
            <button className="btn btn-warning" onClick={() => navigate(`/produtos/${id}/editar`)}>
              <FiEdit2 /> Editar
            </button>
          )}
          {produto.ativo && (
            <button className="btn btn-danger" onClick={handleDelete}>
              <FiTrash2 /> Desativar
            </button>
          )}
        </div>
      </div>

      <div className="produto-header">
        <div className="produto-icon">
          <FiPackage />
        </div>
        <div className="produto-info">
          <h1>{produto.nome}</h1>
          <div className="status-badges">
            <span className={`badge ${produto.ativo ? 'badge-success' : 'badge-secondary'}`}>
              {produto.ativo ? 'Ativo' : 'Inativo'}
            </span>
          </div>
        </div>
      </div>

      <div className="produto-content">
        <div className="info-section">
          <h2>Informações Básicas</h2>
          <div className="info-grid">
            <div className="info-item">
              <span className="label">Nome:</span>
              <span className="value">{produto.nome}</span>
            </div>
            <div className="info-item">
              <span className="label">Categoria:</span>
              <span className="value">{produto.categoria?.nome || '-'}</span>
            </div>
            <div className="info-item full-width">
              <span className="label">Descrição:</span>
              <span className="value">{produto.descricao || '-'}</span>
            </div>
          </div>
        </div>

        <div className="info-section">
          <h2>Informações do Sistema</h2>
          <div className="info-grid">
            <div className="info-item">
              <span className="label">ID:</span>
              <span className="value mono">{produto.id}</span>
            </div>
            <div className="info-item">
              <span className="label">Criado em:</span>
              <span className="value">
                {new Date(produto.criado_em).toLocaleString('pt-BR')}
              </span>
            </div>
            {produto.atualizado_em && (
              <div className="info-item">
                <span className="label">Atualizado em:</span>
                <span className="value">
                  {new Date(produto.atualizado_em).toLocaleString('pt-BR')}
                </span>
              </div>
            )}
          </div>
        </div>

        <div className="info-section">
          <h2>Variantes</h2>
          <div className="empty-state-small">
            <p>Funcionalidade de variantes será implementada em breve</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProdutoDetalhesPage;
