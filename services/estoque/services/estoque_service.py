"""
Service de Estoque.
Contém a lógica de negócio para gestão de estoque.
"""
import asyncio
from datetime import datetime, date, timedelta
from typing import List, Optional, Tuple
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
import httpx
import structlog

from models.estoque import (
    TipoMovimentacao,
    StatusLote,
    Movimentacao,
    Estoque,
    BaixaVendaProcessada,
    EstornoVendaProcessado,
    EntradaNfeProcessada,
)
from utils.concorrencia import (
    MAX_TENTATIVAS_DEADLOCK,
    backoff_segundos,
    chave_ordenacao_item,
    eh_erro_transitorio,
    extrair_sqlstate,
)
from repositories.estoque_repository import (
    EstoqueRepository,
    MovimentacaoRepository,
    LoteRepository,
    InventarioRepository
)
from schemas.estoque import (
    EstoqueCreate,
    EstoqueUpdate,
    EstoqueResponse,
    EstoqueComAlerta,
    MovimentacaoCreate,
    LoteCreate,
    EntradaEstoqueRequest,
    EntradaNfeRequest,
    SaidaEstoqueRequest,
    AjusteEstoqueRequest,
    ReservaEstoqueRequest,
    LiberarReservaRequest,
    BaixaVendaRequest,
    EstornoVendaRequest,
    DisponibilidadeResponse,
    RelatorioEstoque,
    RelatorioMovimentacoes,
)
from config import settings
from interno import auth_interno

log = structlog.get_logger()


class NfeJaImportadaError(ValueError):
    """A chave de acesso desta NF-e já deu entrada no estoque da empresa."""


