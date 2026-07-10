import { useState } from 'react';
import { toast } from 'react-toastify';
import Modal from '@/components/common/Modal/Modal';
import { getErrorMessage } from '@/services/api/axios';
import type { Estoque } from '@/types/estoque';
import {
  useEntradaEstoque,
  useSaidaEstoque,
  useAjusteEstoque,
  useReservarEstoque,
  useLiberarReserva,
} from '@/hooks/useEstoque';
import { useAuth } from '@/hooks/useAuth';
import { formatarQuantidade } from '../estoqueFormat';

export type OperacaoEstoque = 'entrada' | 'saida' | 'ajuste' | 'reservar' | 'liberar';

interface Props {
  operacao: OperacaoEstoque;
  /** null = primeira entrada de um produto sem linha de estoque (exige produtoIdInicial). */
  estoque: Estoque | null;
  produtoNome?: string;
  /** Produto da primeira entrada quando não há linha de estoque (linha "Nunca recebido"). */
  produtoIdInicial?: string;
  onClose: () => void;
}

const TITULOS: Record<OperacaoEstoque, string> = {
  entrada: 'Entrada de estoque',
  saida: 'Saída de estoque',
  ajuste: 'Ajuste de inventário',
  reservar: 'Reservar estoque',
  liberar: 'Liberar reserva',
};

const LABEL_QUANTIDADE: Record<OperacaoEstoque, string> = {
  entrada: 'Quantidade a adicionar',
  saida: 'Quantidade a remover',
  ajuste: 'Nova quantidade (contagem física)',
  reservar: 'Quantidade a reservar',
  liberar: 'Quantidade a liberar',
};

const SUBMIT_LABEL: Record<OperacaoEstoque, string> = {
  entrada: 'Registrar entrada',
  saida: 'Registrar saída',
  ajuste: 'Aplicar ajuste',
  reservar: 'Reservar',
  liberar: 'Liberar',
};

const FORM_ID = 'estoque-operacao-form';

