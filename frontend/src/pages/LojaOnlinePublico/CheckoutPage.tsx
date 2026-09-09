import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { FiArrowLeft, FiUser, FiTruck, FiCreditCard, FiCheck, FiAlertCircle, FiLogIn, FiUserPlus } from 'react-icons/fi';
import axios from 'axios';
import { useCarrinho } from '@/hooks/useCarrinho';
import MaskedInput from '@/components/common/MaskedInput/MaskedInput';
import { validateCPF, validateEmail, validatePhone, validateCEP, validateRequired } from '@/utils/validators';
import { unmask, maskCurrency } from '@/utils/masks';
import { Toast } from '@/utils/toast';
import { logCheckoutError, isRetryableError, extractErrorMessage, sleep } from '@/utils/errorLogger';
import './CheckoutPage.scss';

// API Configuration
const apiPublica = axios.create({
  baseURL: '/api',
  timeout: 30000, // 30 segundos
  headers: { 'Content-Type': 'application/json' },
  withCredentials: true  // ✅ CRITICAL: Envia cookies HTTP-only em todas as requisições
});

// Interceptor para tratar timeout e erros de conexão
apiPublica.interceptors.response.use(
  response => response,
  error => {
    if (error.code === 'ECONNABORTED') {
      Toast.error('Conexão lenta. Por favor, tente novamente.');
    } else if (!error.response) {
      Toast.error('Erro de conexão. Verifique sua internet.');
    }
    return Promise.reject(error);
  }
);

// Types - Checkout Form Data Structures
interface ClienteNovo {
  nome: string;
  telefone: string;
  email?: string;
  cpf?: string;
}

interface Endereco {
  cep: string;
  logradouro: string;
  numero: string;
  complemento?: string;
  bairro: string;
  cidade: string;
  estado: string;
}

interface Pagamento {
  forma_pagamento: 'PIX' | 'DEBITO' | 'CREDITO' | 'DINHEIRO' | 'FIADO';
  valor: number;
}

// Step navigation type
type TipoEntrega = 'RETIRADA' | 'DELIVERY';
type Step = 1 | 2 | 3;
type ModoCheckout = 'selecao' | 'login' | 'guest';

// Interface para dados completos do cliente autenticado
interface Cliente {
  id: string;
  empresa_id: number;
  nome: string;
  cpf: string | null;
  telefone: string | null;
  email: string;
  limite_credito: number;
  credito_disponivel: number;
  bloqueado: boolean;
  ativo: boolean;
  criado_em: string;
}

