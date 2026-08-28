import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { FiDownload, FiRotateCcw, FiCopy, FiXCircle } from 'react-icons/fi';
import { toast } from 'react-toastify';
import Modal from '@/components/common/Modal/Modal';
import { getErrorMessage } from '@/services/api/axios';
import { plataformaApi } from '@/services/api/plataformaApi';
import {
  useAuditoria,
  useDumps,
  useReverterRegistro,
  useCriarAssinatura,
  useCancelarAssinatura,
} from '@/hooks/usePlataforma';
import type { Tenant, AuditoriaResult, AssinaturaLink } from '@/types/plataforma';
import { assinaturaSchema, valorParaNumero, type AssinaturaFormData } from './assinaturaSchema';

type Aba = 'auditoria' | 'assinatura' | 'backups';

const ABAS: Array<{ id: Aba; label: string }> = [
  { id: 'auditoria', label: 'Auditoria' },
  { id: 'assinatura', label: 'Assinatura' },
  { id: 'backups', label: 'Backups' },
];

interface Linha {
  chave: string;
  criado_em: string;
  oQue: string;
  detalhe: string;
  registroId: number | null;
  /** Só as linhas de snapshot têm diff; a trilha do middleware não tem estado. */
  diff: string | null;
}

const quando = (iso: string) => new Date(iso).toLocaleString('pt-BR');

/**
 * Campos que realmente mudam, em "campo: antes -> depois".
 *
 * O registro inteiro tem dezenas de colunas e quase nenhuma muda; despejar os
 * dois jsonb crus num confirm() é o mesmo que não mostrar nada. Só o delta
 * responde a pergunta que o super admin está fazendo antes de sobrescrever.
 */
const resumirDiff = (
  antes: Record<string, unknown> | null,
  depois: Record<string, unknown> | null,
): string | null => {
  if (!antes) return null;
  const mudou = Object.keys(antes).filter(
    (k) => JSON.stringify(antes[k]) !== JSON.stringify(depois?.[k]),
  );
  if (mudou.length === 0) return null;
  return mudou
    .map((k) => `${k}: ${JSON.stringify(depois?.[k]) ?? '—'} -> ${JSON.stringify(antes[k])}`)
    .join('\n');
};

/**
 * As duas camadas viram uma lista só, ordenada no tempo.
 *
 * A trilha do middleware dá o "quem e quando" e nunca é reversível; só as linhas
 * de snapshot carregam `registroId`, e o backend já diz quais ainda podem voltar.
 */
const unificar = (dados: AuditoriaResult): Linha[] =>
  [
    ...dados.registros.map((r) => ({
      chave: `snap-${r.id}`,
      criado_em: r.criado_em,
      oQue: `${r.operacao} ${r.schema_origem}.${r.tabela}`,
      detalhe: r.revertido_em ? `#${r.registro_id} — revertido` : `#${r.registro_id}`,
      registroId: r.reversivel ? r.id : null,
      diff: resumirDiff(r.dados_antes, r.dados_depois),
    })),
    ...dados.requisicoes.map((q) => ({
      chave: `req-${q.id}`,
      criado_em: q.criado_em,
      oQue: `${q.metodo} ${q.rota}`,
      detalhe: `HTTP ${q.status_resposta}`,
      registroId: null,
      diff: null,
    })),
  ].sort((a, b) => b.criado_em.localeCompare(a.criado_em));

