import { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  FiArrowLeft,
  FiPlus,
  FiMinus,
  FiEdit2,
  FiBookmark,
  FiUnlock,
  FiArrowRight,
} from 'react-icons/fi';
import { useEstoque, useMovimentacoes, useLotes } from '@/hooks/useEstoque';
import { useProduto } from '@/hooks/useProdutos';
import type { TipoMovimentacao } from '@/types/estoque';
import type { Variante } from '@/types/produtos';
import EstoqueStatusBadge from './components/EstoqueStatusBadge';
import MovimentacaoTimeline from './components/MovimentacaoTimeline';
import { MOV_INFO } from './components/MovimentacaoBadge';
import EstoqueOperacaoModal, { type OperacaoEstoque } from './components/EstoqueOperacaoModal';
import { formatarQuantidade, formatarData } from './estoqueFormat';
import './EstoqueDetalhePage.scss';

type TipoFiltro = TipoMovimentacao | 'todos';

const ACOES: { operacao: OperacaoEstoque; label: string; icon: React.ReactNode; tom: string }[] = [
  { operacao: 'entrada', label: 'Entrada', icon: <FiPlus />, tom: 'success' },
  { operacao: 'saida', label: 'Saída', icon: <FiMinus />, tom: 'danger' },
  { operacao: 'ajuste', label: 'Ajuste', icon: <FiEdit2 />, tom: 'warning' },
  { operacao: 'reservar', label: 'Reservar', icon: <FiBookmark />, tom: 'info' },
  { operacao: 'liberar', label: 'Liberar reserva', icon: <FiUnlock />, tom: 'info' },
];

const FLUXO = [
  'Estoque físico',
  'Reserva criada',
  'Pagamento aprovado',
  'Baixa automática',
  'Pedido entregue',
];

/** Rótulo humano da variante (SKU + atributos). Nunca expõe o id. */
const varianteLabel = (variante: Variante): string => {
  const atributos = variante.atributos?.map((attr) => `${attr.chave}: ${attr.valor}`).join(', ');
  return atributos ? `${variante.sku} · ${atributos}` : variante.sku;
};

