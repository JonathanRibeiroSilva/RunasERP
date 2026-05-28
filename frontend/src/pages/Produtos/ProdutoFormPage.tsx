import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { FiArrowLeft, FiSave } from 'react-icons/fi';
import { toast } from 'react-toastify';
import { api } from '@/services/api/axios';
import './ProdutoFormPage.scss';

// Schema de validação
const produtoSchema = z.object({
  nome: z.string().min(3, 'Nome deve ter no mínimo 3 caracteres'),
  categoria_id: z.string().uuid('Categoria inválida'),
  descricao: z.string().optional().or(z.literal('')),
});

type ProdutoFormData = z.infer<typeof produtoSchema>;

interface Categoria {
  id: string;
  nome: string;
}

interface Produto extends ProdutoFormData {
  id: string;
  ativo: boolean;
  criado_em: string;
}

const ProdutoFormPage = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const [loading, setLoading] = useState(!!id);
  const [submitting, setSubmitting] = useState(false);
  const [produto, setProduto] = useState<Produto | null>(null);
  const [categorias, setCategorias] = useState<Categoria[]>([]);

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<ProdutoFormData>({
    resolver: zodResolver(produtoSchema),
  });

  useEffect(() => {
    carregarCategorias();
    if (id) {
      carregarProduto();
    }
  }, [id]);

  const carregarCategorias = async () => {
    try {
      const response = await api.get('/categorias?limit=100');
      setCategorias(response.data.items || []);
    } catch (error) {
      toast.error('Erro ao carregar categorias');
      console.error(error);
    }
  };

  const carregarProduto = async () => {
    try {
      setLoading(true);
      const response = await api.get(`/produtos/${id}`);
      setProduto(response.data);
      reset(response.data);
    } catch (error) {
      toast.error('Erro ao carregar produto');
      console.error(error);
      navigate('/produtos');
    } finally {
      setLoading(false);
    }
  };

  const onSubmit = async (data: ProdutoFormData) => {
    try {
      setSubmitting(true);

      if (id) {
        // Editar
        await api.put(`/produtos/${id}`, data);
        toast.success('Produto atualizado com sucesso');
      } else {
        // Criar
        await api.post('/produtos', data);
        toast.success('Produto criado com sucesso');
      }

      navigate('/produtos');
    } catch (error: any) {
      const message = error.response?.data?.detail || 'Erro ao salvar produto';
      toast.error(message);
      console.error(error);
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="produto-form-page">
        <div className="loading">
          <div className="spinner-border text-primary" role="status">
            <span className="visually-hidden">Carregando...</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="produto-form-page">
      <div className="page-header">
        <button className="btn-back" onClick={() => navigate('/produtos')}>
          <FiArrowLeft /> Voltar
        </button>
        <h1>{id ? 'Editar Produto' : 'Novo Produto'}</h1>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="produto-form">
        <div className="form-section">
          <h2>Informações do Produto</h2>

          <div className="form-group">
            <label htmlFor="nome">Nome *</label>
            <input
              id="nome"
              type="text"
              placeholder="Nome do produto"
              {...register('nome')}
              className={errors.nome ? 'is-invalid' : ''}
            />
            {errors.nome && <span className="error-message">{errors.nome.message}</span>}
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="categoria_id">Categoria *</label>
              <select
                id="categoria_id"
                {...register('categoria_id')}
                className={errors.categoria_id ? 'is-invalid' : ''}
              >
                <option value="">Selecione uma categoria</option>
                {categorias.map((cat) => (
                  <option key={cat.id} value={cat.id}>
                    {cat.nome}
                  </option>
                ))}
              </select>
              {errors.categoria_id && (
                <span className="error-message">{errors.categoria_id.message}</span>
              )}
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="descricao">Descrição</label>
            <textarea
              id="descricao"
              placeholder="Descrição do produto"
              rows={4}
              {...register('descricao')}
              className={errors.descricao ? 'is-invalid' : ''}
            />
            {errors.descricao && <span className="error-message">{errors.descricao.message}</span>}
          </div>
        </div>

        {produto && (
          <div className="form-section">
            <h2>Informações Adicionais</h2>
            <div className="info-box">
              <div className="info-item">
                <span className="label">Status:</span>
                <span className={`value ${produto.ativo ? 'ativo' : 'inativo'}`}>
                  {produto.ativo ? 'Ativo' : 'Inativo'}
                </span>
              </div>
              <div className="info-item">
                <span className="label">Criado em:</span>
                <span className="value">{new Date(produto.criado_em).toLocaleDateString('pt-BR')}</span>
              </div>
            </div>
          </div>
        )}

        <div className="form-actions">
          <button
            type="button"
            className="btn btn-outline-secondary"
            onClick={() => navigate('/produtos')}
          >
            Cancelar
          </button>
          <button type="submit" className="btn btn-primary" disabled={submitting}>
            <FiSave /> {submitting ? 'Salvando...' : 'Salvar'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default ProdutoFormPage;