/** Abas de auditoria, assinatura e backups do tenant — o detalhe da tela /plataforma. */
const TenantDetalhe = ({ tenant, onClose }: { tenant: Tenant | null; onClose: () => void }) => {
  const [aba, setAba] = useState<Aba>('auditoria');
  // Erro do backend na própria aba: no 409 de reversão a explicação É o resultado
  // — o super admin precisa ler por que aquela operação não pode voltar.
  const [erro, setErro] = useState<string | null>(null);
  const [link, setLink] = useState<AssinaturaLink | null>(null);

  const tenantId = tenant?.id ?? null;
  const auditoria = useAuditoria(aba === 'auditoria' ? tenantId : null);
  const dumps = useDumps(aba === 'backups' ? tenantId : null);
  const reverter = useReverterRegistro();
  const criarAssinatura = useCriarAssinatura();
  const cancelarAssinatura = useCancelarAssinatura();

  const form = useForm<AssinaturaFormData>({
    resolver: zodResolver(assinaturaSchema),
    defaultValues: { plano: tenant?.plano ?? 'BASICO', valor: '', email_pagador: '' },
  });

  const trocarAba = (proxima: Aba) => {
    setErro(null);
    setAba(proxima);
  };

  const handleReverter = (linha: Linha) => {
    if (!linha.registroId) return;
    const aviso = linha.diff
      ? `Reverter ${linha.oQue} (${linha.detalhe})?\n\nO que volta ao valor antigo:\n${linha.diff}`
      : `Reverter ${linha.oQue} (${linha.detalhe}) ao estado anterior?`;
    if (!window.confirm(aviso)) return;
    setErro(null);
    reverter.mutate(linha.registroId, {
      onSuccess: () => toast.success('Operação revertida'),
      onError: (error) => setErro(getErrorMessage(error, 'Não foi possível reverter')),
    });
  };

  const submitAssinatura = async (dados: AssinaturaFormData) => {
    if (!tenant) return;
    setErro(null);
    try {
      setLink(
        await criarAssinatura.mutateAsync({
          id: tenant.id,
          data: {
            plano: dados.plano,
            valor: valorParaNumero(dados.valor),
            email_pagador: dados.email_pagador,
          },
        })
      );
      toast.success('Link de assinatura gerado');
    } catch (error) {
      setErro(getErrorMessage(error, 'Erro ao gerar o link de assinatura'));
    }
  };

  const handleCancelar = () => {
    if (!tenant) return;
    if (!window.confirm(`Cancelar a assinatura de ${tenant.nome_fantasia}?`)) return;
    setErro(null);
    cancelarAssinatura.mutate(tenant.id, {
      onSuccess: () => {
        setLink(null);
        toast.success('Assinatura cancelada');
      },
      onError: (error) => setErro(getErrorMessage(error, 'Erro ao cancelar a assinatura')),
    });
  };

  if (!tenant) return null;
  const linhas = auditoria.data ? unificar(auditoria.data) : [];

  return (
    <Modal isOpen title={`Tenant — ${tenant.nome_fantasia}`} onClose={onClose}>
      <div className="tenant-detalhe admin-list">
        <div className="detalhe-topo">
          <div className="tabs" role="tablist">
            {ABAS.map((a) => (
              <button
                key={a.id}
                type="button"
                role="tab"
                aria-selected={aba === a.id}
                className={`tab ${aba === a.id ? 'active' : ''}`}
                onClick={() => trocarAba(a.id)}
              >
                {a.label}
              </button>
            ))}
          </div>
          <a
            className="btn btn-sm btn-outline-primary"
            href={plataformaApi.urlExportar(tenant.id)}
            target="_blank"
            rel="noreferrer"
          >
            <FiDownload /> Exportar JSON
          </a>
        </div>

        {erro && <div className="form-error">{erro}</div>}

        {aba === 'auditoria' && (
          <div className="table-responsive">
            {auditoria.isLoading ? (
              <div className="empty-state">Carregando...</div>
            ) : linhas.length === 0 ? (
              <div className="empty-state">Nenhuma escrita registrada para este tenant</div>
            ) : (
              <table>
                <thead>
                  <tr>
                    <th>Quando</th>
                    <th>Operação</th>
                    <th>Detalhe</th>
                    <th>Ações</th>
                  </tr>
                </thead>
                <tbody>
                  {linhas.map((linha) => (
                    <tr key={linha.chave}>
                      <td data-label="Quando">{quando(linha.criado_em)}</td>
                      <td data-label="Operação">{linha.oQue}</td>
                      <td data-label="Detalhe">{linha.detalhe}</td>
                      <td data-label="Ações">
                        {linha.registroId !== null && (
                          <button
                            type="button"
                            className="btn btn-sm btn-outline-danger"
                            onClick={() => handleReverter(linha)}
                            disabled={reverter.isPending}
                          >
                            <FiRotateCcw /> Reverter
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )}

        {aba === 'assinatura' && (
          <form className="admin-form" onSubmit={form.handleSubmit(submitAssinatura)}>
            <p className="detalhe-nota">
              Plano atual: <strong>{tenant.plano}</strong> · Status da empresa:{' '}
              <strong>{tenant.status}</strong>. O status da cobrança é atualizado pelo webhook do
              Mercado Pago e não é exposto por esta API.
            </p>

            <div className="form-row">
              <div className="form-group">
                <label htmlFor="assinatura_plano">Plano *</label>
                <input id="assinatura_plano" type="text" {...form.register('plano')} />
                {form.formState.errors.plano && (
                  <span className="field-error">{form.formState.errors.plano.message}</span>
                )}
              </div>
              <div className="form-group">
                <label htmlFor="assinatura_valor">Valor mensal (R$) *</label>
                <input
                  id="assinatura_valor"
                  type="text"
                  placeholder="99,90"
                  {...form.register('valor')}
                />
                {form.formState.errors.valor && (
                  <span className="field-error">{form.formState.errors.valor.message}</span>
                )}
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="assinatura_email">E-mail do pagador *</label>
              <input id="assinatura_email" type="email" {...form.register('email_pagador')} />
              {form.formState.errors.email_pagador && (
                <span className="field-error">{form.formState.errors.email_pagador.message}</span>
              )}
            </div>

            {link && (
              <div className="form-group">
                <label htmlFor="assinatura_link">Link de adesão ({link.preapproval_id})</label>
                <div className="form-row">
                  <input id="assinatura_link" type="text" readOnly value={link.init_point} />
                  <button
                    type="button"
                    className="btn btn-secondary"
                    onClick={() =>
                      navigator.clipboard
                        .writeText(link.init_point)
                        .then(() => toast.success('Link copiado'))
                    }
                  >
                    <FiCopy /> Copiar
                  </button>
                </div>
              </div>
            )}

            <div className="form-actions">
              <button
                type="button"
                className="btn btn-outline-danger"
                onClick={handleCancelar}
                disabled={cancelarAssinatura.isPending}
              >
                <FiXCircle /> Cancelar assinatura
              </button>
              <button type="submit" className="btn btn-primary" disabled={form.formState.isSubmitting}>
                Gerar link de assinatura
              </button>
            </div>
          </form>
        )}

        {aba === 'backups' && (
          <div className="empty-state">
            {dumps.isLoading ? (
              'Carregando...'
            ) : (
              <>
                <p>Nenhum dump disponível — o backup automático entra na Fase 4.</p>
                <p className="detalhe-nota">
                  Restaurar sobrescreve o tenant inteiro e descarta tudo posterior ao dump. Por isso
                  é operação de terminal, com revisão humana: <code>{dumps.data?.detalhe}</code>. O
                  caminho de suporte do dia a dia é a reversão pontual na aba Auditoria.
                </p>
              </>
            )}
          </div>
        )}
      </div>
    </Modal>
  );
};

export default TenantDetalhe;
