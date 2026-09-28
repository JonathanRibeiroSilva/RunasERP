import { Link } from 'react-router-dom';
import {
  FiGrid,
  FiUsers,
  FiDollarSign,
  FiAlertTriangle,
  FiSlash,
  FiArrowRight,
} from 'react-icons/fi';
import { useTenants } from '@/hooks/usePlataforma';
import type { Tenant } from '@/types/plataforma';
import { valorParaNumero } from './assinaturaSchema';

/**
 * Os números do negócio, derivados da mesma lista que a tela de lojistas usa.
 *
 * Sem endpoint novo: GET /plataforma/tenants já devolve status, assinatura e
 * usuários ativos de cada lojista. Uma rota de agregação no gateway só faria no
 * Postgres o que aqui é um reduce sobre dados que já estão na memória — e o
 * React Query compartilha o cache, então abrir as duas telas não busca duas vezes.
 */
export const resumirTenants = (tenants: Tenant[]) => ({
  lojistas: tenants.length,
  ativos: tenants.filter((t) => t.ativo).length,
  // Só ATIVA entra no MRR: PENDENTE ainda não foi paga e INADIMPLENTE parou de
  // ser paga — somar as duas infla a receita com dinheiro que não entrou.
  mrr: tenants.reduce(
    (soma, t) => soma + (t.assinatura?.status === 'ATIVA' ? valorParaNumero(t.assinatura.valor) : 0),
    0,
  ),
  // INADIMPLENTE (escrita bloqueada) e SUSPENSA (acesso cortado) são o mesmo
  // trabalho para você: cobrar. Contar junto evita dois cartões dizendo o mesmo.
  aCobrar: tenants.filter(
    (t) => t.assinatura?.status === 'INADIMPLENTE' || t.assinatura?.status === 'SUSPENSA',
  ).length,
  // Provisionado e nunca cobrado: cortesia, teste — ou uma cobrança esquecida.
  semAssinatura: tenants.filter((t) => t.assinatura === null).length,
});

/** Visão geral da plataforma: o negócio do dono do Runas, não o de nenhum lojista. */
const PlataformaDashboard = () => {
  const { data, isLoading } = useTenants();
  const resumo = resumirTenants(data?.items ?? []);

  return (
    <div className="admin-list">
      <div className="page-header">
        <h1><FiGrid className="title-icon" /> Plataforma</h1>
        <p className="page-description">
          Quantos lojistas assinam o Runas, quanto entra por mês e quem está devendo.
        </p>
      </div>

      <div className="stats-grid">
        <div className="stat-card stat-primary">
          <div className="stat-icon-wrapper"><div className="stat-icon"><FiUsers /></div></div>
          <div className="stat-content">
            <p className="stat-title">Lojistas</p>
            <h3 className="stat-value font-mono">{isLoading ? '—' : resumo.lojistas}</h3>
            <span className="stat-change">{resumo.ativos} com acesso liberado</span>
          </div>
        </div>
        <div className="stat-card stat-success">
          <div className="stat-icon-wrapper"><div className="stat-icon"><FiDollarSign /></div></div>
          <div className="stat-content">
            <p className="stat-title">Receita mensal</p>
            <h3 className="stat-value font-mono">
              {isLoading
                ? '—'
                : resumo.mrr.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
            </h3>
            <span className="stat-change">apenas assinaturas ativas</span>
          </div>
        </div>
        <div className="stat-card stat-warning">
          <div className="stat-icon-wrapper"><div className="stat-icon"><FiAlertTriangle /></div></div>
          <div className="stat-content">
            <p className="stat-title">A cobrar</p>
            <h3 className="stat-value font-mono">{isLoading ? '—' : resumo.aCobrar}</h3>
            <span className="stat-change">inadimplentes ou suspensos</span>
          </div>
        </div>
        <div className="stat-card stat-secondary">
          <div className="stat-icon-wrapper"><div className="stat-icon"><FiSlash /></div></div>
          <div className="stat-content">
            <p className="stat-title">Sem assinatura</p>
            <h3 className="stat-value font-mono">{isLoading ? '—' : resumo.semAssinatura}</h3>
            <span className="stat-change">provisionados e nunca cobrados</span>
          </div>
        </div>
      </div>

      <div className="list-header">
        <span className="list-counter">
          Provisionar, cobrar, suspender e auditar ficam na tela de lojistas.
        </span>
        <Link className="btn btn-primary" to="/plataforma/tenants">
          Ver lojistas <FiArrowRight />
        </Link>
      </div>
    </div>
  );
};

export default PlataformaDashboard;
