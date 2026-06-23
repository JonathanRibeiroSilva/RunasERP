"""Visualizador de dependências entre serviços"""
from pathlib import Path
from typing import Dict, List, Set
import networkx as nx
import warnings
warnings.filterwarnings('ignore')


class DependenciesVisualizer:
    """Gera visualização de dependências entre serviços"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.services_dir = self.project_root / "services"
        self.graph = nx.DiGraph()
