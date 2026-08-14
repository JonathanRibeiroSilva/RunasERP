import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { FiArrowLeft, FiSave, FiLock, FiUnlock, FiDollarSign, FiAlertCircle } from 'react-icons/fi';
import { toast } from 'react-toastify';
import { clientesApi } from '@/services/api/clientesApi';
import { getErrorMessage } from '@/services/api/axios';
import './ClienteCreditoPage.scss';

// Schema de validação
const creditoSchema = z.object({
  limite_credito: z.number().min(0, 'Limite de crédito não pode ser negativo'),
  // Campo numérico vazio vira NaN (valueAsNumber) — tratar como "não informado"
  dia_vencimento: z.preprocess(
    (v) => (typeof v === 'number' && Number.isNaN(v) ? undefined : v),
    z.number().min(1, 'Dia deve estar entre 1 e 28').max(28, 'Dia deve estar entre 1 e 28').optional()
  ),
});

// zod 4 splits input from output: preprocess takes unknown in, gives number out.
// useForm needs both, otherwise the resolver type no longer matches.
type CreditoFormInput = z.input<typeof creditoSchema>;
type CreditoFormData = z.output<typeof creditoSchema>;

interface Cliente {
  id: string;
  nome: string;
  cpf: string;
  limite_credito: number;
  credito_disponivel: number;
  bloqueado: boolean;
  dia_vencimento?: number;
}

interface HistoricoCredito {
  id: string;
  data: string;
  tipo: 'AJUSTE_LIMITE' | 'BLOQUEIO' | 'DESBLOQUEIO' | 'VENDA' | 'PAGAMENTO';
  descricao: string;
  valor_anterior?: number;
  valor_novo?: number;
  usuario: string;
}

