# Graphify - Visualizador de Arquitetura RunasERP

Ferramenta customizada para gerar visualizações **interativas em HTML** da arquitetura do sistema ERP.

## 🚀 Uso Rápido (Docker - Recomendado)

**Não precisa ter Python instalado!**

```bash
# Windows
run.bat

# Ou manualmente
docker-compose build
docker-compose run --rm graphify
```

Isso vai gerar `output/graph.html` - abra no navegador!

## 📊 Funcionalidades

1. **Arquitetura de Microsserviços** - Visualiza todos os serviços e suas conexões
2. **Relacionamentos entre Models** - Mapeia entidades e foreign keys
3. **Dependências entre Serviços** - Identifica acoplamento
4. **HTML Interativo** - Arraste, zoom, clique nos nós para detalhes

## 💻 Uso Direto (com Python instalado)

```bash
cd tools/graphify
pip install -r requirements.txt
python main.py --all
```

## 📁 Saída

- `output/graph.html` - **HTML interativo** (abra no navegador!)
- `output/*.md` - Relatórios detalhados

## 🎨 Recursos do HTML

- 🖱️ **Arraste os nós** para reorganizar
- 🔍 **Zoom** com scroll do mouse
- 💡 **Hover** nos nós para ver detalhes
- 🎯 **Clique** para fixar posição
- 🌙 **Tema escuro** moderno
