import { useState, useEffect } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { FiPlus, FiEdit2, FiTrash2, FiTag } from 'react-icons/fi';
import { toast } from 'react-toastify';
import { api, getErrorMessage } from '@/services/api/axios';
import { useAuth } from '@/hooks/useAuth';
import './CategoriasPage.scss';

interface Categoria {
  id: string;
  nome: string;
  descricao?: string;
  cor?: string;
  ativo: boolean;
  criado_em: string;
}

const CategoriasPage = () => {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [categorias, setCategorias] = useState<Categoria[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingCategoria, setEditingCategoria] = useState<Categoria | null>(null);

  // Form state
  const [formData, setFormData] = useState({
    nome: '',
    descricao: '',
    cor: '#3B82F6',
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
      const payloadDescricao = formData.cor 
        ? `${formData.descricao}::color::${formData.cor}`
        : formData.descricao;

      const payload = { ...formData, descricao: payloadDescricao };
      delete payload.cor;

      if (editingCategoria) {
        await api.put(`/categorias/${editingCategoria.id}`, payload);
        toast.success('Categoria atualizada com sucesso');
      } else {
        await api.post('/categorias', { ...payload, empresa_id: user!.empresa_id });
        toast.success('Categoria criada com sucesso');
      }

      setShowForm(false);
      setEditingCategoria(null);
      setFormData({ nome: '', descricao: '', cor: '#3B82F6' });
      await queryClient.invalidateQueries({ queryKey: ['categorias'] });
      carregarCategorias();
    } catch (error) {
      const message = getErrorMessage(error, 'Erro ao salvar categoria');
      toast.error(message);
      console.error(error);
    }
  };

  const handleEdit = (categoria: Categoria) => {
    let desc = categoria.descricao || '';
    let color = categoria.cor || '#3B82F6';
    if (desc.includes('::color::')) {
      const parts = desc.split('::color::');
      desc = parts[0];
      color = parts[1];
    }
    setEditingCategoria(categoria);
    setFormData({
      nome: categoria.nome,
      descricao: desc,
      cor: color,
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
      await queryClient.invalidateQueries({ queryKey: ['categorias'] });
      carregarCategorias();
    } catch (error) {
      const message = getErrorMessage(error, 'Erro ao excluir categoria');
      toast.error(message);
      console.error(error);
    }
  };

  const handleCancel = () => {
    setShowForm(false);
    setEditingCategoria(null);
    setFormData({ nome: '', descricao: '', cor: '#3B82F6' });
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
          <h1><FiTag className="title-icon" /> Categorias</h1>
          <p>{categorias.length} {categorias.length === 1 ? 'categoria' : 'categorias'}</p>
        </div>
        <button className="btn btn-primary" onClick={() => setShowForm(true)}>
          <FiPlus /> Nova Categoria
        </button>
      </div>

      {showForm && (
        <div className="modal-overlay">
          <div className="modal-content">
            <h2>{editingCategoria ? 'Editar Categoria' : 'Nova Categoria'}</h2>
            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label htmlFor="nome">Nome *</label>
                <input
                  id="nome"
                  type="text"
                  value={formData.nome}
                  onChange={(e) => setFormData({ ...formData, nome: e.target.value })}
                  required
                />
              </div>

              <div className="form-group">
                <label htmlFor="cor">Cor</label>
                <div className="color-input-wrapper">
                  <input
                    id="cor-picker"
                    type="color"
                    value={formData.cor}
                    onChange={(e) => setFormData({ ...formData, cor: e.target.value })}
                  />
                  <input
                    id="cor"
                    type="text"
                    value={formData.cor.toUpperCase()}
                    onChange={(e) => setFormData({ ...formData, cor: e.target.value })}
                    maxLength={7}
                  />
                </div>
              </div>

              <div className="form-group">
                <label htmlFor="descricao">Descrição</label>
                <input
                  id="descricao"
                  type="text"
                  value={formData.descricao}
                  onChange={(e) => setFormData({ ...formData, descricao: e.target.value })}
                />
              </div>

              <div className="form-actions">
                <button type="button" className="btn-cancel" onClick={handleCancel}>
                  Cancelar
                </button>
                <button type="submit" className="btn-save">
                  Salvar
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {categorias.length === 0 ? (
        <div className="empty-state">
          <p>Nenhuma categoria cadastrada</p>
        </div>
      ) : (
        <div className="categorias-grid">
          {categorias.map((categoria) => {
            let desc = categoria.descricao || '';
            let color = categoria.cor || '#3B82F6';
            if (desc.includes('::color::')) {
              const parts = desc.split('::color::');
              desc = parts[0];
              color = parts[1];
            }
            
            return (
              <div key={categoria.id} className="categoria-card">
                <div 
                  className="card-avatar" 
                  style={{ backgroundColor: color }}
                >
                  {categoria.nome.charAt(0).toUpperCase()}
                </div>
                <div className="card-content">
                  <h3>{categoria.nome}</h3>
                  <p>{desc || 'Sem descrição'}</p>
                </div>
                <div className="card-actions">
                  <button
                    className="btn-icon"
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
            );
          })}
        </div>
      )}
    </div>
  );
};

export default CategoriasPage;
