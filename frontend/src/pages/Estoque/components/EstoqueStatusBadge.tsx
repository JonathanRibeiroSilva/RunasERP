import type { Estoque } from '@/types/estoque';

type Variant = 'success' | 'warning' | 'danger';

const resolverStatus = (estoque: Estoque): { label: string; variant: Variant } => {
  if (estoque.alerta_estoque_zerado) return { label: 'Sem estoque', variant: 'danger' };
  if (estoque.alerta_estoque_baixo) return { label: 'Estoque baixo', variant: 'warning' };
  return { label: 'Disponível', variant: 'success' };
};

/** Indicador de saúde do estoque (zerado / baixo / disponível). */
const EstoqueStatusBadge: React.FC<{ estoque: Estoque }> = ({ estoque }) => {
  const { label, variant } = resolverStatus(estoque);
  return <span className={`estoque-badge estoque-badge--${variant}`}>{label}</span>;
};

export default EstoqueStatusBadge;
