import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { FiZap, FiSave, FiTrash2 } from 'react-icons/fi';
import { toast } from 'react-toastify';
import { getErrorMessage } from '@/services/api/axios';
import {
  useIntegracoes,
  useSalvarIntegracoes,
  useRemoverIntegracoes,
  useStatusPagamento,
  useSalvarPagamento,
} from '@/hooks/useIntegracoes';
import type { IntegracaoUpdate } from '@/types/integracao';
import {
  integracoesSchema,
  pagamentoSchema,
  SEGREDO_PLACEHOLDER,
  type IntegracoesFormData,
  type PagamentoFormData,
} from './integracoesSchema';
import './Configuracoes.scss';

const texto = (valor?: string) => valor?.trim() || undefined;

/** Segredo só viaja quando o admin digitou algo novo: o placeholder significa "manter o atual". */
const segredo = (valor?: string) =>
  valor && valor !== SEGREDO_PLACEHOLDER ? valor : undefined;

const paraPayload = (data: IntegracoesFormData): IntegracaoUpdate => ({
  evolution_url: texto(data.evolution_url),
  evolution_api_key: segredo(data.evolution_api_key),
  evolution_instance: texto(data.evolution_instance),
  whatsapp_ativo: data.whatsapp_ativo,
  smtp_host: texto(data.smtp_host),
  smtp_port: data.smtp_port ? Number(data.smtp_port) : undefined,
  smtp_user: texto(data.smtp_user),
  smtp_password: segredo(data.smtp_password),
  smtp_from_name: texto(data.smtp_from_name),
  email_ativo: data.email_ativo,
});

