"""Visualizador de arquitetura de microsserviços do RunasERP"""
import os
from pathlib import Path
from typing import Dict, List
import networkx as nx
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')


class ArchitectureVisualizer:
    """Gera visualização da arquitetura de microsserviços"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.services_dir = self.project_root / "services"
        self.api_gateway_dir = self.project_root / "api-gateway"
        self.graph = nx.DiGraph()

    def scan_services(self) -> Dict[str, Dict]:
        """Escaneia todos os microsserviços do projeto"""
        services = {}
        services['api-gateway'] = {'type': 'gateway', 'path': self.api_gateway_dir, 'endpoints': self._scan_endpoints(self.api_gateway_dir), 'dependencies': []}
        if self.services_dir.exists():
            for service_dir in self.services_dir.iterdir():
                if service_dir.is_dir() and not service_dir.name.startswith('_'):
                    service_name = service_dir.name
                    services[service_name] = {'type': 'microservice', 'path': service_dir, 'endpoints': self._scan_endpoints(service_dir), 'models': self._scan_models(service_dir), 'dependencies': self._scan_dependencies(service_dir)}
        return services
    
    def _scan_endpoints(self, service_path: Path) -> List[str]:
        endpoints = []
        routers_dir = service_path / "routers"
        if routers_dir.exists():
            for router_file in routers_dir.glob("*.py"):
                if router_file.name.startswith('_'): continue
                try:
                    content = router_file.read_text(encoding='utf-8')
                    for line in content.split('\n'):
                        if '@router.' in line or '@app.' in line:
                            if '("' in line or "('": endpoints.append(line.strip())
                except Exception: pass
        return endpoints
    
    def _scan_models(self, service_path: Path) -> List[str]:
        models = []
        models_dir = service_path / "models"
        if models_dir.exists():
            for model_file in models_dir.glob("*.py"):
                if model_file.name.startswith('_'): continue
                try:
                    content = model_file.read_text(encoding='utf-8')
                    for line in content.split('\n'):
                        if 'class ' in line and '(Base)' in line:
                            models.append(line.split('class ')[1].split('(')[0].strip())
                except Exception: pass
        return models
    
    def _scan_dependencies(self, service_path: Path) -> List[str]:
        dependencies = []
        for py_file in service_path.rglob("*.py"):
            try:
                content = py_file.read_text(encoding='utf-8')
                for service in ['clientes', 'empresas', 'produtos', 'vendas', 'estoque', 'financeiro', 'notificacoes']:
                    if f'/{service}' in content or f'{service.upper()}_SERVICE' in content:
                        if service not in dependencies: dependencies.append(service)
            except Exception: pass
        return dependencies
