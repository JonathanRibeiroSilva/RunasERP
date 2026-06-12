import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { FiArrowLeft, FiPlus, FiEdit2, FiTrash2, FiDollarSign } from 'react-icons/fi';
import { toast } from 'react-toastify';
import { api } from '@/services/api/axios';
import './ProdutoVariantesPage.scss';

interface Variante {
  id: string;
  produto_id: string;
  sku: string;
  preco_custo: number;
  markup_pct: number;
  preco_venda: number;
  ativo: boolean;
  criado_em: string;
}

interface Produto {
  id: string;
  nome: string;
}

const ProdutoVariantesPage = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const [produto, setProduto] = useState<Produto | null>(null);
  const [variantes, setVariantes] = useState<Variante[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingVariante, setEditingVariante] = useState<Variante | null>(null);

  // Form state
  const [formData, setFormData] = useState({
    sku: '',
    preco_custo: '',
    markup_pct: '',
  });

  useEffect(() => {
    if (id) {
      carregarProduto();
      carregarVariantes();
    }
  }, [id]);

  const carregarProduto = async () => {
    try {
      const response = await api.get(`/produtos/${id}`);
      setProduto(response.data);
    } catch (error) {
      toast.error('Erro ao carregar produto');
      console.error(error);
      navigate('/produtos');
    }
  };

  const carregarVariantes = async () => {
    try {
      setLoading(true);
      const response = await api.get(`/variantes/produto/${id}`);
      setVariantes(response.data || []);
    } catch (error) {
      toast.error('Erro ao carregar variantes');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    const data = {
      produto_id: id,
      empresa_id: 1, // Empresa padrão (virá do contexto de auth futuramente)
      sku: formData.sku,
      preco_custo: parseFloat(formData.preco_custo),
      markup_pct: parseFloat(formData.markup_pct),
      preco_venda: parseFloat(formData.preco_custo) * (1 + parseFloat(formData.markup_pct) / 100),
    };

    try {
      if (editingVariante) {
        await api.put(`/variantes/${editingVariante.id}`, {
          sku: formData.sku,
          preco_custo: parseFloat(formData.preco_custo),
          markup_pct: parseFloat(formData.markup_pct),
          preco_venda: parseFloat(formData.preco_custo) * (1 + parseFloat(formData.markup_pct) / 100),
        });
        toast.success('Variante atualizada com sucesso');
      } else {
        await api.post(`/variantes`, data);
        toast.success('Variante criada com sucesso');
      }

      setShowForm(false);
      setEditingVariante(null);
      setFormData({ sku: '', preco_custo: '', markup_pct: '' });
      carregarVariantes();
    } catch (error: any) {
      const message = error.response?.data?.detail || 'Erro ao salvar variante';
      toast.error(message);
      console.error(error);
    }
  };

  const handleEdit = (variante: Variante) => {
    setEditingVariante(variante);
    setFormData({
      sku: variante.sku,
      preco_custo: variante.preco_custo.toString(),
      markup_pct: variante.markup_pct.toString(),
    });
    setShowForm(true);
  };

  const handleDelete = async (varianteId: string, sku: string) => {
    if (!confirm(`Tem certeza que deseja excluir a variante "${sku}"?`)) {
      return;
    }

    try {
      await api.delete(`/variantes/${varianteId}`);
      toast.success('Variante excluída com sucesso');
      carregarVariantes();
    } catch (error: any) {
      const message = error.response?.data?.detail || 'Erro ao excluir variante';
      toast.error(message);
      console.error(error);
    }
  };

  const handleCancel = () => {
    setShowForm(false);
    setEditingVariante(null);
    setFormData({ sku: '', preco_custo: '', markup_pct: '' });
  };

  const calcularPrecoVenda = () => {
    const custo = parseFloat(formData.preco_custo) || 0;
    const markup = parseFloat(formData.markup_pct) || 0;
    return custo * (1 + markup / 100);
  };

  const formatarMoeda = (valor: number) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL',
    }).format(valor);
  };

  if (loading) {
    return (
      <div className="produto-variantes-page">
        <div className="loading">
          <div className="spinner-border text-primary" role="status">
            <span className="visually-hidden">Carregando...</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="produto-variantes-page">
      <div className="page-header">
        <button className="btn-back" onClick={() => navigate(`/produtos/${id}`)}>
          <FiArrowLeft /> Voltar
        </button>
        <h1>Variantes - {produto?.nome}</h1>
      </div>

      <div className="actions-bar">
        <button className="btn btn-primary" onClick={() => setShowForm(true)}>
          <FiPlus /> Nova Variante
        </button>
      </div>

      {showForm && (
        <div className="form-section">
          <h2>{editingVariante ? 'Editar Variante' : 'Nova Variante'}</h2>
          <form onSubmit={handleSubmit}>
            <div className="form-row">
              <div className="form-group">
                <label htmlFor="sku">SKU *</label>
                <input
                  id="sku"
                  type="text"
                  placeholder="SKU único"
                  value={formData.sku}
                  onChange={(e) => setFormData({ ...formData, sku: e.target.value })}
                  required
                />
              </div>

              <div className="form-group">
                <label htmlFor="preco_custo">Preço de Custo (R$) *</label>
                <input
                  id="preco_custo"
                  type="number"
                  step="0.01"
                  min="0"
                  placeholder="0.00"
                  value={formData.preco_custo}
                  onChange={(e) => setFormData({ ...formData, preco_custo: e.target.value })}
                  required
                />
              </div>

              <div className="form-group">
                <label htmlFor="markup_pct">Markup (%) *</label>
                <input
                  id="markup_pct"
                  type="number"
                  step="0.01"
                  min="0"
                  placeholder="0.00"
                  value={formData.markup_pct}
                  onChange={(e) => setFormData({ ...formData, markup_pct: e.target.value })}
                  required
                />
              </div>

              <div className="form-group">
                <label>Preço de Venda (calculado)</label>
                <div className="calculated-price">
                  <FiDollarSign />
                  {formatarMoeda(calcularPrecoVenda())}
                </div>
              </div>
            </div>

            <div className="form-actions">
              <button type="button" className="btn btn-outline-secondary" onClick={handleCancel}>
                Cancelar
              </button>
              <button type="submit" className="btn btn-primary">
                {editingVariante ? 'Atualizar' : 'Criar'}
              </button>
            </div>
          </form>
        </div>
      )}

      {variantes.length === 0 ? (
        <div className="empty-state">
          <p>Nenhuma variante cadastrada</p>
        </div>
      ) : (
        <div className="table-responsive">
          <table className="variantes-table">
            <thead>
              <tr>
                <th>SKU</th>
                <th>Preço de Custo</th>
                <th>Markup</th>
                <th>Preço de Venda</th>
                <th>Status</th>
                <th>Ações</th>
              </tr>
            </thead>
            <tbody>
              {variantes.map((variante) => (
                <tr key={variante.id} className={!variante.ativo ? 'inactive' : ''}>
                  <td className="sku">{variante.sku}</td>
                  <td className="moeda">{formatarMoeda(variante.preco_custo)}</td>
                  <td>{variante.markup_pct.toFixed(2)}%</td>
                  <td className="moeda destaque">{formatarMoeda(variante.preco_venda)}</td>
                  <td>
                    <span className={`badge ${variante.ativo ? 'badge-success' : 'badge-secondary'}`}>
                      {variante.ativo ? 'Ativo' : 'Inativo'}
                    </span>
                  </td>
                  <td className="acoes">
                    <button
                      className="btn-icon btn-warning"
                      onClick={() => handleEdit(variante)}
                      title="Editar"
                    >
                      <FiEdit2 />
                    </button>
                    <button
                      className="btn-icon btn-danger"
                      onClick={() => handleDelete(variante.id, variante.sku)}
                      title="Excluir"
                    >
                      <FiTrash2 />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default ProdutoVariantesPage;