const ClienteCreditoPage = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const [cliente, setCliente] = useState<Cliente | null>(null);
  const [historico, setHistorico] = useState<HistoricoCredito[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [alterandoBloqueio, setAlterandoBloqueio] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<CreditoFormInput, unknown, CreditoFormData>({
    resolver: zodResolver(creditoSchema),
  });

  useEffect(() => {
    if (id) {
      carregarDados();
    }
  }, [id]);

  const carregarDados = async () => {
    try {
      setLoading(true);
      const [clienteData, historicoData] = await Promise.all([
        clientesApi.obter(id!),
        clientesApi.obterHistoricoCredito(id!).catch(() => []),
      ]);
      setCliente(clienteData);
      setHistorico(historicoData);
      reset({
        limite_credito: clienteData.limite_credito,
        dia_vencimento: clienteData.dia_vencimento,
      });
    } catch (error) {
      toast.error('Erro ao carregar dados');
      console.error(error);
      navigate('/clientes');
    } finally {
      setLoading(false);
    }
  };

  const onSubmit = async (data: CreditoFormData) => {
    try {
      setSubmitting(true);
      await clientesApi.atualizarCredito(id!, {
        limite_credito: data.limite_credito,
        dia_vencimento: data.dia_vencimento ?? null,
      });
      toast.success('Crédito atualizado com sucesso');
      carregarDados();
    } catch (error) {
      const message = getErrorMessage(error, 'Erro ao atualizar crédito');
      toast.error(message);
      console.error(error);
    } finally {
      setSubmitting(false);
    }
  };

  const handleToggleBloqueio = async () => {
    if (!cliente) return;

    const acao = cliente.bloqueado ? 'desbloquear' : 'bloquear';
    if (!window.confirm(`Tem certeza que deseja ${acao} este cliente?`)) {
      return;
    }

    try {
      setAlterandoBloqueio(true);
      await clientesApi.executarAcao(id!, acao);
      toast.success(`Cliente ${cliente.bloqueado ? 'desbloqueado' : 'bloqueado'} com sucesso`);
      carregarDados();
    } catch (error) {
      const message = getErrorMessage(error, 'Erro ao alterar bloqueio');
      toast.error(message);
      console.error(error);
    } finally {
      setAlterandoBloqueio(false);
    }
  };

  const formatarMoeda = (valor: number) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL',
    }).format(valor);
  };

  const formatarData = (data: string) => {
    return new Date(data).toLocaleString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getTipoLabel = (tipo: string) => {
    const labels: Record<string, string> = {
      AJUSTE_LIMITE: 'Ajuste de Limite',
      BLOQUEIO: 'Bloqueio',
      DESBLOQUEIO: 'Desbloqueio',
      VENDA: 'Venda',
      PAGAMENTO: 'Pagamento',
    };
    return labels[tipo] || tipo;
  };

  const getTipoClass = (tipo: string) => {
    const classes: Record<string, string> = {
      AJUSTE_LIMITE: 'info',
      BLOQUEIO: 'danger',
      DESBLOQUEIO: 'success',
      VENDA: 'warning',
      PAGAMENTO: 'success',
    };
    return classes[tipo] || 'secondary';
  };

  if (loading) {
    return (
      <div className="cliente-credito-page">
        <div className="loading">
          <div className="spinner-border text-primary" role="status">
            <span className="visually-hidden">Carregando...</span>
          </div>
        </div>
      </div>
    );
  }

  if (!cliente) {
    return null;
  }

  const saldoDevedor = cliente.limite_credito - cliente.credito_disponivel;
  const percentualUtilizado = cliente.limite_credito > 0
    ? (saldoDevedor / cliente.limite_credito) * 100
    : 0;

  return (
    <div className="cliente-credito-page">
      <div className="page-header">
        <button className="btn-back" onClick={() => navigate('/clientes')}>
          <FiArrowLeft /> Voltar
        </button>
        <div className="header-content">
          <h1>Gestão de Crédito - {cliente.nome}</h1>
          <p className="subtitle">CPF: {cliente.cpf}</p>
        </div>
      </div>

      <div className="credito-overview">
        <div className="credito-card">
          <div className="card-icon limite">
            <FiDollarSign />
          </div>
          <div className="card-content">
            <span className="card-label">Limite de Crédito</span>
            <span className="card-value">{formatarMoeda(cliente.limite_credito)}</span>
          </div>
        </div>

        <div className="credito-card">
          <div className="card-icon disponivel">
            <FiDollarSign />
          </div>
          <div className="card-content">
            <span className="card-label">Crédito Disponível</span>
            <span className={`card-value ${cliente.credito_disponivel < 0 ? 'negativo' : ''}`}>
              {formatarMoeda(cliente.credito_disponivel)}
            </span>
          </div>
        </div>

        <div className="credito-card">
          <div className="card-icon devedor">
            <FiAlertCircle />
          </div>
          <div className="card-content">
            <span className="card-label">Saldo Devedor</span>
            <span className={`card-value ${saldoDevedor > 0 ? 'negativo' : ''}`}>
              {formatarMoeda(saldoDevedor)}
            </span>
          </div>
        </div>

        <div className="credito-card">
          <div className={`card-icon status ${cliente.bloqueado ? 'bloqueado' : 'ativo'}`}>
            {cliente.bloqueado ? <FiLock /> : <FiUnlock />}
          </div>
          <div className="card-content">
            <span className="card-label">Status</span>
            <span className={`card-value ${cliente.bloqueado ? 'bloqueado' : 'ativo'}`}>
              {cliente.bloqueado ? 'Bloqueado' : 'Ativo'}
            </span>
          </div>
        </div>
      </div>

      {cliente.limite_credito > 0 && (
        <div className="utilizacao-credito">
          <div className="utilizacao-header">
            <span className="utilizacao-label">Utilização do Crédito</span>
            <span className="utilizacao-percentual">{percentualUtilizado.toFixed(1)}%</span>
          </div>
          <div className="utilizacao-bar">
            <div
              className={`utilizacao-fill ${percentualUtilizado > 90 ? 'danger' : percentualUtilizado > 70 ? 'warning' : 'success'}`}
              style={{ width: `${Math.min(percentualUtilizado, 100)}%` }}
            />
          </div>
        </div>
      )}

      <div className="credito-actions-section">
        <div className="form-container">
          <h2>Ajustar Limite de Crédito</h2>
          <form onSubmit={handleSubmit(onSubmit)} className="credito-form">
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

            <div className="form-actions">
              <button type="submit" className="btn btn-primary" disabled={submitting}>
                <FiSave /> {submitting ? 'Salvando...' : 'Salvar Alterações'}
              </button>
            </div>
          </form>
        </div>

        <div className="bloqueio-container">
          <h2>Bloqueio de Crédito</h2>
          <p className="bloqueio-description">
            {cliente.bloqueado
              ? 'Cliente bloqueado. Não pode realizar compras fiadas.'
              : 'Cliente ativo. Pode realizar compras fiadas dentro do limite disponível.'}
          </p>
          <button
            className={`btn ${cliente.bloqueado ? 'btn-success' : 'btn-danger'}`}
            onClick={handleToggleBloqueio}
            disabled={alterandoBloqueio}
          >
            {cliente.bloqueado ? <FiUnlock /> : <FiLock />}
            {alterandoBloqueio
              ? 'Processando...'
              : cliente.bloqueado
              ? 'Desbloquear Cliente'
              : 'Bloquear Cliente'}
          </button>
        </div>
      </div>

      {historico.length > 0 && (
        <div className="historico-section">
          <h2>Histórico de Crédito</h2>
          <div className="historico-list">
            {historico.map((item) => (
              <div key={item.id} className="historico-item">
                <div className="historico-header">
                  <span className={`historico-tipo badge-${getTipoClass(item.tipo)}`}>
                    {getTipoLabel(item.tipo)}
                  </span>
                  <span className="historico-data">{formatarData(item.data)}</span>
                </div>
                <p className="historico-descricao">{item.descricao}</p>
                {item.valor_anterior !== undefined && item.valor_novo !== undefined && (
                  <div className="historico-valores">
                    <span>
                      De: <strong>{formatarMoeda(item.valor_anterior)}</strong>
                    </span>
                    <span>→</span>
                    <span>
                      Para: <strong>{formatarMoeda(item.valor_novo)}</strong>
                    </span>
                  </div>
                )}
                <span className="historico-usuario">Por: {item.usuario}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default ClienteCreditoPage;
