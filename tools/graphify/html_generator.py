"""Gerador HTML com vis.js"""
from pathlib import Path
import json

class HTMLGenerator:
    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def generate_architecture_html(self, services: dict, output_file: str = "graph.html"):
        nodes, edges = [], []
        colors = {'gateway': {'background': '#FF6B6B', 'border': '#C92A2A'}, 'microservice': {'background': '#4ECDC4', 'border': '#0B7285'}}
        
        for svc_name, svc_info in services.items():
            node_type = svc_info['type']
            endpoints = len(svc_info.get('endpoints', []))
            models = len(svc_info.get('models', []))
            color = colors.get(node_type, {'background': '#95E1D3', 'border': '#087F5B'})
            nodes.append({'id': svc_name, 'label': svc_name, 'title': f'{svc_name}<br>Endpoints: {endpoints}<br>Models: {models}', 'color': color, 'value': 50 if node_type == 'gateway' else 30})
        
        eid = 0
        if 'api-gateway' in services:
            for svc in services:
                if svc != 'api-gateway':
                    edges.append({'from': 'api-gateway', 'to': svc, 'color': '#666', 'arrows': 'to'})
                    eid += 1
        
        for svc, info in services.items():
            for dep in info.get('dependencies', []):
                if dep in services:
                    edges.append({'from': svc, 'to': dep, 'color': '#FFA500', 'width': 3, 'arrows': 'to', 'dashes': True})
                    eid += 1
        
        html = self._create_html(nodes, edges)
        output_path = self.output_dir / output_file
        output_path.write_text(html, encoding='utf-8')
        return output_path

    def _create_html(self, nodes, edges):
        return f'''<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>RunasERP - Arquitetura</title>
<script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
<style>body{{margin:0;font-family:Arial;background:#1a1a1a;color:#fff}}
#network{{width:100vw;height:100vh}}
#info{{position:absolute;top:10px;left:10px;background:rgba(0,0,0,0.8);padding:15px;border-radius:5px}}
</style></head><body>
<div id="info"><h2>RunasERP - Arquitetura</h2><p>🔵 Gateway | 🟢 Microsserviços</p></div>
<div id="network"></div>
<script>
var nodes = new vis.DataSet({json.dumps(nodes)});
var edges = new vis.DataSet({json.dumps(edges)});
var container = document.getElementById('network');
var data = {{nodes: nodes, edges: edges}};
var options = {{
  nodes: {{shape: 'dot', font: {{color: '#fff', size: 14}}}},
  edges: {{smooth: {{type: 'continuous'}}}},
  physics: {{barnesHut: {{gravitationalConstant: -8000, springLength: 200}}}},
  interaction: {{hover: true, tooltipDelay: 100}}
}};
var network = new vis.Network(container, data, options);
</script></body></html>'''
