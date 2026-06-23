# Graphify - Visualizador de Arquitetura RunasERP

Ferramenta customizada para gerar visualizações da arquitetura do sistema ERP.

## 🚀 Instalação

```bash
cd tools/graphify
pip install -r requirements.txt
```

## 📊 Funcionalidades

1. **Arquitetura de Microsserviços** - Visualiza todos os serviços e suas conexões
2. **Relacionamentos entre Models** - Mapeia entidades e foreign keys
3. **Dependências entre Serviços** - Identifica acoplamento
4. **Estrutura Detalhada** - Analisa endpoints, models, schemas

## 💻 Uso

```bash
# Gerar todas as visualizações
python main.py --all

# Apenas arquitetura
python main.py --architecture

# Apenas models
python main.py --models

# Apenas dependências
python main.py --dependencies
```

## 📁 Saída

- `architecture.png` - Diagrama da arquitetura
- `models_relationships.png` - Relacionamentos entre models
- `dependencies.png` - Grafo de dependências
- `*.md` - Relatórios detalhados