const IntegracoesPage = () => {
  const { data: integracoes, isLoading } = useIntegracoes();
  const { data: pagamento } = useStatusPagamento();
  const salvar = useSalvarIntegracoes();
  const remover = useRemoverIntegracoes();
  const salvarPagamento = useSalvarPagamento();

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<IntegracoesFormData>({
    resolver: zodResolver(integracoesSchema),
    defaultValues: { whatsapp_ativo: false, email_ativo: false },
  });

  const formPagamento = useForm<PagamentoFormData>({
    resolver: zodResolver(pagamentoSchema),
    defaultValues: { ativo: true },
  });

  useEffect(() => {
    if (!integracoes) return;
    reset({
      evolution_url: integracoes.evolution_url ?? '',
      evolution_api_key: integracoes.evolution_api_key_configurado ? SEGREDO_PLACEHOLDER : '',
      evolution_instance: integracoes.evolution_instance ?? '',
      whatsapp_ativo: integracoes.whatsapp_ativo,
      smtp_host: integracoes.smtp_host ?? '',
      smtp_port: integracoes.smtp_port ? String(integracoes.smtp_port) : '',
      smtp_user: integracoes.smtp_user ?? '',
      smtp_password: integracoes.smtp_password_configurado ? SEGREDO_PLACEHOLDER : '',
      smtp_from_name: integracoes.smtp_from_name ?? '',
      email_ativo: integracoes.email_ativo,
    });
  }, [integracoes, reset]);

  useEffect(() => {
    if (pagamento) formPagamento.setValue('ativo', pagamento.ativo);
  }, [pagamento, formPagamento]);

  const onSubmit = async (data: IntegracoesFormData) => {
    try {
      await salvar.mutateAsync(paraPayload(data));
      toast.success('Integrações atualizadas');
    } catch (error) {
      toast.error(getErrorMessage(error, 'Erro ao salvar integrações'));
    }
  };

  const onSubmitPagamento = async (data: PagamentoFormData) => {
    try {
      await salvarPagamento.mutateAsync({
        data,
        jaConfigurado: !!pagamento?.configurado,
      });
      formPagamento.reset({ ...data, mercadopago_access_token: '', mercadopago_public_key: '' });
      toast.success('Credenciais do Mercado Pago salvas');
    } catch (error) {
      toast.error(getErrorMessage(error, 'Erro ao salvar credenciais do Mercado Pago'));
    }
  };

  const handleRemover = async () => {
    if (!window.confirm('Remover as integrações do tenant e voltar ao padrão global?')) return;
    try {
      await remover.mutateAsync();
      toast.success('Integrações removidas — o sistema volta ao padrão global');
    } catch (error) {
      toast.error(getErrorMessage(error, 'Erro ao remover integrações'));
    }
  };

  return (
    <div className="page-container integracoes-page">
      <div className="page-header">
        <h1><FiZap className="title-icon" /> Integrações</h1>
        <p className="page-description">
          Configure Mercado Pago, WhatsApp e e-mail com as credenciais da sua empresa
        </p>
      </div>

      <form className="form-section" onSubmit={formPagamento.handleSubmit(onSubmitPagamento)}>
        <div className="section-head">
          <h2>Mercado Pago</h2>
          <span className={`badge ${pagamento?.configurado ? 'badge-success' : 'badge-warning'}`}>
            {pagamento?.configurado ? 'Configurado' : 'Não configurado'}
          </span>
        </div>
        <p className="section-hint">
          Credenciais da sua aplicação em mercadopago.com.br/developers. O backend exige as duas
          credenciais inteiras a cada gravação — trocar uma é reenviar as duas.
        </p>

        <div className="form-group">
          <label htmlFor="mercadopago_access_token">Access Token *</label>
          <input
            id="mercadopago_access_token"
            type="password"
            autoComplete="off"
            placeholder={pagamento?.configurado ? SEGREDO_PLACEHOLDER : 'APP_USR-...'}
            {...formPagamento.register('mercadopago_access_token')}
          />
          {formPagamento.formState.errors.mercadopago_access_token && (
            <span className="field-error">
              {formPagamento.formState.errors.mercadopago_access_token.message}
            </span>
          )}
        </div>

        <div className="form-group">
          <label htmlFor="mercadopago_public_key">Public Key *</label>
          <input
            id="mercadopago_public_key"
            type="text"
            autoComplete="off"
            placeholder={pagamento?.configurado ? SEGREDO_PLACEHOLDER : 'APP_USR-...'}
            {...formPagamento.register('mercadopago_public_key')}
          />
          {formPagamento.formState.errors.mercadopago_public_key && (
            <span className="field-error">
              {formPagamento.formState.errors.mercadopago_public_key.message}
            </span>
          )}
        </div>

        <div className="switch-row">
          <label htmlFor="mp_ativo">Pagamento online ativo</label>
          <label className="switch">
            <input id="mp_ativo" type="checkbox" {...formPagamento.register('ativo')} />
            <span className="slider" />
          </label>
        </div>

        <div className="form-actions">
          <button type="submit" className="btn btn-primary" disabled={salvarPagamento.isPending}>
            <FiSave /> {salvarPagamento.isPending ? 'Salvando...' : 'Salvar Mercado Pago'}
          </button>
        </div>
      </form>

      {isLoading ? (
        <div className="loading">Carregando...</div>
      ) : (
        <form onSubmit={handleSubmit(onSubmit)}>
          <div className="form-section">
            <div className="section-head">
              <h2>WhatsApp (Evolution API)</h2>
              <span
                className={`badge ${integracoes?.evolution_api_key_configurado ? 'badge-success' : 'badge-warning'}`}
              >
                {integracoes?.evolution_api_key_configurado ? 'Configurado' : 'Não configurado'}
              </span>
            </div>

            <div className="form-group">
              <label htmlFor="evolution_url">URL da Evolution API</label>
              <input id="evolution_url" type="text" placeholder="https://evolution.exemplo.com" {...register('evolution_url')} />
              {errors.evolution_url && <span className="field-error">{errors.evolution_url.message}</span>}
            </div>

            <div className="form-row">
              <div className="form-group">
                <label htmlFor="evolution_api_key">API Key</label>
                <input id="evolution_api_key" type="password" autoComplete="off" {...register('evolution_api_key')} />
              </div>
              <div className="form-group">
                <label htmlFor="evolution_instance">Instância</label>
                <input id="evolution_instance" type="text" {...register('evolution_instance')} />
                {errors.evolution_instance && <span className="field-error">{errors.evolution_instance.message}</span>}
              </div>
            </div>

            <div className="switch-row">
              <label htmlFor="whatsapp_ativo">Notificações por WhatsApp ativas</label>
              <label className="switch">
                <input id="whatsapp_ativo" type="checkbox" {...register('whatsapp_ativo')} />
                <span className="slider" />
              </label>
            </div>
          </div>

          <div className="form-section">
            <div className="section-head">
              <h2>E-mail (SMTP)</h2>
              <span
                className={`badge ${integracoes?.smtp_password_configurado ? 'badge-success' : 'badge-warning'}`}
              >
                {integracoes?.smtp_password_configurado ? 'Configurado' : 'Não configurado'}
              </span>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label htmlFor="smtp_host">Servidor SMTP</label>
                <input id="smtp_host" type="text" placeholder="smtp.gmail.com" {...register('smtp_host')} />
                {errors.smtp_host && <span className="field-error">{errors.smtp_host.message}</span>}
              </div>
              <div className="form-group">
                <label htmlFor="smtp_port">Porta</label>
                <input id="smtp_port" type="text" inputMode="numeric" placeholder="587" {...register('smtp_port')} />
                {errors.smtp_port && <span className="field-error">{errors.smtp_port.message}</span>}
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label htmlFor="smtp_user">Usuário</label>
                <input id="smtp_user" type="text" autoComplete="off" {...register('smtp_user')} />
                {errors.smtp_user && <span className="field-error">{errors.smtp_user.message}</span>}
              </div>
              <div className="form-group">
                <label htmlFor="smtp_password">Senha</label>
                <input id="smtp_password" type="password" autoComplete="off" {...register('smtp_password')} />
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="smtp_from_name">Nome do remetente</label>
              <input id="smtp_from_name" type="text" placeholder="Minha Loja" {...register('smtp_from_name')} />
            </div>

            <div className="switch-row">
              <label htmlFor="email_ativo">Envio de e-mail ativo</label>
              <label className="switch">
                <input id="email_ativo" type="checkbox" {...register('email_ativo')} />
                <span className="slider" />
              </label>
            </div>
          </div>

          <div className="form-actions">
            {integracoes?.id && (
              <button
                type="button"
                className="btn btn-secondary"
                onClick={handleRemover}
                disabled={remover.isPending}
              >
                <FiTrash2 /> Voltar ao padrão global
              </button>
            )}
            <button type="submit" className="btn btn-primary" disabled={salvar.isPending}>
              <FiSave /> {salvar.isPending ? 'Salvando...' : 'Salvar integrações'}
            </button>
          </div>
        </form>
      )}
    </div>
  );
};

export default IntegracoesPage;
