import { useState, useEffect } from 'react';
import { FiPlus, FiEdit2, FiTrash2, FiFolder } from 'react-icons/fi';
import { toast } from 'react-toastify';
import { api } from '@/services/api/axios';
import './CategoriasPage.scss';

interface Categoria {
  id: string;
  nome: string;
  descricao?: string;
  ativo: boolean;
  criado_em: string;
}

const CategoriasPage = () => {
  const [categorias, setCategorias] = useState<Categoria[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingCategoria, setEditingCategoria] = useState<Categoria | null>(null);

  // Form state
  const [formData, setFormData] = useState({
    nome: '',
    descricao: '',
  });

  useEffect(() => {
    carregarCategorias();
  }, []);

  const carregarCategorias = async () => {
    try {
      setLoading(true);
      const response = await api.get('/categorias?limit=100');
      setCategorias(response.data.items || []);
    } catch (error) {
      toast.error('Erro ao carregar categorias');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    try {
      if (editingCategoria) {
        await api.put(`/categorias/${editingCategoria.id}`, formData);
        toast.success('Categoria atualizada com sucesso');
      } else {
        await api.post('/categorias', formData);
        toast.success('Categoria criada com sucesso');
      }

      setShowForm(false);
      setEditingCategoria(null);
      setFormData({ nome: '', descricao: '' });
      carregarCategorias();
    } catch (error: any) {
      const message = error.response?.data?.detail || 'Erro ao salvar categoria';
      toast.error(message);
      console.error(error);
    }
  };

  const handleEdit = (categoria: Categoria) => {
    setEditingCategoria(categoria);
    setFormData({
      nome: categoria.nome,
      descricao: categoria.descricao || '',
    });
    setShowForm(true);
  };

  const handleDelete = async (id: string, nome: string) => {
    if (!confirm(`Tem certeza que deseja excluir a categoria "${nome}"?`)) {
      return;
    }

    try {
      await api.delete(`/categorias/${id}`);
      toast.success('Categoria excluída com sucesso');
      carregarCategorias();
    } catch (error: any) {
      const message = error.response?.data?.detail || 'Erro ao excluir categoria';
      toast.error(message);
      console.error(error);
    }
  };

  const handleCancel = () => {
    setShowForm(false);
    setEditingCategoria(null);
    setFormData({ nome: '', descricao: '' });
  };

  if (loading) {
    return (
      <div className="categorias-page">
        <div className="loading">
          <div className="spinner-border text-primary" role="status">
            <span className="visually-hidden">Carregando...</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="categorias-page">
      <div className="page-header">
        <div className="header-content">
          <h1>Categorias</h1>
          <p>Gerencie as categorias de produtos</p>
        </div>
        <button className="btn btn-primary" onClick={() => setShowForm(true)}>
          <FiPlus /> Nova Categoria
        </button>
      </div>

      {showForm && (
        <div className="form-section">
          <h2>{editingCategoria ? 'Editar Categoria' : 'Nova Categoria'}</h2>
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label htmlFor="nome">Nome *</label>
              <input
                id="nome"
                type="text"
                placeholder="Nome da categoria"
                value={formData.nome}
                onChange={(e) => setFormData({ ...formData, nome: e.target.value })}
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="descricao">Descrição</label>
              <textarea
                id="descricao"
                placeholder="Descrição da categoria"
                rows={3}
                value={formData.descricao}
                onChange={(e) => setFormData({ ...formData, descricao: e.target.value })}
              />
            </div>

            <div className="form-actions">
              <button type="button" className="btn btn-outline-secondary" onClick={handleCancel}>
                Cancelar
              </button>
              <button type="submit" className="btn btn-primary">
                {editingCategoria ? 'Atualizar' : 'Criar'}
              </button>
            </div>
          </form>
        </div>
      )}

      {categorias.length === 0 ? (
        <div className="empty-state">
          <p>Nenhuma categoria cadastrada</p>
        </div>
      ) : (
        <div className="categorias-grid">
          {categorias.map((categoria) => (
            <div key={categoria.id} className="categoria-card">
              <div className="card-icon">
                <FiFolder />
              </div>
              <div className="card-content">
                <h3>{categoria.nome}</h3>
                {categoria.descricao && <p>{categoria.descricao}</p>}
                <div className="card-footer">
                  <span className={`badge ${categoria.ativo ? 'badge-success' : 'badge-secondary'}`}>
                    {categoria.ativo ? 'Ativo' : 'Inativo'}
                  </span>
                  <div className="card-actions">
                    <button
                      className="btn-icon btn-warning"
                      onClick={() => handleEdit(categoria)}
                      title="Editar"
                    >
                      <FiEdit2 />
                    </button>
                    <button
                      className="btn-icon btn-danger"
                      onClick={() => handleDelete(categoria.id, categoria.nome)}
                      title="Excluir"
                    >
                      <FiTrash2 />
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default CategoriasPage;