const EstoqueOperacaoModal: React.FC<Props> = ({
  operacao,
  estoque,
  produtoNome,
  produtoIdInicial,
  onClose,
}) => {
  const { user } = useAuth();
  const [quantidade, setQuantidade] = useState('');
  const [motivo, setMotivo] = useState('');
  const [documento, setDocumento] = useState('');
  const [custo, setCusto] = useState('');
  const [observacao, setObservacao] = useState('');

  const entrada = useEntradaEstoque();
  const saida = useSaidaEstoque();
  const ajuste = useAjusteEstoque();
  const reservar = useReservarEstoque();
  const liberar = useLiberarReserva();

  const pending =
    entrada.isPending ||
    saida.isPending ||
    ajuste.isPending ||
    reservar.isPending ||
    liberar.isPending;

  const mostraMotivo = operacao === 'entrada' || operacao === 'saida' || operacao === 'ajuste';
  const motivoObrigatorio = operacao === 'ajuste';
  const mostraDocumento = operacao !== 'ajuste';
  const mostraCusto = operacao === 'entrada';
  const mostraObservacao = operacao === 'entrada' || operacao === 'saida' || operacao === 'ajuste';

  const callbacks = {
    onSuccess: () => {
      toast.success('Operação registrada com sucesso');
      onClose();
    },
    onError: (error: unknown) => toast.error(getErrorMessage(error)),
  };

  const base = {
    empresa_id: estoque?.empresa_id ?? user!.empresa_id,
    produto_id: estoque?.produto_id ?? produtoIdInicial ?? '',
    variante_id: estoque?.variante_id,
  };

  const acoes: Record<OperacaoEstoque, (qtd: number) => void> = {
    entrada: (qtd) =>
      entrada.mutate(
        {
          ...base,
          quantidade: qtd,
          motivo: motivo || undefined,
          documento: documento || undefined,
          observacao: observacao || undefined,
          custo_unitario: custo ? Number(custo) : undefined,
        },
        callbacks,
      ),
    saida: (qtd) =>
      saida.mutate(
        {
          ...base,
          quantidade: qtd,
          motivo: motivo || undefined,
          documento: documento || undefined,
          observacao: observacao || undefined,
        },
        callbacks,
      ),
    ajuste: (qtd) =>
      ajuste.mutate(
        {
          estoque_id: estoque!.id,
          quantidade_nova: qtd,
          motivo: motivo.trim(),
          observacao: observacao || undefined,
        },
        callbacks,
      ),
    reservar: (qtd) =>
      reservar.mutate({ ...base, quantidade: qtd, documento: documento || undefined }, callbacks),
    liberar: (qtd) =>
      liberar.mutate({ ...base, quantidade: qtd, documento: documento || undefined }, callbacks),
  };

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    if (!base.produto_id) {
      toast.error('Produto não identificado para a operação');
      return;
    }
    const qtd = Number(quantidade);
    const quantidadeInvalida = Number.isNaN(qtd) || (operacao === 'ajuste' ? qtd < 0 : qtd <= 0);
    if (quantidadeInvalida) {
      toast.error('Informe uma quantidade válida');
      return;
    }
    if (motivoObrigatorio && !motivo.trim()) {
      toast.error('Informe o motivo do ajuste');
      return;
    }
    acoes[operacao](qtd);
  };

  const footer = (
    <>
      <button type="button" className="btn btn-ghost" onClick={onClose} disabled={pending}>
        Cancelar
      </button>
      <button type="submit" form={FORM_ID} className="btn btn-primary" disabled={pending}>
        {pending ? 'Processando...' : SUBMIT_LABEL[operacao]}
      </button>
    </>
  );

  return (
    <Modal isOpen title={TITULOS[operacao]} onClose={onClose} footer={footer}>
      <p className="estoque-op-produto">{produtoNome}</p>

      {estoque && (
        <div className="estoque-op-saldo">
          <span>Físico: <strong>{formatarQuantidade(estoque.quantidade)}</strong></span>
          <span>Reservado: <strong>{formatarQuantidade(estoque.quantidade_reservada)}</strong></span>
          <span>Disponível: <strong>{formatarQuantidade(estoque.quantidade_disponivel)}</strong></span>
        </div>
      )}

      <form id={FORM_ID} className="estoque-op-form" onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="op-quantidade">{LABEL_QUANTIDADE[operacao]}</label>
          <input
            id="op-quantidade"
            type="number"
            min={operacao === 'ajuste' ? 0 : 0.01}
            step="0.01"
            value={quantidade}
            onChange={(event) => setQuantidade(event.target.value)}
            autoFocus
            required
          />
        </div>

        {mostraMotivo && (
          <div className="form-group">
            <label htmlFor="op-motivo">Motivo{motivoObrigatorio ? ' *' : ''}</label>
            <input
              id="op-motivo"
              type="text"
              maxLength={200}
              value={motivo}
              onChange={(event) => setMotivo(event.target.value)}
              placeholder={operacao === 'ajuste' ? 'Ex.: Correção de inventário' : 'Opcional'}
            />
          </div>
        )}

        {mostraDocumento && (
          <div className="form-group">
            <label htmlFor="op-documento">Documento</label>
            <input
              id="op-documento"
              type="text"
              maxLength={100}
              value={documento}
              onChange={(event) => setDocumento(event.target.value)}
              placeholder="Nº da nota, pedido ou venda (opcional)"
            />
          </div>
        )}

        {mostraCusto && (
          <div className="form-group">
            <label htmlFor="op-custo">Custo unitário</label>
            <input
              id="op-custo"
              type="number"
              min={0}
              step="0.01"
              value={custo}
              onChange={(event) => setCusto(event.target.value)}
              placeholder="Opcional"
            />
          </div>
        )}

        {mostraObservacao && (
          <div className="form-group">
            <label htmlFor="op-observacao">Observação</label>
            <textarea
              id="op-observacao"
              rows={2}
              value={observacao}
              onChange={(event) => setObservacao(event.target.value)}
              placeholder="Opcional"
            />
          </div>
        )}
      </form>
    </Modal>
  );
};

export default EstoqueOperacaoModal;