class EstoqueService:
    """Service para operações de estoque."""

    @staticmethod
    async def verificar_produto_existe(
        empresa_id: int,
        produto_id: UUID,
        variante_id: Optional[UUID] = None
    ) -> bool:
        """
        Valida que o produto (e a variante, se houver) existem no serviço de produtos,
        dentro da empresa informada, e que o produto está ativo.

        Produtos inativos não podem iniciar estoque (criar registro / primeira entrada);
        operações sobre registros de estoque já existentes não passam por aqui, então
        correções e estornos de produtos com estoque continuam funcionando.

        O X-Empresa-Id é obrigatório: o serviço de produtos exige esse header e responde
        400 sem ele — sem o header, NENHUM produto seria considerado válido (e a criação de
        estoque para produtos válidos ficaria impossível). Enviar o header também garante
        isolamento de tenant: um produto de outra empresa retorna 404 e é rejeitado.
        """
        headers = auth_interno({"X-Empresa-Id": str(empresa_id)})
        try:
            async with httpx.AsyncClient() as client:
                produto = await client.get(
                    f"{settings.PRODUTOS_URL}/produtos/{produto_id}",
                    headers=headers, timeout=5.0
                )
                if produto.status_code != 200:
                    return False
                if not produto.json().get("ativo", False):
                    return False

                if variante_id is None:
                    return True

                variante = await client.get(
                    f"{settings.PRODUTOS_URL}/variantes/{variante_id}",
                    headers=headers, timeout=5.0
                )
                return variante.status_code == 200
        except Exception as e:
            log.error("erro_verificar_produto", error=str(e), produto_id=str(produto_id))
            return False

    @staticmethod
    async def criar_estoque(db: AsyncSession, empresa_id: int, data: EstoqueCreate) -> EstoqueResponse:
        """Cria um novo registro de estoque."""
        # Verificar se produto existe (no tenant correto)
        if not await EstoqueService.verificar_produto_existe(empresa_id, data.produto_id, data.variante_id):
            raise ValueError("Produto ou variante não encontrado")
        
        try:
            async with db.begin_nested():
                # Verificar se já existe estoque para este produto/variante
                estoque_existente = await EstoqueRepository.buscar_por_produto(
                    db, empresa_id, data.produto_id, data.variante_id
                )
                if estoque_existente:
                    raise ValueError("Já existe estoque cadastrado para este produto/variante")
                
                # Criar estoque
                estoque = await EstoqueRepository.criar(db, **data.model_dump())
                
            await db.commit()
            log.info("estoque_criado", estoque_id=estoque.id, produto_id=data.produto_id, empresa_id=empresa_id)
            
            return EstoqueResponse.model_validate(estoque)
        except ValueError:
            await db.rollback()
            raise
        except Exception as e:
            await db.rollback()
            log.error("erro_criar_estoque", error=str(e))
            raise

    @staticmethod
    async def buscar_estoque(db: AsyncSession, empresa_id: int, estoque_id: UUID) -> Optional[EstoqueComAlerta]:
        """Busca estoque por ID com alertas."""
        estoque = await EstoqueRepository.buscar_por_id(db, empresa_id, estoque_id)
        if not estoque:
            return None
        
        # Adicionar alertas
        response = EstoqueComAlerta.model_validate(estoque)
        response.alerta_estoque_baixo = estoque.quantidade <= estoque.estoque_minimo and estoque.quantidade > 0
        response.alerta_estoque_zerado = estoque.quantidade == 0
        
        return response

    @staticmethod
    async def listar_estoques(
        db: AsyncSession,
        empresa_id: int,
        skip: int = 0,
        limit: int = 100,
        apenas_baixo: bool = False,
        apenas_zerado: bool = False
    ) -> List[EstoqueComAlerta]:
        """Lista estoques com alertas."""
        estoques = await EstoqueRepository.listar(
            db, empresa_id=empresa_id, skip=skip, limit=limit,
            apenas_baixo=apenas_baixo,
            apenas_zerado=apenas_zerado
        )
        
        result = []
        for estoque in estoques:
            response = EstoqueComAlerta.model_validate(estoque)
            response.alerta_estoque_baixo = estoque.quantidade <= estoque.estoque_minimo and estoque.quantidade > 0
            response.alerta_estoque_zerado = estoque.quantidade == 0
            result.append(response)
        
        return result

    @staticmethod
    async def atualizar_estoque(
        db: AsyncSession,
        empresa_id: int,
        estoque_id: UUID,
        data: EstoqueUpdate
    ) -> Optional[EstoqueResponse]:
        """Atualiza configurações de estoque com transação atômica."""
        try:
            async with db.begin_nested():
                estoque = await EstoqueRepository.atualizar(db, empresa_id, estoque_id, **data.model_dump(exclude_unset=True))
                if not estoque:
                    return None
            
            await db.commit()
            log.info("estoque_atualizado", estoque_id=str(estoque_id), empresa_id=empresa_id)
            
            return EstoqueResponse.model_validate(estoque)
        except Exception as e:
            await db.rollback()
            log.error("erro_atualizar_estoque", error=str(e))
            raise

    @staticmethod
    async def entrada_estoque(
        db: AsyncSession,
        empresa_id: int,
        data: EntradaEstoqueRequest,
        usuario_id: Optional[UUID] = None
    ) -> Tuple[EstoqueResponse, Optional[UUID]]:
        """Registra entrada de estoque com transação atômica."""
        try:
            async with db.begin_nested():
                estoque, lote_id = await EstoqueService._registrar_entrada(
                    db, empresa_id, data, usuario_id
                )

            # Commit da transação principal
            await db.commit()
            
            log.info(
                "entrada_estoque",
                estoque_id=estoque.id,
                quantidade=data.quantidade,
                lote_id=lote_id,
                empresa_id=empresa_id
            )
            
            return EstoqueResponse.model_validate(estoque), lote_id
        except ValueError:
            await db.rollback()
            raise
        except Exception as e:
            await db.rollback()
            log.error("erro_entrada_estoque", error=str(e))
            raise

    @staticmethod
    async def _registrar_entrada(
        db: AsyncSession,
        empresa_id: int,
        data: EntradaEstoqueRequest,
        usuario_id: Optional[UUID] = None
    ) -> Tuple[Estoque, Optional[UUID]]:
        """Soma uma entrada ao estoque na sessão, sem commit: quem chama é dono da transação."""
        # Buscar ou criar estoque. Toda escrita nesta classe lê a linha
        # com FOR UPDATE: a quantidade nova é calculada em Python a partir
        # dessa leitura, e sem o lock duas requisições simultâneas partem
        # do mesmo valor e a segunda apaga a primeira (lost update).
        estoque = await EstoqueRepository.buscar_por_produto(
            db, empresa_id, data.produto_id, data.variante_id, for_update=True
        )

        if not estoque:
            # Verificar se produto existe (no tenant correto)
            if not await EstoqueService.verificar_produto_existe(empresa_id, data.produto_id, data.variante_id):
                raise ValueError("Produto ou variante não encontrado")

            # Criar estoque
            estoque = await EstoqueRepository.criar(
                db,
                empresa_id=empresa_id,
                produto_id=data.produto_id,
                variante_id=data.variante_id,
                quantidade=0.0,
                estoque_minimo=0.0
            )

        # Registrar movimentação
        quantidade_anterior = estoque.quantidade
        quantidade_posterior = quantidade_anterior + data.quantidade

        movimentacao = await MovimentacaoRepository.criar(
            db,
            estoque_id=estoque.id,
            tipo=TipoMovimentacao.ENTRADA.value,
            quantidade=data.quantidade,
            quantidade_anterior=quantidade_anterior,
            quantidade_posterior=quantidade_posterior,
            motivo=data.motivo,
            observacao=data.observacao,
            documento=data.documento,
            custo_unitario=data.custo_unitario,
            usuario_id=usuario_id
        )

        # Atualizar quantidade
        estoque = await EstoqueRepository.atualizar_quantidade(db, empresa_id, estoque.id, quantidade_posterior)

        # Criar lote se solicitado
        lote_id = None
        if data.criar_lote and data.codigo_lote:
            lote = await LoteRepository.criar(
                db,
                empresa_id=empresa_id,
                estoque_id=estoque.id,
                codigo=data.codigo_lote,
                quantidade=data.quantidade,
                data_fabricacao=data.data_fabricacao,
                data_validade=data.data_validade,
                fornecedor=data.fornecedor,
                nota_fiscal=data.nota_fiscal,
                custo_unitario=data.custo_unitario
            )
            lote_id = lote.id

            # Atualizar movimentação com lote
            movimentacao.lote_id = lote_id

        return estoque, lote_id

    @staticmethod
    async def entrada_nfe(
        db: AsyncSession,
        empresa_id: int,
        data: EntradaNfeRequest
    ) -> List[EstoqueResponse]:
        """
        Dá entrada em todos os itens de uma NF-e de forma atômica e uma vez só por chave.

        Reserva a chave no ledger EntradaNfeProcessada ANTES de movimentar: a unique
        constraint serializa importações simultâneas da mesma nota. Tudo ou nada — se um
        item falha, o rollback desfaz os anteriores e a chave volta a ficar livre.

        Raises:
            NfeJaImportadaError: se a chave já deu entrada para esta empresa.
            ValueError: se algum produto não existir ou estiver inativo.
        """
        try:
            db.add(EntradaNfeProcessada(empresa_id=empresa_id, chave=data.chave))
            try:
                await db.flush()
            except IntegrityError:
                raise NfeJaImportadaError("Esta NF-e já foi importada")

            documento = f"NF-e {data.numero}"
            observacao = " · ".join(filter(None, [data.emitente, f"chave {data.chave}"]))
            resultados: List[Estoque] = []
            # Mesma ordem global da baixa de venda: entrada e venda simultâneas não se travam.
            itens_ordenados = sorted(
                data.itens, key=lambda i: chave_ordenacao_item(i.produto_id, None)
            )
            for item in itens_ordenados:
                entrada = EntradaEstoqueRequest(
                    empresa_id=empresa_id,
                    produto_id=item.produto_id,
                    quantidade=item.quantidade,
                    custo_unitario=item.custo_unitario,
                    motivo="Entrada por XML de NF-e",
                    documento=documento,
                    observacao=observacao,
                )
                try:
                    estoque, _ = await EstoqueService._registrar_entrada(db, empresa_id, entrada)
                except ValueError as e:
                    raise ValueError(f"Produto {item.produto_id}: {e}") from e
                resultados.append(estoque)

            await db.commit()

            log.info(
                "entrada_nfe_concluida",
                empresa_id=empresa_id,
                chave=data.chave,
                itens=len(data.itens)
            )

            return [EstoqueResponse.model_validate(e) for e in resultados]
        except ValueError:
            await db.rollback()
            raise
        except Exception as e:
            await db.rollback()
            log.error("erro_entrada_nfe", error=str(e), chave=data.chave)
            raise

    @staticmethod
    async def saida_estoque(
        db: AsyncSession,
        empresa_id: int,
        data: SaidaEstoqueRequest,
        usuario_id: Optional[UUID] = None
    ) -> EstoqueResponse:
        """Registra saída de estoque com transação atômica."""
        try:
            async with db.begin_nested():
                # Lock também serializa o lote: ele só é tocado depois de conferir
                # que pertence a esta linha de estoque.
                estoque = await EstoqueRepository.buscar_por_produto(
                    db, empresa_id, data.produto_id, data.variante_id, for_update=True
                )
                if not estoque:
                    raise ValueError("Estoque não encontrado para este produto/variante")

                # Verificar disponibilidade
                if estoque.quantidade_disponivel < data.quantidade:
                    raise ValueError(
                        f"Quantidade disponível insuficiente. "
                        f"Disponível: {estoque.quantidade_disponivel}, Solicitado: {data.quantidade}"
                    )
                
                # Se especificou lote, verificar e atualizar
                if data.lote_id:
                    lote = await LoteRepository.buscar_por_id(db, empresa_id, data.lote_id)
                    if not lote or lote.estoque_id != estoque.id:
                        raise ValueError("Lote não encontrado ou não pertence a este estoque")

                    # Só BLOQUEADO para aqui — é quarentena, não se mexe. VENCIDO
                    # sai de propósito: esta saída manual é como se registra o
                    # descarte de um lote vencido, e a venda não passa por lote
                    # nenhum (a baixa de venda nem lê esta tabela).
                    if lote.status == StatusLote.BLOQUEADO.value:
                        raise ValueError(f"Lote {lote.codigo} está bloqueado e não pode sair do estoque")

                    if lote.quantidade < data.quantidade:
                        raise ValueError(f"Quantidade insuficiente no lote. Disponível: {lote.quantidade}")
                    
                    # Atualizar quantidade do lote
                    await LoteRepository.atualizar_quantidade(db, empresa_id, lote.id, lote.quantidade - data.quantidade)
                
                # Registrar movimentação
                quantidade_anterior = estoque.quantidade
                quantidade_posterior = quantidade_anterior - data.quantidade
                
                await MovimentacaoRepository.criar(
                    db,
                    estoque_id=estoque.id,
                    lote_id=data.lote_id,
                    tipo=TipoMovimentacao.SAIDA.value,
                    quantidade=data.quantidade,
                    quantidade_anterior=quantidade_anterior,
                    quantidade_posterior=quantidade_posterior,
                    motivo=data.motivo,
                    observacao=data.observacao,
                    documento=data.documento,
                    usuario_id=usuario_id
                )
                
                # Atualizar quantidade
                estoque = await EstoqueRepository.atualizar_quantidade(db, empresa_id, estoque.id, quantidade_posterior)
            
            # Commit da transação principal
            await db.commit()
            
            log.info(
                "saida_estoque",
                estoque_id=estoque.id,
                quantidade=data.quantidade,
                lote_id=data.lote_id,
                empresa_id=empresa_id
            )
            
            return EstoqueResponse.model_validate(estoque)
        except ValueError:
            await db.rollback()
            raise
        except Exception as e:
            await db.rollback()
            log.error("erro_saida_estoque", error=str(e))
            raise

    @staticmethod
    async def ajustar_estoque(
        db: AsyncSession,
        empresa_id: int,
        data: AjusteEstoqueRequest,
        usuario_id: Optional[UUID] = None
    ) -> EstoqueResponse:
        """Ajusta estoque (inventário) com transação atômica."""
        try:
            async with db.begin_nested():
                # Sem o lock, dois ajustes gravam movimentações com o mesmo
                # quantidade_anterior e a trilha de auditoria deixa de fechar.
                estoque = await EstoqueRepository.buscar_por_id(
                    db, empresa_id, data.estoque_id, for_update=True
                )
                if not estoque:
                    raise ValueError("Estoque não encontrado")

                quantidade_anterior = estoque.quantidade
                quantidade_posterior = data.quantidade_nova
                quantidade_ajuste = quantidade_posterior - quantidade_anterior
                
                # Registrar movimentação
                await MovimentacaoRepository.criar(
                    db,
                    estoque_id=estoque.id,
                    tipo=TipoMovimentacao.AJUSTE.value,
                    quantidade=abs(quantidade_ajuste),
                    quantidade_anterior=quantidade_anterior,
                    quantidade_posterior=quantidade_posterior,
                    motivo=data.motivo,
                    observacao=data.observacao,
                    usuario_id=usuario_id
                )
                
                # Atualizar quantidade
                estoque = await EstoqueRepository.atualizar_quantidade(db, empresa_id, estoque.id, quantidade_posterior)
            
            # Commit da transação principal
            await db.commit()
            
            log.info(
                "ajuste_estoque",
                estoque_id=estoque.id,
                quantidade_anterior=quantidade_anterior,
                quantidade_posterior=quantidade_posterior,
                empresa_id=empresa_id
            )
            
            return EstoqueResponse.model_validate(estoque)
        except ValueError:
            await db.rollback()
            raise
        except Exception as e:
            await db.rollback()
            log.error("erro_ajuste_estoque", error=str(e))
            raise

    @staticmethod
    async def reservar_estoque(
        db: AsyncSession,
        empresa_id: int,
        data: ReservaEstoqueRequest
    ) -> EstoqueResponse:
        """Reserva estoque para venda com transação atômica."""
        try:
            async with db.begin_nested():
                # O checkout reserva por aqui: sem o lock, dois pedidos pelo último
                # item passam na checagem de disponível e os dois ficam reservados.
                estoque = await EstoqueRepository.buscar_por_produto(
                    db, empresa_id, data.produto_id, data.variante_id, for_update=True
                )
                if not estoque:
                    raise ValueError("Estoque não encontrado para este produto/variante")

                estoque = await EstoqueRepository.reservar(db, empresa_id, estoque.id, data.quantidade)
            
            # Commit da transação principal
            await db.commit()
            
            log.info(
                "estoque_reservado",
                estoque_id=estoque.id,
                quantidade=data.quantidade,
                documento=data.documento,
                empresa_id=empresa_id
            )
            
            return EstoqueResponse.model_validate(estoque)
        except ValueError:
            await db.rollback()
            raise
        except Exception as e:
            await db.rollback()
            log.error("erro_reservar_estoque", error=str(e))
            raise

    @staticmethod
    async def liberar_reserva(
        db: AsyncSession,
        empresa_id: int,
        data: LiberarReservaRequest
    ) -> EstoqueResponse:
        """Libera reserva de estoque com transação atômica."""
        try:
            async with db.begin_nested():
                estoque = await EstoqueRepository.buscar_por_produto(
                    db, empresa_id, data.produto_id, data.variante_id, for_update=True
                )
                if not estoque:
                    raise ValueError("Estoque não encontrado para este produto/variante")

                estoque = await EstoqueRepository.liberar_reserva(db, empresa_id, estoque.id, data.quantidade)
            
            # Commit da transação principal
            await db.commit()
            
            log.info(
                "reserva_liberada",
                estoque_id=estoque.id,
                quantidade=data.quantidade,
                documento=data.documento,
                empresa_id=empresa_id
            )
            
            return EstoqueResponse.model_validate(estoque)
        except ValueError:
            await db.rollback()
            raise
        except Exception as e:
            await db.rollback()
            log.error("erro_liberar_reserva", error=str(e))
            raise

    @staticmethod
    async def consultar_disponibilidade(
        db: AsyncSession,
        empresa_id: int,
        produto_id: UUID,
        variante_id: Optional[UUID] = None
    ) -> DisponibilidadeResponse:
        """Consulta a disponibilidade real (física e reservada) de um produto/variante."""
        estoque = await EstoqueRepository.buscar_por_produto(db, empresa_id, produto_id, variante_id)
        if not estoque:
            return DisponibilidadeResponse(
                produto_id=produto_id,
                variante_id=variante_id,
                quantidade=0.0,
                quantidade_reservada=0.0,
                quantidade_disponivel=0.0,
                existe=False
            )

        return DisponibilidadeResponse(
            produto_id=produto_id,
            variante_id=variante_id,
            quantidade=estoque.quantidade,
            quantidade_reservada=estoque.quantidade_reservada,
            quantidade_disponivel=estoque.quantidade_disponivel,
            existe=True
        )

    @staticmethod
    async def baixar_venda(
        db: AsyncSession,
        empresa_id: int,
        data: BaixaVendaRequest
    ) -> List[EstoqueResponse]:
        """
        Baixa o estoque de todos os itens de uma venda de forma atômica e idempotente.

        Garantias:
        - Idempotência (C1): a baixa de uma venda (numero_venda == documento) executa
          EXATAMENTE UMA VEZ. Webhooks duplicados, retries e múltiplas instâncias da API
          colidem no ledger BaixaVendaProcessada (unique empresa_id+documento) e não
          duplicam movimentações. Chamadas repetidas retornam o estado atual sem efeito.
        - Atomicidade: tudo ou nada. Uma venda só é baixada se houver estoque físico real
          para TODOS os itens; se qualquer item faltar, a transação inteira é revertida.
        - Anti-deadlock: as linhas de estoque são travadas (FOR UPDATE) em ordem global
          determinística (produto_id, variante_id). Deadlocks/serialization failures do
          PostgreSQL (40P01/40001) ainda possíveis são reexecutados com backoff limitado.

        Raises:
            ValueError: se algum item não tiver estoque suficiente ou não existir, ou se
                o documento (numero_venda) não for informado.
        """
        if not data.documento:
            raise ValueError(
                "documento (numero_venda) é obrigatório para baixa idempotente de estoque"
            )

        ultimo_erro: Optional[BaseException] = None
        for tentativa in range(MAX_TENTATIVAS_DEADLOCK):
            try:
                return await EstoqueService._baixar_venda_once(db, empresa_id, data)
            except DBAPIError as exc:
                await db.rollback()
                if not eh_erro_transitorio(exc):
                    raise
                ultimo_erro = exc
                log.warning(
                    "baixa_venda_deadlock_retry",
                    documento=data.documento,
                    tentativa=tentativa + 1,
                    sqlstate=extrair_sqlstate(exc),
                )
                await asyncio.sleep(backoff_segundos(tentativa))

        log.error("baixa_venda_deadlock_esgotado", documento=data.documento)
        raise ultimo_erro  # type: ignore[misc]

    @staticmethod
    async def _baixar_venda_once(
        db: AsyncSession,
        empresa_id: int,
        data: BaixaVendaRequest
    ) -> List[EstoqueResponse]:
        """Uma tentativa da baixa de venda (chamada pelo wrapper de retry de deadlock)."""
        # Fast path: já baixado → idempotente, retorna o estado atual sem novo efeito.
        if await EstoqueService._baixa_ja_registrada(db, empresa_id, data.documento):
            log.info(
                "baixa_venda_idempotente_ignorada",
                empresa_id=empresa_id,
                documento=data.documento,
            )
            return await EstoqueService._snapshot_itens(db, empresa_id, data.itens)

        try:
            # Reserva o slot de idempotência ANTES de baixar: a unique constraint serializa
            # baixas concorrentes do mesmo documento. O flush força a checagem do índice.
            db.add(BaixaVendaProcessada(empresa_id=empresa_id, documento=data.documento))
            try:
                await db.flush()
            except IntegrityError:
                # Outra transação registrou/está registrando a mesma baixa → idempotente.
                await db.rollback()
                log.info(
                    "baixa_venda_idempotente_corrida",
                    empresa_id=empresa_id,
                    documento=data.documento,
                )
                return await EstoqueService._snapshot_itens(db, empresa_id, data.itens)

            # Trava as linhas em ordem determinística (anti-deadlock) e baixa.
            itens_ordenados = sorted(
                data.itens,
                key=lambda i: chave_ordenacao_item(i.produto_id, i.variante_id),
            )
            resultados: List[Estoque] = []
            for item in itens_ordenados:
                estoque = await EstoqueRepository.buscar_por_produto(
                    db, empresa_id, item.produto_id, item.variante_id, for_update=True
                )
                if not estoque:
                    raise ValueError(
                        f"Estoque não encontrado para o produto {item.produto_id}"
                    )

                if estoque.quantidade < item.quantidade:
                    raise ValueError(
                        f"Estoque insuficiente para o produto {item.produto_id}. "
                        f"Disponível: {estoque.quantidade}, Solicitado: {item.quantidade}"
                    )

                quantidade_anterior = estoque.quantidade
                quantidade_posterior = quantidade_anterior - item.quantidade

                db.add(Movimentacao(
                    estoque_id=estoque.id,
                    tipo=TipoMovimentacao.SAIDA.value,
                    quantidade=item.quantidade,
                    quantidade_anterior=quantidade_anterior,
                    quantidade_posterior=quantidade_posterior,
                    motivo="Venda confirmada",
                    documento=data.documento
                ))

                estoque.quantidade = quantidade_posterior
                # Converte a reserva do checkout em saída (não deixa reserva órfã).
                estoque.quantidade_reservada = max(
                    0.0, estoque.quantidade_reservada - item.quantidade
                )
                estoque.quantidade_disponivel = (
                    estoque.quantidade - estoque.quantidade_reservada
                )
                estoque.updated_at = datetime.utcnow()
                resultados.append(estoque)

            await db.commit()

            log.info(
                "baixa_venda_concluida",
                empresa_id=empresa_id,
                documento=data.documento,
                itens=len(data.itens)
            )

            return [EstoqueResponse.model_validate(e) for e in resultados]
        except ValueError:
            await db.rollback()
            raise
        except DBAPIError:
            # Deadlock/serialization failure → propaga para o wrapper de retry decidir.
            # (não faz rollback aqui; o wrapper faz, preservando a exceção)
            raise
        except Exception as e:
            await db.rollback()
            log.error("erro_baixar_venda", error=str(e), documento=data.documento)
            raise

    @staticmethod
    async def _baixa_ja_registrada(
        db: AsyncSession,
        empresa_id: int,
        documento: str
    ) -> bool:
        """True se a baixa desta venda (documento) já foi registrada no ledger."""
        result = await db.execute(
            select(BaixaVendaProcessada.id).where(
                BaixaVendaProcessada.empresa_id == empresa_id,
                BaixaVendaProcessada.documento == documento,
            )
        )
        return result.first() is not None

    @staticmethod
    async def _snapshot_itens(
        db: AsyncSession,
        empresa_id: int,
        itens
    ) -> List[EstoqueResponse]:
        """Estado atual do estoque dos itens (resposta idempotente, sem efeito colateral)."""
        snapshot: List[EstoqueResponse] = []
        for item in itens:
            estoque = await EstoqueRepository.buscar_por_produto(
                db, empresa_id, item.produto_id, item.variante_id
            )
            if estoque:
                snapshot.append(EstoqueResponse.model_validate(estoque))
        return snapshot

    @staticmethod
    async def estornar_venda(
        db: AsyncSession,
        empresa_id: int,
        data: EstornoVendaRequest
    ) -> List[EstoqueResponse]:
        """
        Estorna (devolve) o estoque de todos os itens de uma venda reembolsada, de forma
        atômica e idempotente. Espelha baixar_venda, mas no sentido inverso.

        Garantias:
        - Idempotência (D2): o estorno de uma venda (numero_venda == documento) executa
          EXATAMENTE UMA VEZ. Reembolsos reentregues, retries e múltiplas instâncias colidem
          no ledger EstornoVendaProcessado (unique empresa_id+documento) e não devolvem
          estoque em duplicidade. Chamadas repetidas retornam o estado atual sem efeito.
        - Atomicidade: tudo ou nada — devolve para TODOS os itens ou nenhum.
        - Anti-deadlock: linhas travadas (FOR UPDATE) em ordem global determinística; falhas
          transitórias do PostgreSQL (40P01/40001) são reexecutadas com backoff limitado.

        Raises:
            ValueError: se o documento (numero_venda) não for informado.
        """
        if not data.documento:
            raise ValueError(
                "documento (numero_venda) é obrigatório para estorno idempotente de estoque"
            )

        ultimo_erro: Optional[BaseException] = None
        for tentativa in range(MAX_TENTATIVAS_DEADLOCK):
            try:
                return await EstoqueService._estornar_venda_once(db, empresa_id, data)
            except DBAPIError as exc:
                await db.rollback()
                if not eh_erro_transitorio(exc):
                    raise
                ultimo_erro = exc
                log.warning(
                    "estorno_venda_deadlock_retry",
                    documento=data.documento,
                    tentativa=tentativa + 1,
                    sqlstate=extrair_sqlstate(exc),
                )
                await asyncio.sleep(backoff_segundos(tentativa))

        log.error("estorno_venda_deadlock_esgotado", documento=data.documento)
        raise ultimo_erro  # type: ignore[misc]

    @staticmethod
    async def _estornar_venda_once(
        db: AsyncSession,
        empresa_id: int,
        data: EstornoVendaRequest
    ) -> List[EstoqueResponse]:
        """Uma tentativa do estorno de venda (chamada pelo wrapper de retry de deadlock)."""
        # Fast path: já estornado → idempotente, retorna o estado atual sem novo efeito.
        if await EstoqueService._estorno_ja_registrado(db, empresa_id, data.documento):
            log.info(
                "estorno_venda_idempotente_ignorado",
                empresa_id=empresa_id,
                documento=data.documento,
            )
            return await EstoqueService._snapshot_itens(db, empresa_id, data.itens)

        try:
            # Reserva o slot de idempotência ANTES de devolver: a unique constraint serializa
            # estornos concorrentes do mesmo documento. O flush força a checagem do índice.
            db.add(EstornoVendaProcessado(empresa_id=empresa_id, documento=data.documento))
            try:
                await db.flush()
            except IntegrityError:
                # Outra transação registrou/está registrando o mesmo estorno → idempotente.
                await db.rollback()
                log.info(
                    "estorno_venda_idempotente_corrida",
                    empresa_id=empresa_id,
                    documento=data.documento,
                )
                return await EstoqueService._snapshot_itens(db, empresa_id, data.itens)

            # Trava as linhas em ordem determinística (anti-deadlock) e devolve o estoque.
            itens_ordenados = sorted(
                data.itens,
                key=lambda i: chave_ordenacao_item(i.produto_id, i.variante_id),
            )
            resultados: List[Estoque] = []
            for item in itens_ordenados:
                estoque = await EstoqueRepository.buscar_por_produto(
                    db, empresa_id, item.produto_id, item.variante_id, for_update=True
                )
                if not estoque:
                    raise ValueError(
                        f"Estoque não encontrado para o produto {item.produto_id}"
                    )

                quantidade_anterior = estoque.quantidade
                quantidade_posterior = quantidade_anterior + item.quantidade

                db.add(Movimentacao(
                    estoque_id=estoque.id,
                    tipo=TipoMovimentacao.DEVOLUCAO.value,
                    quantidade=item.quantidade,
                    quantidade_anterior=quantidade_anterior,
                    quantidade_posterior=quantidade_posterior,
                    motivo="Venda reembolsada",
                    documento=data.documento
                ))

                estoque.quantidade = quantidade_posterior
                estoque.quantidade_disponivel = (
                    estoque.quantidade - estoque.quantidade_reservada
                )
                estoque.updated_at = datetime.utcnow()
                resultados.append(estoque)

            await db.commit()

            log.info(
                "estorno_venda_concluido",
                empresa_id=empresa_id,
                documento=data.documento,
                itens=len(data.itens)
            )

            return [EstoqueResponse.model_validate(e) for e in resultados]
        except ValueError:
            await db.rollback()
            raise
        except DBAPIError:
            # Deadlock/serialization failure → propaga para o wrapper de retry decidir.
            raise
        except Exception as e:
            await db.rollback()
            log.error("erro_estornar_venda", error=str(e), documento=data.documento)
            raise

    @staticmethod
    async def _estorno_ja_registrado(
        db: AsyncSession,
        empresa_id: int,
        documento: str
    ) -> bool:
        """True se o estorno desta venda (documento) já foi registrado no ledger."""
        result = await db.execute(
            select(EstornoVendaProcessado.id).where(
                EstornoVendaProcessado.empresa_id == empresa_id,
                EstornoVendaProcessado.documento == documento,
            )
        )
        return result.first() is not None

    @staticmethod
    async def gerar_relatorio(db: AsyncSession, empresa_id: int) -> RelatorioEstoque:
        """Gera relatório geral de estoque."""
        total_produtos = await EstoqueRepository.contar_total(db, empresa_id)
        produtos_estoque_baixo = await EstoqueRepository.contar_estoque_baixo(db, empresa_id)
        produtos_sem_estoque = await EstoqueRepository.contar_estoque_zerado(db, empresa_id)
        
        # Calcular total em estoque
        estoques = await EstoqueRepository.listar(db, empresa_id=empresa_id, limit=10000)
        total_em_estoque = sum(e.quantidade for e in estoques)
        
        return RelatorioEstoque(
            total_produtos=total_produtos,
            total_em_estoque=total_em_estoque,
            produtos_estoque_baixo=produtos_estoque_baixo,
            produtos_sem_estoque=produtos_sem_estoque
        )

    @staticmethod
    async def gerar_relatorio_movimentacoes(
        db: AsyncSession,
        empresa_id: int,
        data_inicio: datetime,
        data_fim: datetime
    ) -> RelatorioMovimentacoes:
        """Gera relatório de movimentações."""
        total_entradas = await MovimentacaoRepository.contar_por_tipo(
            db, empresa_id, TipoMovimentacao.ENTRADA, data_inicio, data_fim
        )
        total_saidas = await MovimentacaoRepository.contar_por_tipo(
            db, empresa_id, TipoMovimentacao.SAIDA, data_inicio, data_fim
        )
        
        quantidade_entrada = await MovimentacaoRepository.somar_quantidade_por_tipo(
            db, empresa_id, TipoMovimentacao.ENTRADA, data_inicio, data_fim
        )
        quantidade_saida = await MovimentacaoRepository.somar_quantidade_por_tipo(
            db, empresa_id, TipoMovimentacao.SAIDA, data_inicio, data_fim
        )
        
        return RelatorioMovimentacoes(
            periodo_inicio=data_inicio,
            periodo_fim=data_fim,
            total_entradas=total_entradas,
            total_saidas=total_saidas,
            quantidade_entrada=quantidade_entrada,
            quantidade_saida=quantidade_saida
        )
