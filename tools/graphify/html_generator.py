"""Gerador de visualização HTML interativa"""
from pathlib import Path
from pyvis.network import Network


class HTMLGenerator:
    """Gera HTML interativo com visualização de grafos"""
    
    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def generate_architecture_html(self, services: dict, output_file: str = "graph.html"):
        """Gera HTML interativo da arquitetura"""
        net = Network(height="900px", width="100%", bgcolor="#1a1a1a", font_color="white")
        net.barnes_hut(gravity=-8000, central_gravity=0.3, spring_length=200)
        
        colors = {'gateway': '#FF6B6B', 'microservice': '#4ECDC4'}
        
        for service_name, service_info in services.items():
            node_type = service_info['type']
            color = colors.get(node_type, '#95E1D3')
            endpoints = len(service_info.get('endpoints', []))
            models = len(service_info.get('models', []))
            title = f"<b>{service_name}</b><br>Tipo: {node_type}<br>Endpoints: {endpoints}<br>Models: {models}"
            size = 50 if node_type == 'gateway' else 30
            net.add_node(service_name, label=service_name, title=title, color=color, size=size, shape="dot")
        
        if 'api-gateway' in services:
            for service_name in services:
                if service_name != 'api-gateway':
                    net.add_edge('api-gateway', service_name, color='#666666')
        
        for service_name, service_info in services.items():
            for dep in service_info.get('dependencies', []):
                if dep in services:
                    net.add_edge(service_name, dep, color='#FFA500', width=2)
        
        net.set_options('{"physics":{"enabled":true},"interaction":{"hover":true}}')
        output_path = self.output_dir / output_file
        net.show(str(output_path))
        return output_path
