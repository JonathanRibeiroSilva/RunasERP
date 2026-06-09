"""
Validadores customizados para o serviço de empresas.
"""
import re
from validate_docbr import CNPJ as CNPJValidator


def validar_cnpj(cnpj: str) -> bool:
    """
    Valida um CNPJ usando validação de dígitos verificadores.
    
    Args:
        cnpj: CNPJ com ou sem formatação
        
    Returns:
        True se válido, False caso contrário
    """
    # Remover formatação
    cnpj_limpo = re.sub(r'[^0-9]', '', cnpj)
    
    # Validar com biblioteca
    validator = CNPJValidator()
    return validator.validate(cnpj_limpo)


def formatar_cnpj(cnpj: str) -> str:
    """
    Formata um CNPJ para o padrão XX.XXX.XXX/XXXX-XX.
    
    Args:
        cnpj: CNPJ sem formatação (apenas números)
        
    Returns:
        CNPJ formatado
    """
    cnpj_limpo = re.sub(r'[^0-9]', '', cnpj)
    
    if len(cnpj_limpo) != 14:
        return cnpj
    
    return f"{cnpj_limpo[:2]}.{cnpj_limpo[2:5]}.{cnpj_limpo[5:8]}/{cnpj_limpo[8:12]}-{cnpj_limpo[12:]}"


def limpar_cnpj(cnpj: str) -> str:
    """
    Remove formatação do CNPJ, deixando apenas números.
    
    Args:
        cnpj: CNPJ formatado
        
    Returns:
        CNPJ sem formatação
    """
    return re.sub(r'[^0-9]', '', cnpj)
