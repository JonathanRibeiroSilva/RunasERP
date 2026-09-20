"""
Service de Loja Online (E-commerce).
Gerencia checkout e pedidos online.
"""
from typing import Optional, List
from datetime import datetime, timezone
from uuid import UUID
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
import structlog
import httpx
import secrets
import string

from models.venda import StatusVenda, FormaPagamento, TipoEntrega
from schemas.loja import (
    CheckoutRequest,
    CheckoutResponse,
    PedidoClienteResumido,
    RastreamentoPedido
)
from schemas.venda import (
    VendaCreate,
    ItemVendaCreate
)
from services.carrinho_service import CarrinhoService
from services.venda_service import VendaService
from services.reserva_temporaria_service import ReservaTemporariaService
from services.entrega_service import EntregaService
from services.cliente_validacao_service import ClienteValidacaoService
from services.mercadopago_service import MercadoPagoService
from services.historico_status_service import HistoricoStatusService
from services.notificacao_service import NotificacaoService
from services.cache_service import CacheService
from services.email_service import enviar_email_credenciais
from repositories.venda_repository import VendaRepository
from utils.tenant import get_empresa_slug_by_id
from config import settings

log = structlog.get_logger()


def _utc(dt: Optional[datetime]) -> Optional[datetime]:
    """
    Marca um datetime ingênuo (mas armazenado em UTC) como timezone-aware.

    As colunas de data do banco usam `datetime.utcnow()` (naive). Sem o tzinfo, o
    Pydantic serializa sem sufixo de fuso ("Z"/"+00:00") e o frontend (`new Date(...)`)
    interpreta o valor como hora local do navegador — deslocando a exibição em até
    3h para usuários no fuso do Brasil.
    """
    if dt is None:
        return None
    return dt.replace(tzinfo=timezone.utc)


def gerar_senha_temporaria(tamanho: int = 8) -> str:
    """Gera uma senha temporária aleatória."""
    caracteres = string.ascii_letters + string.digits
    return ''.join(secrets.choice(caracteres) for _ in range(tamanho))