const CheckoutPage = () => {
  const { empresaSlug } = useParams<{ empresaSlug: string }>();
  const navigate = useNavigate();
  const { carrinho, loading: carrinhoLoading, limparCarrinho, carregarCarrinho } = useCarrinho({ empresaSlug });

  // Modo de checkout - GUEST DESABILITADO TEMPORARIAMENTE
  // TODO: Reabilitar guest checkout após implementar fluxo completo de recuperação
  const [modoCheckout, setModoCheckout] = useState<ModoCheckout>('login');
  const [criarConta, setCriarConta] = useState(false);

  // Login
  const [loginEmail, setLoginEmail] = useState('');
  const [loginSenha, setLoginSenha] = useState('');
  const [fazendoLogin, setFazendoLogin] = useState(false);

  // Registro
  const [mostrarRegistro, setMostrarRegistro] = useState(false);
  const [registroNome, setRegistroNome] = useState('');
  const [registroEmail, setRegistroEmail] = useState('');
  const [registroSenha, setRegistroSenha] = useState('');
  const [registroConfirmarSenha, setRegistroConfirmarSenha] = useState('');
  const [registroTelefone, setRegistroTelefone] = useState('');
  const [registroCpf, setRegistroCpf] = useState('');
  const [fazendoRegistro, setFazendoRegistro] = useState(false);

  // Estados para autenticação OAuth
  const [clienteAutenticado, setClienteAutenticado] = useState<Cliente | null>(null);
  const [carregandoCliente, setCarregandoCliente] = useState<boolean>(false);
  const [retornoOAuth, setRetornoOAuth] = useState<boolean>(false);

  // Steps
  const [currentStep, setCurrentStep] = useState<Step>(1);

  // Step 1: Dados do Cliente
  const [clienteNovo, setClienteNovo] = useState<ClienteNovo>({
    nome: '',
    telefone: '',
    email: '',
    cpf: '',
  });

  // Step 2: Entrega
  const [tipoEntrega, setTipoEntrega] = useState<TipoEntrega>('RETIRADA');
  const [endereco, setEndereco] = useState<Endereco>({
    cep: '',
    logradouro: '',
    numero: '',
    complemento: '',
    bairro: '',
    cidade: '',
    estado: '',
  });
  const [frete, setFrete] = useState<number>(0);
  const [buscandoCep, setBuscandoCep] = useState(false);

  // Step 3: Pagamento
  const [formaPagamento, setFormaPagamento] = useState<'PIX' | 'DEBITO' | 'CREDITO' | 'DINHEIRO' | 'FIADO'>('PIX');
  const [valorDinheiro, setValorDinheiro] = useState<string>('');
  const [troco, setTroco] = useState<number>(0);

  // Estados gerais
  const [finalizando, setFinalizando] = useState(false);
  const [erro, setErro] = useState('');

  // Calcular troco quando forma for DINHEIRO
  useEffect(() => {
    if (formaPagamento === 'DINHEIRO' && valorDinheiro && carrinho) {
      const valor = parseFloat(valorDinheiro.replace(',', '.'));
      const subtotalNum = parseFloat(carrinho.subtotal);
      const total = subtotalNum + frete;
      setTroco(Math.max(0, valor - total));
    } else {
      setTroco(0);
    }
  }, [valorDinheiro, formaPagamento, carrinho, frete]);

  /**
   * Detecta retorno do OAuth flow e recarrega carrinho + dados do cliente.
   * Flag 'reload_cart_after_oauth' é setada pelo GoogleCallback/MicrosoftCallback após sucesso.
   */
  useEffect(() => {
    const detectarRetornoOAuth = async () => {
      const reloadCart = sessionStorage.getItem('reload_cart_after_oauth');
      if (reloadCart === 'true') {
        
        // Remove flag para não reprocessar
        sessionStorage.removeItem('reload_cart_after_oauth');
        setRetornoOAuth(true);
        
        try {
          // Forçar reload do carrinho (mantém carrinho via cookie de sessão)
          await carregarCarrinho();
          
          // Buscar dados do cliente (reutiliza função do T2)
          await buscarDadosCliente();
          
          Toast.success('Login realizado com sucesso!');
        } catch (error) {
          Toast.error('Erro ao carregar dados. Por favor, tente novamente.');
        }
      }
    };
    
    detectarRetornoOAuth();
  }, [carregarCarrinho]); // buscarDadosCliente é estável, não precisa na dependência

  /**
   * Pré-preenche o formulário com dados do cliente autenticado.
   * Campos pré-preenchidos permanecem editáveis.
   */
  const preencherDadosCliente = (cliente: Cliente) => {
    setClienteNovo({
      nome: cliente.nome,
      telefone: cliente.telefone || '',
      email: cliente.email,
      cpf: cliente.cpf || '',
    });
  };

  /**
   * Busca dados do cliente com retry automático em caso de falha.
   * Implementa exponential backoff: 1s, 2s, 4s.
   *
   * Usa rota /clientes/me que extrai cliente_id e empresa_id do cookie de sessão
   * automaticamente no gateway. Não manda X-Empresa-Id do navegador: a Cloudflare
   * bloqueia esse header vindo de fora (regra "Headers internos do gateway" — é
   * contrato exclusivo do gateway, ver service_proxy.py) e o gateway já o
   * re-injeta sozinho a partir do cookie, então enviá-lo era redundante e
   * quebrava a chamada.
   *
   * @param maxRetries - Número máximo de tentativas (padrão: 3)
   * @returns Dados do cliente
   */
  const buscarClienteComRetry = async (
    maxRetries = 3
  ): Promise<Cliente> => {
    for (let attempt = 0; attempt < maxRetries; attempt++) {
      try {
        const response = await apiPublica.get('/clientes/me', {
          withCredentials: true  // ✅ Envia cookies HTTP-only automaticamente
        });
        return response.data;
      } catch (error: any) {
        const isLastAttempt = attempt === maxRetries - 1;
        const shouldRetry = isRetryableError(error);

        if (isLastAttempt || !shouldRetry) {
          logCheckoutError(error, {
            component: 'CheckoutPage',
            action: 'buscarClienteComRetry',
            metadata: { attempt: attempt + 1, maxRetries }
          });
          throw error;
        }

        // Exponential backoff: 1s, 2s, 4s
        const delay = 1000 * Math.pow(2, attempt);
        await sleep(delay);
      }
    }

    throw new Error('Falha após todas as tentativas');
  };

  /**
   * Busca dados do cliente autenticado e pré-preenche o formulário.
   * Usa cookies HTTP-only (token gerenciado automaticamente pelo navegador).
   */
  const buscarDadosCliente = async () => {
    // ✅ Não precisa verificar localStorage - cookies são automáticos
    // O navegador envia os cookies HTTP-only automaticamente

    setCarregandoCliente(true);
    try {
      // Buscar dados do cliente usando rota /me
      // Cookies HTTP-only são enviados automaticamente pelo navegador
      const cliente = await buscarClienteComRetry();

      setClienteAutenticado(cliente);
      preencherDadosCliente(cliente);
      setModoCheckout('guest');
      setCurrentStep(1);
    } catch (error: any) {
      // ✅ CORREÇÃO: 401 é esperado quando não está logado - não logar como erro
      if (error.response?.status === 401) {
        // Silenciosamente ignorar - usuário não está logado
        setClienteAutenticado(null);
      } else if (error.response?.status === 404) {
        // Cliente não encontrado
        setClienteAutenticado(null);
        setModoCheckout('selecao');
        Toast.error('Conta não encontrada. Por favor, faça login novamente.');
      } else {
        // Logar apenas erros reais (não 401/404)
        logCheckoutError(error, {
          component: 'CheckoutPage',
          action: 'buscarDadosCliente',
          metadata: { empresaSlug }
        });
      }
    } finally {
      setCarregandoCliente(false);
    }
  };

  // useEffect para detectar autenticação ao montar componente
  useEffect(() => {
    buscarDadosCliente();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [empresaSlug]);

  // 🔒 FORÇAR LOGIN: Redirecionar se não autenticado após tentar buscar cliente
  useEffect(() => {
    // Aguardar finalizar carregamento
    if (carregandoCliente) return;
    
    // Se não está autenticado E não está na tela de login, forçar login
    if (!clienteAutenticado && modoCheckout !== 'login') {
      Toast.info('Por favor, faça login para continuar com a compra');
      setModoCheckout('login');
    }
  }, [carregandoCliente, clienteAutenticado, modoCheckout]);

  /**
   * Detecta carrinho vazio após OAuth e redireciona para loja.
   * Previne que usuário fique preso no checkout sem produtos.
   */
  useEffect(() => {
    if (retornoOAuth && carrinho?.itens.length === 0) {
      Toast.warning('Seu carrinho está vazio. Adicione produtos para continuar.');
      setTimeout(() => {
        navigate(`/c/${empresaSlug}`);
      }, 2000);
    }
  }, [retornoOAuth, carrinho, empresaSlug, navigate]);

  /**
   * Garante que checkbox "criar conta" não seja marcada para usuários autenticados.
   * Previne tentativa de criar conta duplicada no backend.
   */
  useEffect(() => {
    if (clienteAutenticado) {
      setCriarConta(false);
    }
  }, [clienteAutenticado]);

  // Função de Login
  const fazerLogin = async () => {
    if (!loginEmail || !loginSenha) {
      Toast.error('Preencha email e senha');
      return;
    }

    setFazendoLogin(true);
    try {
      const response = await apiPublica.post(`/auth/cliente/login?empresaSlug=${empresaSlug}`, {
        email: loginEmail,
        senha: loginSenha,
      }, {
        withCredentials: true  // ✅ Recebe cookies HTTP-only
      });

      const { cliente } = response.data;

      // ✅ Backend setou cookies HTTP-only automaticamente
      // ❌ NÃO usar localStorage
      
      // Preencher dados do cliente
      setClienteNovo({
        nome: cliente.nome,
        telefone: cliente.telefone || '',
        email: cliente.email,
        cpf: cliente.cpf || '',
      });

      // Ir para step 1 (dados já preenchidos)
      setModoCheckout('guest');
      setCurrentStep(1);
      
      Toast.success(`Bem-vindo de volta, ${cliente.nome}!`);
    } catch (error: any) {
      const mensagem = error.response?.data?.detail || 'Erro ao fazer login';
      Toast.error(mensagem);
    } finally {
      setFazendoLogin(false);
    }
  };

  // Função OAuth Google
  const fazerLoginGoogle = async () => {
    setFazendoLogin(true);
    try {
      // 1. Garantir que carrinho existe (cria sessão se não existir)
      await carregarCarrinho();
      
      // 2. Aguardar um momento para cookie ser setado
      await new Promise(resolve => setTimeout(resolve, 200));
      
      const empresaResponse = await apiPublica.get(`/empresas/publico/${empresaSlug}`);
      const empresa_id = empresaResponse.data.id;
      const redirect_uri = `${window.location.origin}/auth/callback/google`;
      
      const response = await apiPublica.post('/auth/cliente/oauth/google/init', {
        redirect_uri,
        empresa_id
      });

      const { auth_url, state } = response.data;
      sessionStorage.setItem('oauth_state', state);
      sessionStorage.setItem('oauth_empresa_slug', empresaSlug);
      // Save the return URL - after login, go back to checkout
      sessionStorage.setItem('oauth_return_url', `/c/${empresaSlug}/checkout`);
      window.location.href = auth_url;
    } catch (error: any) {
      Toast.error('Erro ao iniciar login com Google');
      setFazendoLogin(false);
    }
  };

  // Função OAuth Microsoft
  const fazerLoginMicrosoft = async () => {
    setFazendoLogin(true);
    try {
      // 1. Garantir que carrinho existe (cria sessão se não existir)
      await carregarCarrinho();
      
      // 2. Aguardar um momento para cookie ser setado
      await new Promise(resolve => setTimeout(resolve, 200));
      
      const empresaResponse = await apiPublica.get(`/empresas/publico/${empresaSlug}`);
      const empresa_id = empresaResponse.data.id;
      const redirect_uri = `${window.location.origin}/auth/callback/microsoft`;
      
      const response = await apiPublica.post('/auth/cliente/oauth/microsoft/init', {
        redirect_uri,
        empresa_id
      });

      const { auth_url, state } = response.data;
      sessionStorage.setItem('oauth_state', state);
      sessionStorage.setItem('oauth_empresa_slug', empresaSlug);
      // Save the return URL - after login, go back to checkout
      sessionStorage.setItem('oauth_return_url', `/c/${empresaSlug}/checkout`);
      window.location.href = auth_url;
    } catch (error: any) {
      Toast.error('Erro ao iniciar login com Microsoft');
      setFazendoLogin(false);
    }
  };

  // Função de Registro
  const fazerRegistro = async () => {
    setErro('');
    if (!registroNome || !registroEmail || !registroSenha || !registroConfirmarSenha || !registroTelefone || !registroCpf) {
      Toast.error('Preencha todos os campos obrigatórios');
      return;
    }
    if (registroSenha !== registroConfirmarSenha) {
      Toast.error('As senhas não conferem');
      return;
    }
    if (registroSenha.length < 8 || registroSenha.length > 20) {
      Toast.error('Senha deve ter entre 8 e 20 caracteres');
      return;
    }
    if (!/[A-Z]/.test(registroSenha)) {
      Toast.error('Senha deve conter ao menos uma letra maiúscula');
      return;
    }
    if (!/[a-z]/.test(registroSenha)) {
      Toast.error('Senha deve conter ao menos uma letra minúscula');
      return;
    }
    if (!/[0-9]/.test(registroSenha)) {
      Toast.error('Senha deve conter ao menos um número');
      return;
    }
    if (!/[!@#$%^&*()_+\-=[\]{}|;:,.<>?]/.test(registroSenha)) {
      Toast.error('Senha deve conter ao menos um caractere especial');
      return;
    }
    const cpfLimpo = unmask(registroCpf);
    if (cpfLimpo.length !== 11) {
      Toast.error('CPF deve ter 11 dígitos');
      return;
    }
    const telefoneLimpo = unmask(registroTelefone);
    if (telefoneLimpo.length < 10) {
      Toast.error('Telefone inválido');
      return;
    }
    setFazendoRegistro(true);
    try {
      const empresaResponse = await apiPublica.get(`/empresas/publico/${empresaSlug}`);
      const empresa_id = empresaResponse.data.id;
      const response = await apiPublica.post('/auth/cliente/register', {
        nome: registroNome,
        email: registroEmail,
        senha: registroSenha,
        cpf: cpfLimpo,
        telefone: telefoneLimpo,
        empresa_id
      }, {
        withCredentials: true  // ✅ Recebe cookies HTTP-only
      });
      
      const { cliente } = response.data;
      
      // ✅ Backend setou cookies HTTP-only automaticamente
      // ❌ NÃO usar localStorage
      
      setClienteNovo({
        nome: cliente.nome,
        telefone: cliente.telefone || '',
        email: cliente.email,
        cpf: cliente.cpf || '',
      });
      setModoCheckout('guest');
      setCurrentStep(1);
      Toast.success(`Conta criada com sucesso! Bem-vindo, ${cliente.nome}!`);
    } catch (error: any) {
      let mensagem = 'Erro ao criar conta';
      if (error.response?.data?.detail) {
        const detail = error.response.data.detail;
        if (Array.isArray(detail)) {
          mensagem = detail.map((err: any) => err.msg || err.message).join('; ');
        } else if (typeof detail === 'string') {
          mensagem = detail;
        } else if (typeof detail === 'object') {
          mensagem = detail.msg || detail.message || JSON.stringify(detail);
        }
      }
      Toast.error(mensagem);
      setErro(mensagem);
    } finally {
      setFazendoRegistro(false);
    }
  };

  // Buscar CEP via ViaCEP
  const buscarCep = async (cep: string) => {
    const cepLimpo = cep.replace(/\D/g, '');
    if (cepLimpo.length !== 8) return;

    try {
      setBuscandoCep(true);
      const response = await fetch(`https://viacep.com.br/ws/${cepLimpo}/json/`);
      const data = await response.json();

      if (data.erro) {
        setErro('CEP não encontrado');
        return;
      }

      setEndereco((prev) => ({
        ...prev,
        cep: cepLimpo,
        logradouro: data.logradouro || '',
        bairro: data.bairro || '',
        cidade: data.localidade || '',
        estado: data.uf || '',
      }));

      // Calcular frete (simulação - backend faz o cálculo real)
      setFrete(8.0); // Valor fixo por enquanto
    } catch (error) {
      setErro('Erro ao buscar CEP');
    } finally {
      setBuscandoCep(false);
    }
  };

  // Validações por step
  const validarStep1 = (): boolean => {
    setErro('');
    
    const nomeError = validateRequired(clienteNovo.nome, 'Nome');
    if (nomeError) {
      Toast.error(nomeError);
      return false;
    }
    
    const telefoneError = validatePhone(clienteNovo.telefone);
    if (telefoneError) {
      Toast.error(telefoneError);
      return false;
    }
    
    // Email é opcional, mas se preenchido deve ser válido
    if (clienteNovo.email) {
      const emailError = validateEmail(clienteNovo.email);
      if (emailError) {
        Toast.error(emailError);
        return false;
      }
    }
    
    // CPF é opcional, mas se preenchido deve ser válido
    if (clienteNovo.cpf) {
      const cpfError = validateCPF(clienteNovo.cpf);
      if (cpfError) {
        Toast.error(cpfError);
        return false;
      }
    }
    
    return true;
  };

  const validarStep2 = (): boolean => {
    setErro('');
    
    if (tipoEntrega === 'DELIVERY') {
      const cepError = validateCEP(endereco.cep);
      if (cepError) {
        Toast.error(cepError);
        return false;
      }
      
      if (!endereco.logradouro || !endereco.numero || !endereco.bairro) {
        Toast.error('Preencha todos os campos obrigatórios do endereço');
        return false;
      }
    }
    return true;
  };

  const proximoStep = () => {
    setErro('');
    
    if (currentStep === 1 && !validarStep1()) return;
    if (currentStep === 2 && !validarStep2()) return;
    
    setCurrentStep((prev) => Math.min(3, prev + 1) as Step);
  };

  const voltarStep = () => {
    setErro('');
    setCurrentStep((prev) => Math.max(1, prev - 1) as Step);
  };

  /**
   * Atualiza cadastro do cliente autenticado com CPF/telefone preenchidos no checkout.
   * Executado antes de finalizar compra para garantir dados atualizados.
   */
  const atualizarCadastroSeNecessario = async (): Promise<boolean> => {
    if (!clienteAutenticado) return true; // Não aplicável para convidados

    // Verificar se há dados novos para atualizar
    const cpfNovo = clienteNovo.cpf && clienteNovo.cpf !== clienteAutenticado.cpf;
    const telefoneNovo = clienteNovo.telefone && clienteNovo.telefone !== clienteAutenticado.telefone;

    if (!cpfNovo && !telefoneNovo) {
      return true;
    }

    try {
      const payload: any = {};
      if (cpfNovo) payload.cpf = unmask(clienteNovo.cpf);
      if (telefoneNovo) payload.telefone = unmask(clienteNovo.telefone);

      // ✅ Usa cookies HTTP-only automaticamente — sem X-Empresa-Id manual:
      // a Cloudflare bloqueia esse header vindo do navegador (é contrato
      // exclusivo do gateway), que já o re-injeta sozinho a partir do cookie.
      const response = await apiPublica.patch(
        `/clientes/me`,  // ✅ Usa /me em vez de ID
        payload,
        {
          withCredentials: true  // ✅ Envia cookies HTTP-only
          // ❌ NÃO enviar Authorization header - cookies são automáticos
        }
      );

      // Atualizar estado local com dados do servidor
      setClienteAutenticado(response.data);

      return true;
    } catch (error: any) {
      logCheckoutError(error, {
        component: 'CheckoutPage',
        action: 'atualizarCadastroSeNecessario',
        metadata: { 
          clienteId: clienteAutenticado.id,
          cpfNovo,
          telefoneNovo
        }
      });

      if (error.response?.status === 409) {
        Toast.error('CPF já cadastrado em outra conta. Por favor, verifique.');
      } else if (error.response?.status === 400) {
        const mensagem = extractErrorMessage(error);
        Toast.error(`Dados inválidos: ${mensagem}`);
      } else if (error.response?.status === 404) {
        Toast.error('Conta não encontrada. Por favor, faça login novamente.');
      } else {
        // Não bloquear checkout em erro de atualização - apenas avisar
      }

      return true; // Permitir continuar mesmo com erro
    }
  };

  // Finalizar Compra
  const finalizarCompra = async () => {
    setErro('');
    setFinalizando(true);

    // Toast de loading
    const toastId = Toast.loading('Processando pedido...');
    
    // 🔍 DEBUG: Verificar cookies antes do checkout
    console.log('🔍 DEBUG: Cookies antes do checkout:', document.cookie);
    const cartCookie = document.cookie.split('; ').find(row => row.startsWith('cart_session_id='));
    console.log('🔍 DEBUG: Cookie cart_session_id:', cartCookie ? cartCookie.split('=')[1] : 'NÃO ENCONTRADO');

    try {
      // 1. Atualizar cadastro se necessário (para usuários autenticados)
      const atualizacaoOk = await atualizarCadastroSeNecessario();
      if (!atualizacaoOk) {
        Toast.dismiss(toastId);
        Toast.error('Erro ao atualizar seus dados. Tente novamente.');
        setFinalizando(false);
        return;
      }

      // 2. Continuar com criação da venda
      const payload: any = {
        cliente_novo: {
          nome: clienteNovo.nome,
          telefone: unmask(clienteNovo.telefone), // Remove máscara
          email: clienteNovo.email || undefined, // Não envia se vazio
          cpf: clienteNovo.cpf ? unmask(clienteNovo.cpf) : undefined, // Remove máscara
        },
        criar_conta: criarConta, // Flag para criar conta automaticamente
        tipo_entrega: tipoEntrega,
        endereco_entrega: tipoEntrega === 'DELIVERY' ? {
          cep: unmask(endereco.cep), // Remove máscara
          logradouro: endereco.logradouro,
          numero: endereco.numero,
          complemento: endereco.complemento || undefined,
          bairro: endereco.bairro,
          cidade: endereco.cidade,
          estado: endereco.estado,
        } : undefined,
        pagamentos: [
          {
            forma_pagamento: formaPagamento,
            valor: parseFloat(carrinho.subtotal) + frete,
          },
        ],
      };

      const response = await apiPublica.post(`/loja/checkout?empresaSlug=${empresaSlug}`, payload);
      const { venda_id, numero_venda, mercadopago_init_point } = response.data;

      // 🔍 DEBUG: Log da resposta do checkout
      console.log('🔍 DEBUG: Resposta do checkout:', {
        venda_id,
        numero_venda,
        tem_mercadopago_link: !!mercadopago_init_point,
        mercadopago_link: mercadopago_init_point
      });

      // Atualiza toast para sucesso
      Toast.update(toastId, 'success', 'Pedido realizado com sucesso!');

      // Se pagamento online (PIX/Cartão), redirecionar para Mercado Pago
      // Backend manterá o carrinho até webhook confirmar pagamento
      // Não precisamos fazer nada no frontend - backend gerencia tudo
      if (mercadopago_init_point) {
        console.log('🔍 DEBUG: Redirecionando para Mercado Pago');
        console.log('🔍 DEBUG: Carrinho será limpo pelo webhook após confirmação');
        
        // Redirecionar imediatamente
        window.location.href = mercadopago_init_point;
        
        return; // Importante: retornar para não executar código abaixo
      }

      // Se pagamento offline, limpar carrinho e ir para rastreamento
      await limparCarrinho();
      navigate(`/c/${empresaSlug}/pedido/${numero_venda}`, {
        state: { sucesso: true },
      });
    } catch (error: any) {
      // Log estruturado do erro
      logCheckoutError(error, {
        component: 'CheckoutPage',
        action: 'finalizarCompra',
        metadata: {
          clienteAutenticado: !!clienteAutenticado,
          tipoEntrega,
          formaPagamento,
          criarConta
        }
      });

      // Atualiza toast para erro
      Toast.dismiss(toastId);

      // Extrair mensagem de erro amigável
      const mensagemErro = extractErrorMessage(error);

      // Mensagens específicas por status code
      if (error.response?.status === 400) {
        Toast.error(`Dados inválidos: ${mensagemErro}`);
      } else if (error.response?.status === 401) {
        Toast.error('Sessão expirada. Por favor, faça login novamente.');
        // ✅ Backend limpa cookies automaticamente ao expirar
        setModoCheckout('selecao');
      } else if (error.response?.status === 404) {
        Toast.error('Recurso não encontrado. Por favor, tente novamente.');
      } else if (error.response?.status === 409) {
        Toast.error(`Conflito: ${mensagemErro}`);
      } else if (error.response?.status >= 500) {
        Toast.error('Erro no servidor. Por favor, tente novamente em alguns instantes.');
      } else {
        Toast.error(mensagemErro);
      }

      setErro(mensagemErro);
    } finally {
      setFinalizando(false);
    }
  };

  // Formatadores
  const formatarTelefone = (value: string) => {
    const limpo = value.replace(/\D/g, '');
    if (limpo.length <= 10) {
      return limpo.replace(/(\d{2})(\d{4})(\d{0,4})/, '($1) $2-$3');
    }
    return limpo.replace(/(\d{2})(\d{5})(\d{0,4})/, '($1) $2-$3');
  };

  const formatarCep = (value: string) => {
    const limpo = value.replace(/\D/g, '');
    return limpo.replace(/(\d{5})(\d{0,3})/, '$1-$2');
  };

  const formatarCpf = (value: string) => {
    const limpo = value.replace(/\D/g, '');
    return limpo.replace(/(\d{3})(\d{3})(\d{3})(\d{0,2})/, '$1.$2.$3-$4');
  };

  const formatarPreco = (valor: string | number) => {
    const valorNum = typeof valor === 'string' ? parseFloat(valor) : valor;
    return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(valorNum);
  };

  // Loading state - mostra enquanto carrega o carrinho
  if (carrinhoLoading || (!carrinho && carregandoCliente)) {
    return (
      <div className="checkout-page">
        <div className="loading-overlay">
          <div className="loading-spinner"></div>
          <p>Carregando checkout...</p>
        </div>
      </div>
    );
  }

  // Early return se carrinho vazio (mas NÃO se ainda está carregando)
  if (!carrinho || carrinho.itens.length === 0) {
    return (
      <div className="checkout-page">
        <div className="checkout-vazio">
          <div className="vazio-icon">🛒</div>
          <h2>Seu carrinho está vazio</h2>
          <p>Adicione produtos para continuar</p>
          <button onClick={() => navigate(`/c/${empresaSlug}`)}>
            Ver produtos
          </button>
        </div>
      </div>
    );
  }

  const total = parseFloat(carrinho.subtotal) + frete;

  return (
    <div className="checkout-page">
      {/* Header */}
      <header className="checkout-header">
        <button className="btn-voltar" onClick={() => navigate(`/c/${empresaSlug}/carrinho`)}>
          <FiArrowLeft /> Voltar ao carrinho
        </button>
        <h1>Finalizar Compra</h1>
      </header>

      {/* Steps Indicator - Temporariamente oculto */}
      {/* TODO: Implementar stepper em modal/drawer separado */}
      {/* <div className="steps-indicator">...</div> */}

      {erro && (
        <div className="erro-mensagem">
          <FiAlertCircle /> {erro}
        </div>
      )}

      {/* Loading overlay quando busca dados do cliente */}
      {carregandoCliente && (
        <div className="loading-overlay">
          <div className="loading-spinner"></div>
          <p>Carregando seus dados...</p>
        </div>
      )}

      <div className="checkout-container">
        {/* 🔒 GUEST CHECKOUT DESABILITADO - Apenas Login */}
        {/* Tela de seleção removida temporariamente - forçando login obrigatório */}
        
        {/* Tela de Login */}
        {modoCheckout === 'login' && !mostrarRegistro && (
          <div className="login-checkout">
            <div className="login-card">
              <div className="login-header">
                <FiUser size={40} />
                <h2>Bem-vindo de volta!</h2>
                <p>Acesse sua conta para finalizar a compra</p>
              </div>

              {/* Social Login Buttons */}
              <div className="social-login-buttons">
                <button
                  className="btn-google"
                  onClick={fazerLoginGoogle}
                  disabled={fazendoLogin}
                >
                  <svg viewBox="0 0 24 24" width="18" height="18">
                    <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                    <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                    <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                    <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                  </svg>
                  Entrar com Google
                </button>

                <button
                  className="btn-microsoft"
                  onClick={fazerLoginMicrosoft}
                  disabled={fazendoLogin}
                >
                  <svg viewBox="0 0 24 24" width="18" height="18">
                    <path fill="#f25022" d="M1 1h10v10H1z"/>
                    <path fill="#00a4ef" d="M13 1h10v10H13z"/>
                    <path fill="#7fba00" d="M1 13h10v10H1z"/>
                    <path fill="#ffb900" d="M13 13h10v10H13z"/>
                  </svg>
                  Entrar com Microsoft
                </button>
              </div>

              <div className="divider">
                <span>ou use seu e-mail</span>
              </div>

              <div className="form-group">
                <label>E-mail *</label>
                <input
                  type="email"
                  value={loginEmail}
                  onChange={(e) => setLoginEmail(e.target.value)}
                  placeholder="Digite seu e-mail"
                  disabled={fazendoLogin}
                  autoComplete="email"
                />
              </div>

              <div className="form-group">
                <label>Senha *</label>
                <input
                  type="password"
                  value={loginSenha}
                  onChange={(e) => setLoginSenha(e.target.value)}
                  placeholder="Digite sua senha"
                  disabled={fazendoLogin}
                  autoComplete="current-password"
                />
              </div>

              <div className="login-actions">
                <button
                  className="btn-primary"
                  onClick={fazerLogin}
                  disabled={fazendoLogin}
                >
                  {fazendoLogin ? 'Entrando...' : 'Entrar'}
                </button>
                <button
                  className="btn-link"
                  onClick={() => setModoCheckout('selecao')}
                  disabled={fazendoLogin}
                >
                  Voltar
                </button>
              </div>

              <div className="login-footer">
                <p>
                  Não tem conta?{' '}
                  <button
                    className="btn-link-inline"
                    onClick={() => setMostrarRegistro(true)}
                  >
                    Criar conta agora
                  </button>
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Tela de Registro */}
        {modoCheckout === 'login' && mostrarRegistro && (
          <div className="login-checkout">
            <div className="login-card">
              <div className="login-header">
                <FiUserPlus size={40} />
                <h2>Criar nova conta</h2>
                <p>Preencha seus dados para se cadastrar</p>
              </div>

              <div className="form-group">
                <label>Nome completo *</label>
                <input
                  type="text"
                  value={registroNome}
                  onChange={(e) => setRegistroNome(e.target.value)}
                  placeholder="Digite seu nome completo"
                  disabled={fazendoRegistro}
                  autoComplete="name"
                />
              </div>

              <div className="form-group">
                <label>E-mail *</label>
                <input
                  type="email"
                  value={registroEmail}
                  onChange={(e) => setRegistroEmail(e.target.value)}
                  placeholder="Digite seu e-mail"
                  disabled={fazendoRegistro}
                  autoComplete="email"
                />
              </div>

              <MaskedInput
                mask="phone"
                value={registroTelefone}
                onChange={(value) => setRegistroTelefone(value)}
                onValidate={validatePhone}
                label="Telefone *"
                placeholder="Digite seu telefone"
                showValidation={true}
                required
              />

              <MaskedInput
                mask="cpf"
                value={registroCpf}
                onChange={(value) => setRegistroCpf(value)}
                onValidate={validateCPF}
                label="CPF *"
                placeholder="Digite seu CPF"
                showValidation={true}
                required
              />

              <div className="form-group">
                <label>Senha *</label>
                <input
                  type="password"
                  value={registroSenha}
                  onChange={(e) => setRegistroSenha(e.target.value)}
                  placeholder="Mínimo 8 caracteres"
                  disabled={fazendoRegistro}
                  autoComplete="new-password"
                />
                <small>
                  Deve conter: 8-20 caracteres, 1 maiúscula, 1 minúscula, 1 número e 1 caractere especial
                </small>
              </div>

              <div className="form-group">
                <label>Confirmar senha *</label>
                <input
                  type="password"
                  value={registroConfirmarSenha}
                  onChange={(e) => setRegistroConfirmarSenha(e.target.value)}
                  placeholder="Digite a senha novamente"
                  disabled={fazendoRegistro}
                  autoComplete="new-password"
                />
              </div>

              <div className="login-actions">
                <button
                  className="btn-primary"
                  onClick={fazerRegistro}
                  disabled={fazendoRegistro}
                >
                  {fazendoRegistro ? 'Criando conta...' : 'Criar conta'}
                </button>
                <button
                  className="btn-link"
                  onClick={() => setMostrarRegistro(false)}
                  disabled={fazendoRegistro}
                >
                  Voltar para login
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Formulário - Só exibe se modo for 'guest' */}
        {modoCheckout === 'guest' && (
          <>
        <div className="checkout-form">
          {/* Step 1: Dados do Cliente */}
          {currentStep === 1 && (
            <div className="form-section">
              <h2>Seus dados</h2>
              <p className="section-description">Informe seus dados para contato</p>

              {/* Banner OAuth */}
              {clienteAutenticado && (
                <div className="oauth-info-banner">
                  <div className="banner-icon">
                    <FiCheck />
                  </div>
                  <div className="banner-content">
                    <strong>Login realizado com sucesso!</strong>
                    <p>
                      Seus dados foram preenchidos automaticamente. 
                      Você pode editá-los se desejar antes de continuar.
                    </p>
                  </div>
                </div>
              )}

              <div className={`form-group ${clienteAutenticado ? 'prefilled' : ''}`}>
                <label>Nome completo *</label>
                <input
                  type="text"
                  value={clienteNovo.nome}
                  onChange={(e) => setClienteNovo({ ...clienteNovo, nome: e.target.value })}
                  placeholder="Digite seu nome completo"
                  autoComplete="name"
                />
                {clienteAutenticado && (
                  <div className="prefilled-indicator">
                    <FiCheck />
                    <span>Dados do OAuth</span>
                  </div>
                )}
              </div>

              <MaskedInput
                mask="phone"
                value={clienteNovo.telefone}
                onChange={(value) => setClienteNovo({ ...clienteNovo, telefone: value })}
                onValidate={validatePhone}
                label="Telefone (WhatsApp) *"
                placeholder="Digite seu telefone"
                helperText="Usaremos para enviar atualizações do pedido"
                showValidation={true}
                required
              />

              <div className={`form-group ${clienteAutenticado ? 'prefilled' : ''}`}>
                <MaskedInput
                  value={clienteNovo.email || ''}
                  onChange={(value) => setClienteNovo({ ...clienteNovo, email: value })}
                  onValidate={validateEmail}
                  label="E-mail"
                  placeholder="Digite seu e-mail"
                  type="email"
                  showValidation={true}
                />
                {clienteAutenticado && (
                  <div className="prefilled-indicator">
                    <FiCheck />
                    <span>Dados do OAuth</span>
                  </div>
                )}
              </div>

              <MaskedInput
                mask="cpf"
                value={clienteNovo.cpf || ''}
                onChange={(value) => setClienteNovo({ ...clienteNovo, cpf: value })}
                onValidate={validateCPF}
                label={clienteAutenticado ? "CPF (recomendado)" : "CPF (opcional)"}
                placeholder="Digite seu CPF"
                showValidation={true}
              />

              {/* Aviso de dados opcionais recomendados */}
              {clienteAutenticado && (!clienteNovo.cpf || !clienteNovo.telefone) && (
                <div className="optional-data-warning">
                  <FiAlertCircle className="icon-warning" />
                  <div className="warning-content">
                    <strong>Recomendamos preencher estes dados</strong>
                    <p>
                      CPF e telefone ajudam na identificação em caso de problemas 
                      com a entrega e facilitam o suporte.
                    </p>
                  </div>
                </div>
              )}

              {/* Checkbox Criar Conta - DESABILITADO (apenas login obrigatório agora) */}
              {/* TODO: Reabilitar quando guest checkout for implementado */}
              {/* {!clienteAutenticado && (
                <div className="criar-conta-checkbox">
                  <label className="checkbox-label">
                    <input
                      type="checkbox"
                      checked={criarConta}
                      onChange={(e) => setCriarConta(e.target.checked)}
                    />
                    <span className="checkbox-text">
                      <strong>Criar uma conta para mim</strong>
                      <small>
                        Facilita rastreamento de pedidos e recompras rápidas. 
                        Você receberá suas credenciais por email.
                      </small>
                    </span>
                  </label>
                </div>
              )} */}

              <button className="btn-proximo" onClick={proximoStep}>
                Continuar <FiCheck />
              </button>
            </div>
          )}

          {/* Step 2: Entrega */}
          {currentStep === 2 && (
            <div className="form-section">
              <h2>Tipo de entrega</h2>

              <div className="entrega-opcoes">
                <label className={`entrega-opcao ${tipoEntrega === 'RETIRADA' ? 'selected' : ''}`}>
                  <input
                    type="radio"
                    name="entrega"
                    value="RETIRADA"
                    checked={tipoEntrega === 'RETIRADA'}
                    onChange={() => {
                      setTipoEntrega('RETIRADA');
                      setFrete(0);
                    }}
                  />
                  <div className="opcao-content">
                    <strong>Retirar no local</strong>
                    <span className="opcao-preco">Grátis</span>
                  </div>
                </label>

                <label className={`entrega-opcao ${tipoEntrega === 'DELIVERY' ? 'selected' : ''}`}>
                  <input
                    type="radio"
                    name="entrega"
                    value="DELIVERY"
                    checked={tipoEntrega === 'DELIVERY'}
                    onChange={() => setTipoEntrega('DELIVERY')}
                  />
                  <div className="opcao-content">
                    <strong>Entrega em domicílio</strong>
                    <span className="opcao-preco">
                      {frete > 0 ? formatarPreco(frete) : 'Calcular'}
                    </span>
                  </div>
                </label>
              </div>

              {tipoEntrega === 'DELIVERY' && (
                <div className="endereco-form">
                  <h3>Endereço de entrega</h3>

                  <MaskedInput
                    mask="cep"
                    value={endereco.cep}
                    onChange={(value) => {
                      setEndereco({ ...endereco, cep: value });
                      // Busca CEP quando estiver completo
                      const cleaned = unmask(value);
                      if (cleaned.length === 8) {
                        buscarCep(value);
                      }
                    }}
                    onValidate={validateCEP}
                    label="CEP *"
                    placeholder="Digite o CEP"
                    helperText={buscandoCep ? 'Buscando endereço...' : 'Preencheremos o endereço automaticamente'}
                    showValidation={true}
                    required
                  />

                  <div className="form-row">
                    <div className="form-group">
                      <label>Logradouro *</label>
                      <input
                        type="text"
                        value={endereco.logradouro}
                        onChange={(e) => setEndereco({ ...endereco, logradouro: e.target.value })}
                        placeholder="Nome da rua"
                        autoComplete="street-address"
                      />
                    </div>

                    <div className="form-group form-group-small">
                      <label>Número *</label>
                      <input
                        type="text"
                        value={endereco.numero}
                        onChange={(e) => setEndereco({ ...endereco, numero: e.target.value })}
                        placeholder="Nº"
                        autoComplete="address-line2"
                      />
                    </div>
                  </div>

                  <div className="form-group">
                    <label>Complemento</label>
                    <input
                      type="text"
                      value={endereco.complemento}
                      onChange={(e) => setEndereco({ ...endereco, complemento: e.target.value })}
                      placeholder="Apartamento, bloco, etc."
                      autoComplete="address-line3"
                    />
                  </div>

                  <div className="form-row">
                    <div className="form-group">
                      <label>Bairro *</label>
                      <input
                        type="text"
                        value={endereco.bairro}
                        onChange={(e) => setEndereco({ ...endereco, bairro: e.target.value })}
                        placeholder="Nome do bairro"
                        autoComplete="address-level3"
                      />
                    </div>

                    <div className="form-group">
                      <label>Cidade *</label>
                      <input
                        type="text"
                        value={endereco.cidade}
                        onChange={(e) => setEndereco({ ...endereco, cidade: e.target.value })}
                        placeholder="Nome da cidade"
                        autoComplete="address-level2"
                      />
                    </div>

                    <div className="form-group form-group-small">
                      <label>UF *</label>
                      <input
                        type="text"
                        value={endereco.estado}
                        onChange={(e) => setEndereco({ ...endereco, estado: e.target.value.toUpperCase() })}
                        placeholder="UF"
                        maxLength={2}
                        autoComplete="address-level1"
                      />
                    </div>
                  </div>
                </div>
              )}

              <div className="form-buttons">
                <button className="btn-voltar-step" onClick={voltarStep}>
                  <FiArrowLeft /> Voltar
                </button>
                <button className="btn-proximo" onClick={proximoStep}>
                  Continuar <FiCheck />
                </button>
              </div>
            </div>
          )}

          {/* Step 3: Pagamento */}
          {currentStep === 3 && (
            <div className="form-section">
              <h2>Forma de pagamento</h2>

              <div className="pagamento-opcoes">
                <label className={`pagamento-opcao ${formaPagamento === 'PIX' ? 'selected' : ''}`}>
                  <input
                    type="radio"
                    name="pagamento"
                    value="PIX"
                    checked={formaPagamento === 'PIX'}
                    onChange={() => setFormaPagamento('PIX')}
                  />
                  <div className="opcao-content">
                    <strong>PIX</strong>
                    <span>Pagamento instantâneo via Mercado Pago</span>
                  </div>
                </label>

                <label className={`pagamento-opcao ${formaPagamento === 'DEBITO' ? 'selected' : ''}`}>
                  <input
                    type="radio"
                    name="pagamento"
                    value="DEBITO"
                    checked={formaPagamento === 'DEBITO'}
                    onChange={() => setFormaPagamento('DEBITO')}
                  />
                  <div className="opcao-content">
                    <strong>Cartão de Débito</strong>
                    <span>Aprovação imediata</span>
                  </div>
                </label>

                <label className={`pagamento-opcao ${formaPagamento === 'CREDITO' ? 'selected' : ''}`}>
                  <input
                    type="radio"
                    name="pagamento"
                    value="CREDITO"
                    checked={formaPagamento === 'CREDITO'}
                    onChange={() => setFormaPagamento('CREDITO')}
                  />
                  <div className="opcao-content">
                    <strong>Cartão de Crédito</strong>
                    <span>Parcelamento disponível</span>
                  </div>
                </label>

                <label className={`pagamento-opcao ${formaPagamento === 'DINHEIRO' ? 'selected' : ''}`}>
                  <input
                    type="radio"
                    name="pagamento"
                    value="DINHEIRO"
                    checked={formaPagamento === 'DINHEIRO'}
                    onChange={() => setFormaPagamento('DINHEIRO')}
                  />
                  <div className="opcao-content">
                    <strong>Dinheiro</strong>
                    <span>Pagamento na entrega/retirada</span>
                  </div>
                </label>
              </div>

              {formaPagamento === 'DINHEIRO' && (
                <div className="form-group">
                  <label>Troco para quanto?</label>
                  <input
                    type="text"
                    value={valorDinheiro}
                    onChange={(e) => setValorDinheiro(e.target.value)}
                    placeholder="Digite o valor (ex: 100.00)"
                  />
                  {troco > 0 && (
                    <small className="troco-info">Troco: {formatarPreco(troco)}</small>
                  )}
                </div>
              )}

              <div className="form-buttons">
                <button className="btn-voltar-step" onClick={voltarStep}>
                  <FiArrowLeft /> Voltar
                </button>
                <button
                  className="btn-finalizar"
                  onClick={finalizarCompra}
                  disabled={finalizando}
                >
                  {finalizando ? 'Processando...' : 'Finalizar Pedido'}
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Resumo - Exibe tanto para guest quanto para login */}
        {(modoCheckout === 'guest' || modoCheckout === 'login') && (
        <div className="checkout-resumo">
          <h3>Resumo do pedido</h3>

          <div className="resumo-itens">
            {carrinho.itens.map((item) => {
              const itemKey = `${item.produto_id}-${item.variante_id || 'null'}`;
              const quantidadeNum = parseFloat(item.quantidade);
              
              return (
                <div key={itemKey} className="resumo-item">
                  <span className="item-nome">
                    {quantidadeNum}x {item.descricao_produto}
                  </span>
                  <span className="item-preco">{formatarPreco(item.subtotal)}</span>
                </div>
              );
            })}
          </div>

          <div className="resumo-totais">
            <div className="total-linha">
              <span>Subtotal</span>
              <span>{formatarPreco(carrinho.subtotal)}</span>
            </div>
            <div className="total-linha">
              <span>Frete</span>
              <span>{frete > 0 ? formatarPreco(frete) : 'Grátis'}</span>
            </div>
            <div className="total-linha total-final">
              <span>Total</span>
              <span>{formatarPreco(total)}</span>
            </div>
          </div>
        </div>
        )}
          </>
        )}
      </div>

      <footer className="loja-online-footer">
        <p>Powered by <strong>Runas ERP</strong></p>
      </footer>
    </div>
  );
};

export default CheckoutPage;
