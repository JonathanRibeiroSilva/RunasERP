# Instalação do Graphify

## Pré-requisitos

### 1. Instalar Python
- Download: https://www.python.org/downloads/
- Versão mínima: 3.9+
- **IMPORTANTE**: Marcar "Add Python to PATH" durante instalação

### 2. Verificar instalação
```bash
python --version
```

## Instalação das Dependências

```bash
cd tools\graphify
pip install -r requirements.txt
```

## Uso

```bash
# Gerar todas as visualizações
python main.py --all

# Visualizações específicas
python main.py --architecture
python main.py --models
python main.py --dependencies
```