class LojaService:
    """Service para operações de loja online."""
    
    @staticmethod
    async def processar_checkout(
        db: AsyncSession,
        sessao_id: str,
        empresa_id: int,
        data: CheckoutRequest
    ) -> CheckoutResponse:
        """
        Processa checkout completo: converte carrinho em venda.
        
        Fluxo completo:
        1. Obtém e valida carrinho do Redis
        2. Valida cliente (existente ou convidado)
        3. Se cliente cadastrado com FIADO, verifica permite_fiado_online
        4. Calcula taxa de entrega (se DELIVERY)
        5. Valida estoque com reserva temporária (15min - TTL padrão do carrinho)
        6. Cria venda com status apropriado (PEDIDO ou PENDENTE_PAGAMENTO)
        7. Se pagamento online, cria preferência Mercado Pago
        8. Registra histórico de status
        9. Envia notificação WhatsApp
        10. Libera reservas temporárias do carrinho
        11. Limpa carrinho
        12. Retorna dados da venda
        """
        try:
            # 🔍 DEBUG: Log inicial do checkout
            log.info(
                "🔍 DEBUG: Iniciando checkout",
                sessao_id=sessao_id,
                empresa_id=empresa_id,
                cliente_id=str(data.cliente_id) if data.cliente_id else None,
                tem_cliente_novo=bool(data.cliente_novo),
                tipo_entrega=data.tipo_entrega.value,
                formas_pagamento=[p.forma_pagamento.value for p in data.pagamentos]
            )
            
            # 1. Obter carrinho
            carrinho = await CarrinhoService.obter_ou_criar_carrinho(sessao_id, empresa_id)
            
            # 🔍 DEBUG: Log do carrinho obtido
            log.info(
                "🔍 DEBUG: Carrinho obtido do Redis",
                sessao_id=sessao_id,
                carrinho_vazio=not carrinho.itens,
                quantidade_itens=len(carrinho.itens),
                subtotal=float(carrinho.subtotal) if carrinho.itens else 0,
                criado_em=str(carrinho.criado_em),
                atualizado_em=str(carrinho.atualizado_em)
            )
            
            if not carrinho.itens:
                log.error(
                    "❌ DEBUG: Carrinho vazio no checkout",
                    sessao_id=sessao_id,
                    empresa_id=empresa_id
                )
                raise ValueError("Carrinho está vazio")
            
            # 2. Determinar e validar cliente
            cliente_id = data.cliente_id
            cliente_info = None
            senha_temporaria = None
            access_token = None
            conta_criada = False

            # 2.1 Cliente convidado (guest)
            if data.cliente_novo and not cliente_id:
                # Validar dados do cliente convidado
                valido, cliente_validado, erros = ClienteValidacaoService.validar_cliente_convidado(
                    nome=data.cliente_novo.nome,
                    telefone=data.cliente_novo.telefone,
                    email=data.cliente_novo.email if data.cliente_novo.email else None,
                    cpf=data.cliente_novo.cpf if data.cliente_novo.cpf else None
                )
                
                if not valido:
                    raise ValueError(f"Dados inválidos: {'; '.join(erros)}")
                
                cliente_info = {
                    'nome': cliente_validado['nome'],
                    'telefone': cliente_validado['telefone'],
                    'email': cliente_validado.get('email'),
                    'cpf': cliente_validado.get('cpf')
                }
                
                log.info(
                    "checkout_cliente_convidado",
                    nome=cliente_info['nome'],
                    telefone_masked=cliente_info['telefone'][:8] + "****"
                )
                
                # 2.1.1 Se marcou "criar conta", criar cliente e autenticação
                if data.criar_conta and cliente_info.get('email'):
                    try:
                        log.info("checkout_iniciando_criacao_conta", email=cliente_info['email'])
                        
                        # Gerar senha temporária
                        senha_temporaria = gerar_senha_temporaria(8)
                        
                        # 1. Criar cliente no serviço de clientes
                        async with httpx.AsyncClient() as client:
                            cliente_payload = {
                                "empresa_id": empresa_id,
                                "nome": cliente_info['nome'],
                                "cpf": cliente_info['cpf'],
                                "telefone": cliente_info['telefone'],
                                "email": cliente_info['email']
                            }
                            
                            response = await client.post(
                                f"{settings.CLIENTES_URL}/clientes",
                                json=cliente_payload,
                                headers={"X-Empresa-Id": str(empresa_id)},
                                timeout=10.0
                            )
                            
                            if response.status_code == 201:
                                cliente_criado = response.json()
                                cliente_id = UUID(cliente_criado['id'])
                                
                                log.info(
                                    "checkout_cliente_criado",
                                    cliente_id=str(cliente_id),
                                    email=cliente_info['email']
                                )
                                
                                # 2. Criar autenticação no API Gateway
                                from passlib.context import CryptContext
                                pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
                                # Bcrypt limita senhas a 72 bytes - truncar se necessário
                                senha_hash = pwd_context.hash(senha_temporaria[:72])
                                
                                auth_payload = {
                                    "email": cliente_info['email'],
                                    "senha_hash": senha_hash,
                                    "cliente_id": str(cliente_id),
                                    "empresa_id": empresa_id
                                }
                                
                                auth_response = await client.post(
                                    f"{settings.API_GATEWAY_URL}/auth/cliente/registrar-interno",
                                    json=auth_payload,
                                    timeout=10.0
                                )
                                
                                if auth_response.status_code in [200, 201]:
                                    # 3. Gerar token JWT para o cliente
                                    from datetime import datetime, timedelta
                                    from jose import jwt
                                    
                                    now = datetime.utcnow()
                                    expire = now + timedelta(minutes=30)
                                    
                                    token_payload = {
                                        "sub": str(cliente_id),
                                        "role": "CLIENTE",
                                        "user_type": "cliente",
                                        "empresa_id": empresa_id,
                                        "exp": int(expire.timestamp()),
                                        "iat": int(now.timestamp())
                                    }
                                    
                                    access_token = jwt.encode(
                                        token_payload,
                                        settings.SECRET_KEY,
                                        algorithm=settings.ALGORITHM
                                    )
                                    
                                    conta_criada = True
                                    
                                    # 4. Enviar email com credenciais (não bloquear checkout se falhar)
                                    try:
                                        # Buscar nome da empresa para o email
                                        empresa_response = await client.get(
                                            f"{settings.CLIENTES_URL}/../empresas/empresas/{empresa_id}",
                                            headers={"X-Empresa-Id": str(empresa_id)},
                                            timeout=5.0
                                        )
                                        empresa_nome = "Loja Online"
                                        empresa_slug = None
                                        if empresa_response.status_code == 200:
                                            empresa_data = empresa_response.json()
                                            empresa_nome = empresa_data.get('nome_fantasia') or empresa_data.get('razao_social', 'Loja Online')
                                            empresa_slug = empresa_data.get('slug')

                                        await enviar_email_credenciais(
                                            to_email=cliente_info['email'],
                                            senha_temporaria=senha_temporaria,
                                            empresa_nome=empresa_nome,
                                            empresa_slug=empresa_slug,
                                            empresa_id=empresa_id
                                        )
                                        log.info("checkout_email_credenciais_enviado", email=cliente_info['email'])
                                    except Exception as e:
                                        log.warning("checkout_erro_enviar_email", error=str(e))
                                    
                                    log.info(
                                        "checkout_conta_criada_com_sucesso",
                                        cliente_id=str(cliente_id),
                                        email=cliente_info['email']
                                    )
                                else:
                                    log.error(
                                        "checkout_erro_criar_auth",
                                        status=auth_response.status_code,
                                        error=auth_response.text
                                    )
                            else:
                                log.error(
                                    "checkout_erro_criar_cliente",
                                    status=response.status_code,
                                    error=response.text
                                )
                    
                    except Exception as e:
                        log.error("checkout_erro_criar_conta", error=str(e), exc_info=True)
                        # Não falhar o checkout por erro na criação de conta
                        # Cliente pode criar conta manualmente depois
            
            # 2.2 Cliente cadastrado
            elif cliente_id:
                # Buscar cliente no serviço de clientes
                cliente_info = await VendaService.verificar_cliente_existe(empresa_id, cliente_id)
                if not cliente_info:
                    raise ValueError("Cliente não encontrado ou inválido")
                
                # Se tem FIADO nos pagamentos, verificar permite_fiado_online
                tem_fiado = any(
                    p.forma_pagamento == FormaPagamento.FIADO 
                    for p in data.pagamentos
                )
                
                if tem_fiado and not cliente_info.get('permite_fiado_online', False):
                    raise ValueError(
                        "Cliente não autorizado para compras fiadas online. "
                        "Entre em contato com a loja."
                    )
            
            # 3. Calcular taxa de entrega
            valor_frete = Decimal('0.0')
            if data.tipo_entrega == TipoEntrega.DELIVERY:
                if not data.endereco_entrega:
                    raise ValueError("Endereço de entrega obrigatório para DELIVERY")
                
                # Calcular taxa via EntregaService
                valor_frete = await EntregaService.calcular_taxa_entrega(
                    db,
                    empresa_id,
                    data.endereco_entrega.cep,
                    data.endereco_entrega.bairro
                )
            
            # 4. Validar estoque e recriar reservas temporárias (15min - TTL padrão)
            # Liberar reservas temporárias do carrinho (15min) e recriar reservas (15min)
            for item in carrinho.itens:
                # Liberar reserva do carrinho
                await ReservaTemporariaService.liberar_reserva(
                    db,
                    empresa_id,
                    item.produto_id,
                    sessao_id,
                    item.variante_id
                )
                
                # Calcular estoque disponível
                disponivel = await ReservaTemporariaService.calcular_disponivel(
                    db,
                    empresa_id,
                    item.produto_id,
                    item.variante_id
                )
                
                if disponivel < item.quantidade:
                    raise ValueError(
                        f"Estoque insuficiente para {item.descricao_produto}. "
                        f"Disponível: {disponivel}, Solicitado: {item.quantidade}"
                    )
                
                # Reservar novamente (15min padrão - não suporta TTL customizado)
                sucesso, disp, erro = await ReservaTemporariaService.reservar(
                    db,
                    empresa_id,
                    item.produto_id,
                    item.quantidade,
                    sessao_id,
                    item.variante_id
                )
                
                if not sucesso:
                    raise ValueError(erro or f"Falha ao reservar {item.descricao_produto}")
            
            # 5. Calcular total dos pagamentos
            total_pagamentos = sum(p.valor for p in data.pagamentos)
            subtotal_carrinho = carrinho.subtotal + valor_frete
            
            if total_pagamentos < subtotal_carrinho:
                raise ValueError(
                    f"Total dos pagamentos (R$ {total_pagamentos}) é menor que o total do pedido (R$ {subtotal_carrinho})"
                )
            
            # 6. Converter itens do carrinho para ItemVendaCreate.
            # O preço do carrinho não vai junto: criar_venda relê o catálogo, a mesma
            # fonte de onde o carrinho tirou o preço. O que muda é o instante da
            # leitura — preço alterado com o carrinho aberto passa a valer o de agora.
            itens_venda = [
                ItemVendaCreate(
                    produto_id=item.produto_id,
                    variante_id=item.variante_id,
                    quantidade=item.quantidade,
                    codigo_produto=item.codigo_produto,  # 🔧 CORREÇÃO: Incluir código
                    descricao_produto=item.descricao_produto  # 🔧 CORREÇÃO: Incluir descrição
                )
                for item in carrinho.itens
            ]
            
            # 7. Determinar status inicial
            tem_pagamento_online = any(
                p.forma_pagamento in [FormaPagamento.PIX, FormaPagamento.DEBITO, FormaPagamento.CREDITO]
                for p in data.pagamentos
            )
            
            status_inicial = StatusVenda.PENDENTE_PAGAMENTO if tem_pagamento_online else StatusVenda.PEDIDO
            
            # 8. Criar venda
            venda_data = VendaCreate(
                empresa_id=empresa_id,
                cliente_id=cliente_id,
                tipo_entrega=data.tipo_entrega,
                observacao=data.observacao,
                itens=itens_venda,
                desconto_tipo=None,
                desconto_valor=Decimal('0.0')
            )
            
            venda = await VendaService.criar_venda(db, empresa_id, venda_data)
            
            # 8.1 Atualizar campos adicionais da venda
            updates = {
                'status': status_inicial.value,
                'valor_frete': valor_frete,
                'sessao_carrinho_id': sessao_id  # 🔑 Salvar sessao_id para limpar carrinho depois
            }
            
            # Se cliente convidado, salvar dados
            if cliente_info and not cliente_id:
                updates.update({
                    'cliente_convidado_nome': cliente_info['nome'],
                    'cliente_convidado_telefone': cliente_info['telefone'],
                    'cliente_convidado_email': cliente_info.get('email'),
                    'cliente_convidado_cpf': cliente_info.get('cpf')
                })
            
            # Se DELIVERY, salvar endereço
            if data.tipo_entrega == TipoEntrega.DELIVERY and data.endereco_entrega:
                updates.update({
                    'endereco_logradouro': data.endereco_entrega.logradouro,
                    'endereco_numero': data.endereco_entrega.numero,
                    'endereco_complemento': data.endereco_entrega.complemento,
                    'endereco_bairro': data.endereco_entrega.bairro,
                    'endereco_cidade': data.endereco_entrega.cidade,
                    'endereco_estado': data.endereco_entrega.estado,
                    'endereco_cep': data.endereco_entrega.cep
                })
            
            venda = await VendaRepository.atualizar(
                db,
                empresa_id,
                venda.id,
                **updates
            )
            
            # 9. Registrar histórico de status
            await HistoricoStatusService.registrar_mudanca(
                db,
                venda.id,
                None,  # Status anterior (primeira mudança)
                status_inicial.value,
                None,  # Sistema
                f"Pedido criado via loja online com {'pagamento online pendente' if tem_pagamento_online else 'pagamento offline'}"
            )
            
            # 10. Se pagamento online, criar preferência Mercado Pago
            mercadopago_init_point = None
            if tem_pagamento_online:
                pagamento_online = next(
                    p for p in data.pagamentos
                    if p.forma_pagamento in [FormaPagamento.PIX, FormaPagamento.DEBITO, FormaPagamento.CREDITO]
                )
                
                try:
                    # Obter slug da empresa dinamicamente (multi-tenant).
                    # Sem fallback fixo: um slug de outra loja geraria back_urls/webhook do
                    # tenant errado. Falha aqui cai no except abaixo — a venda fica
                    # PENDENTE_PAGAMENTO e o cliente usa o retry-payment.
                    empresa_slug = await get_empresa_slug_by_id(db, empresa_id)
                    if not empresa_slug:
                        raise ValueError(f"Slug não encontrado para empresa_id={empresa_id}")
                    
                    # Buscar venda completa com itens para criar preferência
                    venda_completa = await VendaRepository.buscar_por_id(
                        db,
                        empresa_id,
                        venda.id,
                        com_relacionamentos=True
                    )
                    
                    preferencia_id, init_point, sandbox_init_point, erro = await MercadoPagoService.criar_preferencia(
                        db=db,
                        venda=venda_completa,
                        empresa_id=empresa_id,
                        empresa_slug=empresa_slug
                    )
                    
                    if erro:
                        log.error("erro_mercadopago", venda_id=str(venda.id), erro=erro)

                    if preferencia_id and init_point:
                        # Checkout Pro always redirects to init_point. With a Mercado Pago
                        # test user the preference is already a TEST transaction (the
                        # account owns it), so the regular checkout accepts test cards.
                        # The legacy sandbox_init_point (sandbox.mercadopago.com.br) is
                        # deprecated: card payments are never created there, leaving the
                        # merchant_order at payment_required with 0 payments. APP_USR
                        # (test user or live) uses the same init_point for both environments.
                        mercadopago_init_point = init_point

                        await VendaRepository.atualizar(
                            db,
                            empresa_id,
                            venda.id,
                            mercadopago_preference_id=preferencia_id
                        )

                        log.info(
                            "mercadopago_checkout_url_definida",
                            venda_id=str(venda.id),
                            checkout_url_tipo="init_point"
                        )

                except Exception as e:
                    # Não falhar o checkout por erro no Mercado Pago: a venda fica
                    # PENDENTE_PAGAMENTO e o job de timeout a cancela se não for paga.
                    log.error(
                        "erro_criar_preferencia_mercadopago",
                        venda_id=str(venda.id),
                        error=str(e),
                        error_type=type(e).__name__,
                        exc_info=True
                    )
            
            # 11. Enviar notificação WhatsApp (não bloquear checkout se falhar)
            try:
                telefone = None
                if cliente_info:
                    telefone = cliente_info.get('telefone')
                
                if telefone:
                    await NotificacaoService.enviar_confirmacao_pedido(
                        telefone,
                        venda.numero_venda,
                        venda.valor_total,
                        venda.tipo_entrega,
                        empresa_id=empresa_id
                    )
            except Exception as e:
                log.warning(
                    "erro_enviar_notificacao_checkout",
                    venda_id=str(venda.id),
                    error=str(e)
                )
            
            # 12. Limpar carrinho APENAS se pagamento offline
            # Para pagamento online, carrinho só é limpo após confirmação do webhook
            
            # 🔍 DEBUG: Verificar estado do carrinho ANTES da decisão
            log.info(
                "🔍 DEBUG: Estado do carrinho antes da limpeza",
                sessao_id=sessao_id,
                venda_id=str(venda.id),
                tem_pagamento_online=tem_pagamento_online,
                quantidade_itens_carrinho=len(carrinho.itens),
                subtotal_carrinho=float(carrinho.subtotal)
            )
            
            if not tem_pagamento_online:
                await CarrinhoService.limpar_carrinho(sessao_id, empresa_id)
                log.info(
                    "✅ Carrinho limpo - pagamento offline",
                    sessao_id=sessao_id,
                    venda_id=str(venda.id)
                )
            else:
                log.info(
                    "⏸️ Carrinho MANTIDO - aguardando pagamento online",
                    sessao_id=sessao_id,
                    venda_id=str(venda.id),
                    sessao_carrinho_id_salvo=updates.get('sessao_carrinho_id'),
                    mensagem="Carrinho será limpo após confirmação do pagamento via webhook"
                )
                
                # 🔍 DEBUG: Verificar se carrinho ainda existe no Redis
                try:
                    carrinho_pos_checkout = await CarrinhoService.obter_ou_criar_carrinho(sessao_id, empresa_id)
                    log.info(
                        "🔍 DEBUG: Carrinho após checkout (deve estar intacto)",
                        sessao_id=sessao_id,
                        existe=True,
                        quantidade_itens=len(carrinho_pos_checkout.itens),
                        subtotal=float(carrinho_pos_checkout.subtotal)
                    )
                except Exception as e:
                    log.error(
                        "❌ DEBUG: Erro ao verificar carrinho após checkout",
                        sessao_id=sessao_id,
                        erro=str(e)
                    )
            
            await db.commit()
            
            log.info(
                "checkout_processado",
                sessao_id=sessao_id,
                venda_id=str(venda.id),
                numero_venda=venda.numero_venda,
                valor_total=float(venda.valor_total),
                status=status_inicial.value,
                tem_pagamento_online=tem_pagamento_online
            )
            
            # 13. Retornar resposta
            mensagem = f"Pedido {venda.numero_venda} criado com sucesso! "
            
            if tem_pagamento_online:
                mensagem += "Complete o pagamento para confirmar seu pedido."
            else:
                mensagem += "Aguarde a confirmação do pagamento."
            
            response = CheckoutResponse(
                venda_id=venda.id,
                numero_venda=venda.numero_venda,
                status=status_inicial.value,
                valor_total=venda.valor_total,
                mercadopago_init_point=mercadopago_init_point,
                mensagem=mensagem
            )
            
            # Adicionar dados de autenticação se conta foi criada
            if conta_criada and access_token and cliente_id:
                response.access_token = access_token
                response.cliente_id = cliente_id
                response.conta_criada = True
                response.mensagem += " Sua conta foi criada! Verifique seu email para a senha de acesso."
            
            return response
            
        except ValueError:
            await db.rollback()
            raise
        except Exception as e:
            await db.rollback()
            log.error("erro_processar_checkout", error=str(e))
            raise
    
    @staticmethod
    async def listar_pedidos_cliente(
        db: AsyncSession,
        empresa_id: int,
        cliente_id: UUID,
        skip: int = 0,
        limit: int = 20
    ) -> List[PedidoClienteResumido]:
        """
        Lista pedidos de um cliente específico (área do cliente).
        """
        vendas, _ = await VendaService.listar_vendas(
            db,
            empresa_id=empresa_id,
            cliente_id=cliente_id,
            skip=skip,
            limit=limit
        )
        
        pedidos = []
        for venda in vendas:
            pedidos.append(
                PedidoClienteResumido(
                    id=venda.id,
                    numero_venda=venda.numero_venda,
                    data_pedido=_utc(venda.data_pedido),
                    status=venda.status.value,
                    valor_total=venda.valor_total,
                    quantidade_itens=len(venda.itens)
                )
            )
        
        return pedidos
    
    @staticmethod
    async def rastrear_pedido(
        db: AsyncSession,
        empresa_id: int,
        numero_venda: str
    ) -> Optional[RastreamentoPedido]:
        """
        Rastreia pedido pelo número da venda.
        Retorna histórico completo e próxima etapa esperada.
        
        Usa dados do `historico_status_venda` para timeline completa.
        """
        from services.historico_status_service import HistoricoStatusService
        
        # Buscar venda
        venda = await VendaRepository.buscar_por_numero(
            db,
            empresa_id,
            numero_venda
        )
        
        if not venda:
            return None
        
        # Buscar histórico de status
        historico_db = await HistoricoStatusService.listar_por_venda(db, venda.id)
        
        # Montar timeline do histórico
        historico = []
        
        for h in historico_db:
            historico.append({
                "etapa": h.status_novo,
                "descricao": h.observacao or LojaService._get_descricao_status(h.status_novo),
                "data": _utc(h.alterado_em).isoformat(),
                "concluido": True,
                "alterado_por": "sistema" if not h.alterado_por else "usuario"
            })
        
        # Se não tem histórico, usar dados das datas da venda (backward compatibility)
        if not historico:
            historico = LojaService._montar_historico_legado(venda)
        
        # Determinar próxima etapa
        proxima_etapa = None
        previsao_entrega = None
        
        if venda.status == StatusVenda.PEDIDO.value:
            proxima_etapa = "Aguardando confirmação de pagamento"
        elif venda.status == StatusVenda.PENDENTE_PAGAMENTO.value:
            proxima_etapa = "Aguardando pagamento online (5 minutos)"
        elif venda.status == StatusVenda.CONFIRMADA.value:
            proxima_etapa = "Seu pedido será separado em breve"
        elif venda.status == StatusVenda.SEPARADA.value:
            if venda.tipo_entrega == "DELIVERY":
                proxima_etapa = "Seu pedido está pronto para envio"
                previsao_entrega = "Entrega em até 2 dias úteis"
            else:
                proxima_etapa = "Seu pedido está pronto para retirada"
        elif venda.status == StatusVenda.ENTREGUE.value:
            proxima_etapa = "Aguardando confirmação final"
        elif venda.status == StatusVenda.FINALIZADA.value:
            proxima_etapa = "Pedido concluído"
        elif venda.status == StatusVenda.CANCELADA.value:
            proxima_etapa = "Pedido cancelado"
            if venda.motivo_cancelamento:
                proxima_etapa += f" - {venda.motivo_cancelamento}"
        elif venda.status == StatusVenda.REEMBOLSADA.value:
            proxima_etapa = "Pedido reembolsado"
        
        return RastreamentoPedido(
            numero_venda=venda.numero_venda,
            status_atual=venda.status,
            data_pedido=_utc(venda.data_pedido),
            data_confirmacao=_utc(venda.data_confirmacao),
            data_separacao=_utc(venda.data_separacao),
            data_entregue=_utc(venda.data_entregue),
            data_finalizada=_utc(venda.data_finalizada),
            data_cancelada=_utc(venda.data_cancelada),
            tipo_entrega=venda.tipo_entrega,
            valor_total=venda.valor_total,
            historico=historico,
            proxima_etapa=proxima_etapa,
            previsao_entrega=previsao_entrega
        )
    
    @staticmethod
    def _get_descricao_status(status: str) -> str:
        """Retorna descrição amigável do status."""
        descricoes = {
            StatusVenda.PEDIDO.value: "Pedido criado",
            StatusVenda.PENDENTE_PAGAMENTO.value: "Aguardando pagamento online",
            StatusVenda.CONFIRMADA.value: "Pagamento confirmado",
            StatusVenda.SEPARADA.value: "Pedido separado",
            StatusVenda.EM_ENTREGA.value: "Pedido em entrega",
            StatusVenda.ENTREGUE.value: "Pedido entregue/retirado",
            StatusVenda.FINALIZADA.value: "Pedido finalizado",
            StatusVenda.CANCELADA.value: "Pedido cancelado",
            StatusVenda.REEMBOLSADA.value: "Pedido reembolsado"
        }
        return descricoes.get(status, status)
    
    @staticmethod
    def _montar_historico_legado(venda) -> list:
        """Monta histórico usando datas da venda (backward compatibility)."""
        historico = []
        
        if venda.data_pedido:
            historico.append({
                "etapa": "PEDIDO",
                "descricao": "Pedido criado",
                "data": _utc(venda.data_pedido).isoformat(),
                "concluido": True,
                "alterado_por": "sistema"
            })
        
        if venda.data_confirmacao:
            historico.append({
                "etapa": "CONFIRMADA",
                "descricao": "Pagamento confirmado",
                "data": _utc(venda.data_confirmacao).isoformat(),
                "concluido": True,
                "alterado_por": "sistema"
            })
        
        if venda.data_separacao:
            historico.append({
                "etapa": "SEPARADA",
                "descricao": "Pedido separado",
                "data": _utc(venda.data_separacao).isoformat(),
                "concluido": True,
                "alterado_por": "sistema"
            })
        
        if venda.data_entregue:
            historico.append({
                "etapa": "ENTREGUE",
                "descricao": "Pedido entregue/retirado",
                "data": _utc(venda.data_entregue).isoformat(),
                "concluido": True,
                "alterado_por": "sistema"
            })
        
        if venda.data_finalizada:
            historico.append({
                "etapa": "FINALIZADA",
                "descricao": "Pedido finalizado",
                "data": _utc(venda.data_finalizada).isoformat(),
                "concluido": True,
                "alterado_por": "sistema"
            })
        
        if venda.data_cancelada:
            descricao = "Pedido cancelado"
            if venda.motivo_cancelamento:
                descricao += f": {venda.motivo_cancelamento}"
            
            historico.append({
                "etapa": "CANCELADA",
                "descricao": descricao,
                "data": _utc(venda.data_cancelada).isoformat(),
                "concluido": True,
                "alterado_por": "sistema"
            })
        
        return historico
