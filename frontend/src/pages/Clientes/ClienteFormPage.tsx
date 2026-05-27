import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { FiArrowLeft, FiSave } from 'react-icons/fi';
import { toast } from 'react-toastify';
import { api } from '@/services/api/axios';
import './ClienteFormPage.scss';

// Schema de validação
const clienteSchema = z.object({
  nome: z.string().min(3, 'Nome deve ter no mínimo 3 caracteres'),
  cpf: z.string().regex(/^\d{11}$/, 'CPF deve ter 11 dígitos'),
  telefone: z.string().regex(/^\(\d{2}\)\s\d{4,5}-\d{4}$/, 'Telefone inválido'),
  email: z.string().email('Email inválido').optional().or(z.literal('')),
  data_nasc: z.string().optional().or(z.literal('')),
  limite_credito: z.number().min(0, 'Limite de crédito não pode ser negativo'),
  dia_vencimento: z.number().min(1).max(28, 'Dia deve estar entre 1 e 28').optional(),
});

type ClienteFormData = z.infer<typeof clienteSchema>;

interface Cliente extends ClienteFormData {
  id: string;
  ativo: boolean;
  bloqueado: boolean;
  credito_disponivel: number;
}

const ClienteFormPage = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const [loading, setLoading] = useState(!!id);
  const [submitting, setSubmitting] = useState(false);
  const [cliente, setCliente] = useState<Cliente | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
    watch,
  } = useForm<ClienteFormData>({
    resolver: zodResolver(clienteSchema),
  });

  const telefone = watch('telefone');

  useEffect(() => {
    if (id) {
      carregarCliente();
    }
  }, [id]);

  const carregarCliente = async () => {
    try {
      setLoading(true);
      const response = await api.get(`/clientes/${id}`);
      setCliente(response.data);
      reset(response.data);
    } catch (error) {
      toast.error('Erro ao carregar cliente');
      console.error(error);
      navigate('/clientes');
    } finally {
      setLoading(false);
    }
  };

  const onSubmit = async (data: ClienteFormData) => {
    try {
      setSubmitting(true);

      if (id) {
        // Editar
        await api.put(`/clientes/${id}`, data);
        toast.success('Cliente atualizado com sucesso');
      } else {
        // Criar
        await api.post('/clientes', data);
        toast.success('Cliente criado com sucesso');
      }

      navigate('/clientes');
    } catch (error: any) {
      const message = error.response?.data?.detail || 'Erro ao salvar cliente';
      toast.error(message);
      console.error(error);
    } finally {
      setSubmitting(false);
    }
  };

  const formatarTelefone = (value: string) => {
    const numbers = value.replace(/\D/g, '');
    if (numbers.length <= 2) return numbers;
    if (numbers.length <= 6) return `(${numbers.slice(0, 2)}) ${numbers.slice(2)}`;
    if (numbers.length <= 10)
      return `(${numbers.slice(0, 2)}) ${numbers.slice(2, 7)}-${numbers.slice(7)}`;
    return `(${numbers.slice(0, 2)}) ${numbers.slice(2, 7)}-${numbers.slice(7, 11)}`;
  };

  const formatarCPF = (value: string) => {
    return value.replace(/\D/g, '').slice(0, 11);
  };

  if (loading) {
    return (
      <div className="cliente-form-page">
        <div className="loading">
          <div className="spinner-border text-primary" role="status">
            <span className="visually-hidden">Carregando...</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="cliente-form-page">
      <div className="page-header">
        <button className="btn-back" onClick={() => navigate('/clientes')}>
          <FiArrowLeft /> Voltar
        </button>
        <h1>{id ? 'Editar Cliente' : 'Novo Cliente'}</h1>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="cliente-form">
        <div className="form-section">
          <h2>Informações Pessoais</h2>

          <div className="form-group">
            <label htmlFor="nome">Nome *</label>
            <input
              id="nome"
              type="text"
              placeholder="Nome completo"
              {...register('nome')}
              className={errors.nome ? 'is-invalid' : ''}
            />
            {errors.nome && <span className="error-message">{errors.nome.message}</span>}
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="cpf">CPF *</label>
              <input
                id="cpf"
                type="text"
                placeholder="00000000000"
                {...register('cpf', {
                  onChange: (e) => {
                    e.target.value = formatarCPF(e.target.value);
                  },
                })}
                className={errors.cpf ? 'is-invalid' : ''}
              />
              {errors.cpf && <span className="error-message">{errors.cpf.message}</span>}
            </div>

            <div className="form-group">
              <label htmlFor="telefone">Telefone *</label>
              <input
                id="telefone"
                type="text"
                placeholder="(00) 00000-0000"
                {...register('telefone', {
                  onChange: (e) => {
                    e.target.value = formatarTelefone(e.target.value);
                  },
                })}
                className={errors.telefone ? 'is-invalid' : ''}
              />
              {errors.telefone && <span className="error-message">{errors.telefone.message}</span>}
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="email">Email</label>
              <input
                id="email"
                type="email"
                placeholder="email@exemplo.com"
                {...register('email')}
                className={errors.email ? 'is-invalid' : ''}
              />
              {errors.email && <span className="error-message">{errors.email.message}</span>}
            </div>

            <div className="form-group">
              <label htmlFor="data_nasc">Data de Nascimento</label>
              <input
                id="data_nasc"
                type="date"
                {...register('data_nasc')}
                className={errors.data_nasc ? 'is-invalid' : ''}
              />
              {errors.data_nasc && <span className="error-message">{errors.data_nasc.message}</span>}
            </div>
          </div>
        </div>

        <div className="form-section">
          <h2>Informações de Crédito</h2>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="limite_credito">Limite de Crédito (R$) *</label>
              <input
                id="limite_credito"
                type="number"
                step="0.01"
                placeholder="0.00"
                {...register('limite_credito', { valueAsNumber: true })}
                className={errors.limite_credito ? 'is-invalid' : ''}
              />
              {errors.limite_credito && (
                <span className="error-message">{errors.limite_credito.message}</span>
              )}
            </div>

            <div className="form-group">
              <label htmlFor="dia_vencimento">Dia de Vencimento</label>
              <input
                id="dia_vencimento"
                type="number"
                min="1"
                max="28"
                placeholder="1-28"
                {...register('dia_vencimento', { valueAsNumber: true })}
                className={errors.dia_vencimento ? 'is-invalid' : ''}
              />
              {errors.dia_vencimento && (
                <span className="error-message">{errors.dia_vencimento.message}</span>
              )}
            </div>
          </div>

          {cliente && (
            <div className="info-box">
              <div className="info-item">
                <span className="label">Crédito Disponível:</span>
                <span className="value">
                  R$ {cliente.credito_disponivel.toFixed(2).replace('.', ',')}
                </span>
              </div>
              <div className="info-item">
                <span className="label">Status:</span>
                <span className={`value ${cliente.bloqueado ? 'bloqueado' : 'ativo'}`}>
                  {cliente.bloqueado ? 'Bloqueado' : 'Ativo'}
                </span>
              </div>
            </div>
          )}
        </div>

        <div className="form-actions">
          <button
            type="button"
            className="btn btn-outline-secondary"
            onClick={() => navigate('/clientes')}
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

export default ClienteFormPage;
