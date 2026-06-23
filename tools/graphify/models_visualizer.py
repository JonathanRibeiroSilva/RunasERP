"""Visualizador de relacionamentos entre models SQLAlchemy"""
import re
from pathlib import Path
from typing import Dict, List
import networkx as nx
import warnings
warnings.filterwarnings('ignore')


class ModelsVisualizer:
    """Gera visualização dos relacionamentos entre models"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.services_dir = self.project_root / "services"
        self.graph = nx.DiGraph()
        self.models = {}
