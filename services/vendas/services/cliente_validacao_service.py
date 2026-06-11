"""
Service de Validação de Cliente Convidado.
Valida dados de clientes não cadastrados (compra sem cadastro).
"""
import re
from typing import Optional, tuple
import structlog

log = structlog.get_logger()


class ClienteValidacaoService:
    """
    Service para validar dados de cliente convidado.
    
    Validações:
    - Telefone: DDD (2 dígitos) + número (9 dígitos para celular)
    - Email: formato válido (regex)
    - CPF: dígitos verificadores
    - Nome: mínimo 3 caracteres
    """
    
    @staticmethod
    def validar_nome(nome: str) -> tuple[bool, Optional[str]]:
        """
        Valida nome do cliente.
        
        Regras:
        - Mínimo 3 caracteres
        - Máximo 200 caracteres
        
        Returns:
            tuple: (valido, erro)
        """
        if not nome or len(nome.strip()) < 3:
            return (False, "Nome deve ter no mínimo 3 caracteres")
        
        if len(nome) > 200:
            return (False, "Nome deve ter no máximo 200 caracteres")
        
        return (True, None)
    
    @staticmethod
    def normalizar_telefone(telefone: str) -> str:
        """
        Normaliza telefone removendo caracteres não numéricos.
        
        Exemplo: (11) 99999-9999 → 11999999999
        
        Returns:
            str: Telefone apenas com dígitos
        """
        return re.sub(r'\D', '', telefone)
    
    @staticmethod
    def validar_telefone(telefone: str) -> tuple[bool, Optional[str], Optional[str]]:
        """
        Valida telefone brasileiro.
        
        Regras:
        - DDD: 2 dígitos (11-99)
        - Celular: 9 dígitos (9XXXX-XXXX)
        - Fixo: 8 dígitos (XXXX-XXXX) - também aceito
        
        Returns:
            tuple: (valido, telefone_normalizado, erro)
        """
        # Normalizar (remover formatação)
        tel_limpo = ClienteValidacaoService.normalizar_telefone(telefone)
        
        # Deve ter 10 ou 11 dígitos (DDD + número)
        if len(tel_limpo) not in [10, 11]:
            return (False, None, "Telefone deve ter 10 ou 11 dígitos (DDD + número)")
        
        # Extrair DDD
        ddd = tel_limpo[:2]
        
        # Validar DDD (11-99)
        if not (11 <= int(ddd) <= 99):
            return (False, None, "DDD inválido (deve ser entre 11 e 99)")
        
        # Validar 9º dígito para celular
        if len(tel_limpo) == 11:
            nono_digito = tel_limpo[2]
            if nono_digito != '9':
                return (False, None, "Celular deve começar com 9")
        
        log.info(
            "telefone_validado",
            telefone_original=telefone,
            telefone_normalizado=tel_limpo
        )
        
        return (True, tel_limpo, None)
    
    @staticmethod
    def validar_email(email: str) -> tuple[bool, Optional[str]]:
        """
        Valida formato de email (regex simples).
        
        Regra:
        - Formato: algo@dominio.com
        
        Returns:
            tuple: (valido, erro)
        """
        # Regex simples para email
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if not re.match(pattern, email):
            return (False, "Email inválido")
        
        return (True, None)
    
    @staticmethod
    def validar_cpf(cpf: str) -> tuple[bool, Optional[str], Optional[str]]:
        """
        Valida CPF brasileiro (dígitos verificadores).
        
        Regra:
        - 11 dígitos numéricos
        - Algoritmo de validação dos dígitos verificadores
        
        Returns:
            tuple: (valido, cpf_normalizado, erro)
        """
        # Remover formatação
        cpf_limpo = re.sub(r'\D', '', cpf)
        
        # Deve ter 11 dígitos
        if len(cpf_limpo) != 11:
            return (False, None, "CPF deve ter 11 dígitos")
        
        # Verificar se não é sequência repetida (111.111.111-11, etc)
        if cpf_limpo == cpf_limpo[0] * 11:
            return (False, None, "CPF inválido")
        
        # Calcular primeiro dígito verificador
        soma = 0
        for i in range(9):
            soma += int(cpf_limpo[i]) * (10 - i)
        
        resto = soma % 11
        digito1 = 0 if resto < 2 else 11 - resto
        
        if int(cpf_limpo[9]) != digito1:
            return (False, None, "CPF inválido (dígito verificador incorreto)")
        
        # Calcular segundo dígito verificador
        soma = 0
        for i in range(10):
            soma += int(cpf_limpo[i]) * (11 - i)
        
        resto = soma % 11
        digito2 = 0 if resto < 2 else 11 - resto
        
        if int(cpf_limpo[10]) != digito2:
            return (False, None, "CPF inválido (dígito verificador incorreto)")
        
        log.info(
            "cpf_validado",
            cpf_normalizado=cpf_limpo
        )
        
        return (True, cpf_limpo, None)
    
    @staticmethod
    def validar_cliente_convidado(
        nome: str,
        telefone: str,
        email: Optional[str] = None,
        cpf: Optional[str] = None
    ) -> tuple[bool, dict, list[str]]:
        """
        Valida todos os dados do cliente convidado.
        
        Args:
            nome: Nome completo (obrigatório)
            telefone: Telefone com DDD (obrigatório)
            email: Email (opcional)
            cpf: CPF (opcional)
        
        Returns:
            tuple: (valido, dados_normalizados, erros)
                - valido: True se todos os campos obrigatórios válidos
                - dados_normalizados: Dict com dados limpos
                - erros: Lista de mensagens de erro
        """
        erros = []
        dados = {}
        
        # 1. Validar nome (obrigatório)
        valido_nome, erro_nome = ClienteValidacaoService.validar_nome(nome)
        if not valido_nome:
            erros.append(erro_nome)
        else:
            dados['nome'] = nome.strip()
        
        # 2. Validar telefone (obrigatório)
        valido_tel, tel_norm, erro_tel = ClienteValidacaoService.validar_telefone(telefone)
        if not valido_tel:
            erros.append(erro_tel)
        else:
            dados['telefone'] = tel_norm
        
        # 3. Validar email (opcional)
        if email:
            valido_email, erro_email = ClienteValidacaoService.validar_email(email)
            if not valido_email:
                erros.append(erro_email)
            else:
                dados['email'] = email.lower().strip()
        
        # 4. Validar CPF (opcional)
        if cpf:
            valido_cpf, cpf_norm, erro_cpf = ClienteValidacaoService.validar_cpf(cpf)
            if not valido_cpf:
                erros.append(erro_cpf)
            else:
                dados['cpf'] = cpf_norm
        
        # Validação geral
        valido = len(erros) == 0
        
        if valido:
            log.info(
                "cliente_convidado_validado",
                nome=dados.get('nome'),
                telefone=dados.get('telefone'),
                tem_email=bool(email),
                tem_cpf=bool(cpf)
            )
        else:
            log.warning(
                "cliente_convidado_invalido",
                erros=erros
            )
        
        return (valido, dados, erros)