const EstoqueDetalhePage = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [tipoFiltro, setTipoFiltro] = useState<TipoFiltro>('todos');
  const [operacao, setOperacao] = useState<OperacaoEstoque | null>(null);

  const { data: estoque, isLoading, isError } = useEstoque(id);
  const { data: produto, isLoading: produtoLoading } = useProduto(estoque?.produto_id);
  const { data: movimentacoes = [], isLoading: carregandoMov } = useMovimentacoes(id, {
    tipo: tipoFiltro === 'todos' ? undefined : tipoFiltro,
    limit: 100,
  });
  const { data: lotes = [] } = useLotes(id);

  if (isLoading) {
    return (
      <div className="estoque-detalhe-page">
        <div className="loading">
          <div className="spinner-border" role="status">
            <span className="visually-hidden">Carregando...</span>
          </div>
        </div>
      </div>
    );
  }

  if (isError || !estoque) {
    return (
      <div className="estoque-detalhe-page">
        <button className="btn-back" onClick={() => navigate('/estoque')}>
          <FiArrowLeft /> Voltar para o estoque
        </button>
        <div className="empty-state">
          <p>Registro de estoque não encontrado</p>
        </div>
      </div>
    );
  }

  const produtoNome = produto?.nome ?? (produtoLoading ? 'Carregando…' : 'Produto sem cadastro');
  const variante = produto?.variantes?.find((item) => item.id === estoque.variante_id);

  const metadados: string[] = [];
  if (estoque.localizacao) metadados.push(`Local: ${estoque.localizacao}`);
  if (produto?.sku) metadados.push(`SKU ${produto.sku}`);
  if (produto?.codigo_barras) metadados.push(`Cód. ${produto.codigo_barras}`);
  if (estoque.variante_id) {
    metadados.push(variante ? `Variante: ${varianteLabel(variante)}` : 'Variante');
  }

  const saldos = [
    { label: 'Físico', valor: estoque.quantidade, tom: '' },
    { label: 'Reservado', valor: estoque.quantidade_reservada, tom: 'info' },
    { label: 'Disponível', valor: estoque.quantidade_disponivel, tom: 'success' },
    { label: 'Mínimo', valor: estoque.estoque_minimo, tom: 'muted' },
    { label: 'Máximo', valor: estoque.estoque_maximo ?? 0, tom: 'muted' },
  ];

  const filtrosTipo: TipoFiltro[] = ['todos', ...(Object.keys(MOV_INFO) as TipoMovimentacao[])];

  return (
    <div className="estoque-detalhe-page">
      <button className="btn-back" onClick={() => navigate('/estoque')}>
        <FiArrowLeft /> Voltar para o estoque
      </button>

      <div className="detalhe-header">
        <div>
          <h1>{produtoNome}</h1>
          <p className="sub">
            {metadados.length > 0 ? metadados.join(' · ') : 'Sem informações adicionais'}
          </p>
        </div>
        <EstoqueStatusBadge estoque={estoque} />
      </div>

      <div className="saldo-grid">
        {saldos.map((saldo) => (
          <div key={saldo.label} className={`saldo-card ${saldo.tom ? `saldo-card--${saldo.tom}` : ''}`}>
            <span className="saldo-valor">{formatarQuantidade(saldo.valor)}</span>
            <span className="saldo-label">{saldo.label}</span>
          </div>
        ))}
      </div>

      <div className="acoes-bar">
        {ACOES.map((acao) => (
          <button
            key={acao.operacao}
            type="button"
            className={`acao-btn acao-btn--${acao.tom}`}
            onClick={() => setOperacao(acao.operacao)}
          >
            {acao.icon} {acao.label}
          </button>
        ))}
      </div>

      <section className="lifecycle">
        <h2>Ciclo de vida no ERP</h2>
        <div className="lifecycle-flow">
          {FLUXO.map((passo, indice) => (
            <div key={passo} className="lifecycle-step">
              <span className="lifecycle-dot">{indice + 1}</span>
              <span className="lifecycle-text">{passo}</span>
              {indice < FLUXO.length - 1 && <FiArrowRight className="lifecycle-arrow" />}
            </div>
          ))}
        </div>
        <ul className="lifecycle-alt">
          <li>Pagamento expira → <strong>reserva liberada</strong> (volta a disponível)</li>
          <li>Reembolso → <strong>estoque restaurado</strong> (movimentação de Devolução)</li>
        </ul>
      </section>

      <section className="movimentacoes">
        <div className="section-head">
          <h2>Histórico de movimentações</h2>
          <div className="tipo-filtros">
            {filtrosTipo.map((tipo) => (
              <button
                key={tipo}
                type="button"
                className={`chip ${tipoFiltro === tipo ? 'chip--active' : ''}`}
                onClick={() => setTipoFiltro(tipo)}
              >
                {tipo === 'todos' ? 'Todas' : MOV_INFO[tipo].label}
              </button>
            ))}
          </div>
        </div>

        {carregandoMov ? (
          <div className="loading">
            <div className="spinner-border" role="status">
              <span className="visually-hidden">Carregando...</span>
            </div>
          </div>
        ) : (
          <MovimentacaoTimeline movimentacoes={movimentacoes} />
        )}
      </section>

      {lotes.length > 0 && (
        <section className="lotes">
          <h2>Lotes</h2>
          <div className="table-responsive">
            <table className="estoque-table">
              <thead>
                <tr>
                  <th>Código</th>
                  <th className="num">Quantidade</th>
                  <th>Validade</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {lotes.map((lote) => (
                  <tr key={lote.id}>
                    <td className="nome">{lote.codigo}</td>
                    <td className="num">{formatarQuantidade(lote.quantidade)}</td>
                    <td>
                      {formatarData(lote.data_validade)}
                      {lote.vencido && <span className="lote-flag lote-flag--danger">Vencido</span>}
                      {!lote.vencido && lote.alerta_vencimento && (
                        <span className="lote-flag lote-flag--warning">
                          Vence em {lote.dias_para_vencer}d
                        </span>
                      )}
                    </td>
                    <td>{lote.status}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {operacao && (
        <EstoqueOperacaoModal
          operacao={operacao}
          estoque={estoque}
          produtoNome={produtoNome}
          onClose={() => setOperacao(null)}
        />
      )}
    </div>
  );
};

export default EstoqueDetalhePage;
