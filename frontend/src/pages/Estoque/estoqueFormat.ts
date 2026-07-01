// Formatadores compartilhados do módulo de Estoque.

const QUANTIDADE = new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 2 });

export const formatarQuantidade = (valor: number | null | undefined): string =>
  QUANTIDADE.format(Number(valor ?? 0));

export const formatarDataHora = (iso: string): string =>
  new Date(iso).toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'short' });

export const formatarData = (iso: string | null): string =>
  iso ? new Date(iso).toLocaleDateString('pt-BR') : '—';
