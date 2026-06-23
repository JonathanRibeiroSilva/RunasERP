#!/usr/bin/env python3
"""
Graphify - Ferramenta de visualização de arquitetura
"""
import sys
import os
import argparse
from pathlib import Path

# No Docker, o projeto está montado em /project
project_root = Path(os.getenv('PROJECT_ROOT', '/project'))
sys.path.insert(0, str(project_root))


def main():
    parser = argparse.ArgumentParser(description='Graphify - Visualizador de Arquitetura')
    parser.add_argument('--all', action='store_true', help='Gerar todas as visualizações')
    parser.add_argument('--architecture', action='store_true', help='Arquitetura de microsserviços')
    parser.add_argument('--models', action='store_true', help='Relacionamentos entre models')
    parser.add_argument('--dependencies', action='store_true', help='Dependências entre serviços')
    
    args = parser.parse_args()
    
    # Se nenhum argumento, mostra help
    if not any([args.all, args.architecture, args.models, args.dependencies]):
        parser.print_help()
        return
    
    print("🚀 Graphify - Iniciando análise do RunasERP\n")
    
    try:
        from architecture_visualizer import ArchitectureVisualizer
        from html_generator import HTMLGenerator
        
        if args.all or args.architecture:
            print("📊 Gerando visualização de arquitetura...")
            arch_viz = ArchitectureVisualizer(str(project_root))
            services = arch_viz.scan_services()
            print(f"   ✅ {len(services)} serviços encontrados")
            
            html_gen = HTMLGenerator()
            output_file = html_gen.generate_architecture_html(services)
            print(f"   ✅ HTML gerado: {output_file}")
        
        if args.all or args.models:
            print("🗺️  Gerando visualização de models...")
            print("   ⚠️  Em desenvolvimento")
        
        if args.all or args.dependencies:
            print("🔗 Gerando visualização de dependências...")
            print("   ⚠️  Em desenvolvimento")
        
        print("\n✅ Análise concluída! Abra output/graph.html no navegador.")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
