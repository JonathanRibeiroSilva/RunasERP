import type { TipoMovimentacao } from '@/types/estoque';

interface MovInfo {
  label: string;
  variant: string;
}

/** Rótulo + cor de cada tipo de movimentação (também usado nos filtros do timeline). */
export const MOV_INFO: Record<TipoMovimentacao, MovInfo> = {
  ENTRADA: { label: 'Entrada', variant: 'entrada' },
  SAIDA: { label: 'Saída', variant: 'saida' },
  AJUSTE: { label: 'Ajuste', variant: 'ajuste' },
  DEVOLUCAO: { label: 'Devolução', variant: 'devolucao' },
  PERDA: { label: 'Perda', variant: 'perda' },
  TRANSFERENCIA: { label: 'Transferência', variant: 'transferencia' },
};

const MovimentacaoBadge: React.FC<{ tipo: TipoMovimentacao }> = ({ tipo }) => {
  const info = MOV_INFO[tipo] ?? { label: tipo, variant: 'ajuste' };
  return <span className={`mov-badge mov-badge--${info.variant}`}>{info.label}</span>;
};

export default MovimentacaoBadge;
