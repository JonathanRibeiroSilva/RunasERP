import { useEffect, useMemo, useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { FiUsers, FiPlus, FiEdit2, FiTrash2 } from 'react-icons/fi';
import { toast } from 'react-toastify';
import Modal from '@/components/common/Modal/Modal';
import { getErrorMessage } from '@/services/api/axios';
import { useAuth } from '@/hooks/useAuth';
import {
  useUsuarios,
  useCriarUsuario,
  useAtualizarUsuario,
  useDesativarUsuario,
} from '@/hooks/useUsuarios';
import type { Usuario, RoleTenant } from '@/types/usuario';
import { usuarioSchema, type UsuarioFormData } from './usuarioSchema';
import './Configuracoes.scss';

const POR_PAGINA = 10;

const ROLES: Array<{ value: RoleTenant; label: string }> = [
  { value: 'ADMIN', label: 'Administrador' },
  { value: 'OPERADOR', label: 'Operador' },
];

const VAZIO: UsuarioFormData = {
  nome: '',
  email: '',
  senha: '',
  role: 'OPERADOR',
  ativo: true,
};

const UsuariosPage = () => {
  const { user } = useAuth();
  const [page, setPage] = useState(1);
  const [editando, setEditando] = useState<Usuario | null>(null);
  const [modalAberto, setModalAberto] = useState(false);
  // Erro do backend fica visível dentro do modal: um 409 de limite de plano ou de
  // "último admin ativo" precisa ser lido junto do form que o causou, não só no toast.
  const [erro, setErro] = useState<string | null>(null);

  const { data, isLoading, isError } = useUsuarios({
    skip: (page - 1) * POR_PAGINA,
    limit: POR_PAGINA,
  });

  const criar = useCriarUsuario();
  const atualizar = useAtualizarUsuario();
  const desativar = useDesativarUsuario();

  const usuarios = data?.items ?? [];
  const total = data?.total ?? 0;
  // O backend limita por usuários ATIVOS; contar os desativados travaria o
  // botão antes da hora e o 409 nunca apareceria.
  const ativos = data?.ativos ?? 0;
  const limite = data?.max_usuarios ?? null;
  const totalPaginas = Math.max(1, Math.ceil(total / POR_PAGINA));
  const noLimite = limite !== null && ativos >= limite;

  const criando = editando === null;
  const schema = useMemo(() => usuarioSchema(criando), [criando]);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<UsuarioFormData>({ resolver: zodResolver(schema), defaultValues: VAZIO });

  useEffect(() => {
    if (isError) toast.error('Erro ao carregar usuários');
  }, [isError]);

  const abrir = (usuario: Usuario | null) => {
    setEditando(usuario);
    setErro(null);
    reset(
      usuario
        ? {
            nome: usuario.nome,
            email: usuario.email,
            senha: '',
            role: usuario.role === 'ADMIN' ? 'ADMIN' : 'OPERADOR',
            ativo: usuario.ativo,
          }
        : VAZIO
    );
    setModalAberto(true);
  };

  const fechar = () => {
    setModalAberto(false);
    setEditando(null);
  };

  const onSubmit = async (form: UsuarioFormData) => {
    setErro(null);
    try {
      if (editando) {
        await atualizar.mutateAsync({
          id: editando.id,
          data: { nome: form.nome, email: form.email, role: form.role, ativo: form.ativo },
        });
        toast.success('Usuário atualizado');
      } else {
        await criar.mutateAsync({ ...form, empresa_id: user!.empresa_id });
        toast.success('Usuário criado');
      }
      fechar();
    } catch (error) {
      setErro(getErrorMessage(error, 'Erro ao salvar usuário'));
    }
  };

  const handleDesativar = (usuario: Usuario) => {
    if (!window.confirm(`Desativar o acesso de ${usuario.nome}?`)) return;
    desativar.mutate(usuario.id, {
      onSuccess: () => toast.success('Usuário desativado'),
      onError: (error) => toast.error(getErrorMessage(error, 'Erro ao desativar usuário')),
    });
  };

  return (
    <div className="page-container admin-list">
      <div className="page-header">
        <h1><FiUsers className="title-icon" /> Gerenciar Usuários</h1>
        <p className="page-description">
          Adicione, edite e gerencie os usuários do sistema e suas permissões
        </p>
      </div>

      <div className="list-header">
        <span className="list-counter">
          {limite === null ? `${ativos} usuários` : `${ativos} de ${limite} usuários`}
        </span>
        <button
          className="btn btn-primary"
          onClick={() => abrir(null)}
          disabled={noLimite}
          title={noLimite ? 'Limite do plano atingido' : 'Novo usuário'}
        >
          <FiPlus /> Novo Usuário
        </button>
      </div>

      {isLoading ? (
        <div className="empty-state">Carregando...</div>
      ) : usuarios.length === 0 ? (
        <div className="empty-state">Nenhum usuário encontrado</div>
      ) : (
        <>
          <div className="table-responsive">
            <table>
              <thead>
                <tr>
                  <th>Nome</th>
                  <th>E-mail</th>
                  <th>Papel</th>
                  <th>Status</th>
                  <th>Ações</th>
                </tr>
              </thead>
              <tbody>
                {usuarios.map((u) => (
                  <tr key={u.id} className={u.ativo ? '' : 'inactive'}>
                    <td data-label="Nome">{u.nome}</td>
                    <td data-label="E-mail">{u.email}</td>
                    <td data-label="Papel">
                      <span className={`badge ${u.role === 'ADMIN' ? 'badge-info' : 'badge-warning'}`}>
                        {u.role === 'ADMIN' ? 'Administrador' : 'Operador'}
                      </span>
                    </td>
                    <td data-label="Status">
                      <span className={`badge ${u.ativo ? 'badge-success' : 'badge-error'}`}>
                        {u.ativo ? 'Ativo' : 'Inativo'}
                      </span>
                    </td>
                    <td data-label="Ações">
                      <div className="actions-group">
                        <button className="btn btn-sm btn-outline-primary" onClick={() => abrir(u)} title="Editar">
                          <FiEdit2 />
                        </button>
                        {u.ativo && (
                          <button
                            className="btn btn-sm btn-outline-danger"
                            onClick={() => handleDesativar(u)}
                            title="Desativar"
                          >
                            <FiTrash2 />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="pagination">
            <button className="btn btn-sm btn-outline-primary" disabled={page === 1} onClick={() => setPage(page - 1)}>
              Anterior
            </button>
            <span className="page-info">Página {page} de {totalPaginas}</span>
            <button
              className="btn btn-sm btn-outline-primary"
              disabled={page === totalPaginas}
              onClick={() => setPage(page + 1)}
            >
              Próxima
            </button>
          </div>
        </>
      )}

      <Modal
        isOpen={modalAberto}
        title={editando ? 'Editar usuário' : 'Novo usuário'}
        onClose={fechar}
      >
        <form className="admin-form" onSubmit={handleSubmit(onSubmit)}>
          {erro && <div className="form-error">{erro}</div>}

          <div className="form-group">
            <label htmlFor="nome">Nome *</label>
            <input id="nome" type="text" {...register('nome')} />
            {errors.nome && <span className="field-error">{errors.nome.message}</span>}
          </div>

          <div className="form-group">
            <label htmlFor="email">E-mail *</label>
            <input id="email" type="email" {...register('email')} />
            {errors.email && <span className="field-error">{errors.email.message}</span>}
          </div>

          {criando && (
            <div className="form-group">
              <label htmlFor="senha">Senha *</label>
              <input id="senha" type="password" autoComplete="new-password" {...register('senha')} />
              {errors.senha && <span className="field-error">{errors.senha.message}</span>}
            </div>
          )}

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="role">Papel *</label>
              <select id="role" {...register('role')}>
                {ROLES.map((r) => (
                  <option key={r.value} value={r.value}>{r.label}</option>
                ))}
              </select>
            </div>
            <div className="form-group checkbox-group">
              <label htmlFor="ativo">
                <input id="ativo" type="checkbox" {...register('ativo')} /> Usuário ativo
              </label>
            </div>
          </div>

          <div className="form-actions">
            <button type="button" className="btn btn-secondary" onClick={fechar}>Cancelar</button>
            <button type="submit" className="btn btn-primary" disabled={isSubmitting}>
              {editando ? 'Salvar' : 'Criar'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};

export default UsuariosPage;
