import type { Movimentacao } from '@/types/estoque';
import MovimentacaoBadge from './MovimentacaoBadge';
import { formatarQuantidade, formatarDataHora } from '../estoqueFormat';

/** Variação líquida com sinal (cobre AJUSTE, que pode subir ou descer). */
const sinalDelta = (movimentacao: Movimentacao): string => {
  const delta = movimentacao.quantidade_posterior - movimentacao.quantidade_anterior;
  const valor = formatarQuantidade(Math.abs(delta));
  if (delta > 0) return `+${valor}`;
  if (delta < 0) return `-${valor}`;
  return valor;
};

/**
 * Linha do tempo de movimentações: cada lançamento mostra tipo, variação, saldo
 * antes→depois, motivo e documento — tornando visível cada transição do ciclo de vida
 * (venda → baixa, reembolso → devolução, ajuste de inventário, etc.).
 */
const MovimentacaoTimeline: React.FC<{ movimentacoes: Movimentacao[] }> = ({ movimentacoes }) => {
  if (movimentacoes.length === 0) {
    return (
      <div className="empty-state">
        <p>Nenhuma movimentação registrada para este filtro</p>
      </div>
    );
  }

  return (
    <ul className="mov-timeline">
      {movimentacoes.map((movimentacao) => (
        <li key={movimentacao.id} className="mov-timeline__item">
          <span className={`mov-timeline__marker mov-timeline__marker--${movimentacao.tipo.toLowerCase()}`} />
          <div className="mov-timeline__content">
            <div className="mov-timeline__head">
              <MovimentacaoBadge tipo={movimentacao.tipo} />
              <span className="mov-timeline__delta">{sinalDelta(movimentacao)}</span>
              <span className="mov-timeline__saldo">
                {formatarQuantidade(movimentacao.quantidade_anterior)} →{' '}
                {formatarQuantidade(movimentacao.quantidade_posterior)}
              </span>
              <time className="mov-timeline__date">{formatarDataHora(movimentacao.created_at)}</time>
            </div>
            {(movimentacao.motivo || movimentacao.documento) && (
              <div className="mov-timeline__meta">
                {movimentacao.motivo && (
                  <span className="mov-timeline__motivo">{movimentacao.motivo}</span>
                )}
                {movimentacao.documento && (
                  <span className="mov-timeline__doc">Doc: {movimentacao.documento}</span>
                )}
              </div>
            )}
          </div>
        </li>
      ))}
    </ul>
  );
};

export default MovimentacaoTimeline;
