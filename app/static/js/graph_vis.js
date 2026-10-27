/**
 * Graph Visualizer & Traversal Engine (BFS & DFS)
 * Interactive HTML5 Canvas Renderer
 */

class InteractiveGraphVis {
  constructor(canvasId, logContainerId) {
    this.canvas = document.getElementById(canvasId);
    if (!this.canvas) return;
    this.ctx = this.canvas.getContext('2d');
    this.logContainer = document.getElementById(logContainerId);

    this.nodes = [];
    this.edges = [];
    this.nodeMap = new Map();
    this.selectedNode = null;
    this.draggedNode = null;
    this.isDragging = false;
    this.activeHighlights = new Set();
    this.activeEdges = new Set();

    this.initCanvasSize();
    this.bindEvents();
  }

  initCanvasSize() {
    const rect = this.canvas.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    this.width = rect.width;
    this.height = rect.height || 450;
    this.canvas.width = this.width * dpr;
    this.canvas.height = this.height * dpr;
    this.ctx.scale(dpr, dpr);
  }

  setData(data) {
    this.nodeMap.clear();
    const count = data.nodes.length;
    const centerX = this.width / 2;
    const centerY = this.height / 2;
    const radius = Math.min(this.width, this.height) * 0.38;

    // Distribute nodes circularly with slight spring offset
    this.nodes = data.nodes.map((n, i) => {
      const angle = (i / count) * 2 * Math.PI;
      const node = {
        ...n,
        x: centerX + radius * Math.cos(angle) + (Math.random() - 0.5) * 20,
        y: centerY + radius * Math.sin(angle) + (Math.random() - 0.5) * 20,
        radius: 22 + Math.min(n.degree * 2, 8),
        color: '#7c5cbf',
        state: 'default' // 'default', 'start', 'visited', 'active'
      };
      this.nodeMap.set(n.id, node);
      return node;
    });

    this.edges = data.edges.map(e => ({
      ...e,
      fromNode: this.nodeMap.get(e.from),
      toNode: this.nodeMap.get(e.to),
      state: 'default'
    }));

    this.draw();
  }

  bindEvents() {
    this.canvas.addEventListener('mousedown', (e) => this.onMouseDown(e));
    this.canvas.addEventListener('mousemove', (e) => this.onMouseMove(e));
    window.addEventListener('mouseup', () => this.onMouseUp());
    window.addEventListener('resize', () => {
      this.initCanvasSize();
      this.draw();
    });
  }

  getMousePos(e) {
    const rect = this.canvas.getBoundingClientRect();
    return {
      x: e.clientX - rect.left,
      y: e.clientY - rect.top
    };
  }

  findNodeAt(x, y) {
    for (let i = this.nodes.length - 1; i >= 0; i--) {
      const n = this.nodes[i];
      const dist = Math.hypot(n.x - x, n.y - y);
      if (dist <= n.radius + 4) return n;
    }
    return null;
  }

  onMouseDown(e) {
    const pos = this.getMousePos(e);
    const node = this.findNodeAt(pos.x, pos.y);
    if (node) {
      this.draggedNode = node;
      this.isDragging = true;
      this.selectedNode = node;
      // Trigger book select event if present
      const selectElem = document.getElementById('graphBookSelect');
      if (selectElem && selectElem.value != node.id) {
        selectElem.value = node.id;
        selectElem.dispatchEvent(new Event('change'));
      }
    }
  }

  onMouseMove(e) {
    const pos = this.getMousePos(e);
    if (this.isDragging && this.draggedNode) {
      this.draggedNode.x = pos.x;
      this.draggedNode.y = pos.y;
      this.draw();
    } else {
      const hovered = this.findNodeAt(pos.x, pos.y);
      this.canvas.style.cursor = hovered ? 'pointer' : 'default';
    }
  }

  onMouseUp() {
    this.isDragging = false;
    this.draggedNode = null;
  }

  draw() {
    this.ctx.clearRect(0, 0, this.width, this.height);

    // Draw background subtle grid
    this.ctx.strokeStyle = '#f1ecfa';
    this.ctx.lineWidth = 1;
    for (let x = 0; x < this.width; x += 40) {
      this.ctx.beginPath();
      this.ctx.moveTo(x, 0);
      this.ctx.lineTo(x, this.height);
      this.ctx.stroke();
    }
    for (let y = 0; y < this.height; y += 40) {
      this.ctx.beginPath();
      this.ctx.moveTo(0, y);
      this.ctx.lineTo(this.width, y);
      this.ctx.stroke();
    }

    // Draw Edges
    this.edges.forEach(edge => {
      if (!edge.fromNode || !edge.toNode) return;
      const isTraversed = this.activeEdges.has(`${edge.from}-${edge.to}`) || this.activeEdges.has(`${edge.to}-${edge.from}`);

      this.ctx.beginPath();
      this.ctx.moveTo(edge.fromNode.x, edge.fromNode.y);
      this.ctx.lineTo(edge.toNode.x, edge.toNode.y);

      if (isTraversed) {
        this.ctx.strokeStyle = '#10b981';
        this.ctx.lineWidth = 3.5;
      } else {
        this.ctx.strokeStyle = '#e2d7f5';
        this.ctx.lineWidth = 1.8;
      }
      this.ctx.stroke();

      // Draw relation label near midpoint
      const midX = (edge.fromNode.x + edge.toNode.x) / 2;
      const midY = (edge.fromNode.y + edge.toNode.y) / 2;
      this.ctx.fillStyle = isTraversed ? '#065f46' : '#8e85a6';
      this.ctx.font = '10px Inter, sans-serif';
      this.ctx.textAlign = 'center';
      this.ctx.fillText(edge.relation || '', midX, midY - 3);
    });

    // Draw Nodes
    this.nodes.forEach(node => {
      const isSelected = this.selectedNode && this.selectedNode.id === node.id;
      
      // Node Outer Shadow / Glow
      if (node.state === 'active' || isSelected) {
        this.ctx.beginPath();
        this.ctx.arc(node.x, node.y, node.radius + 6, 0, 2 * Math.PI);
        this.ctx.fillStyle = 'rgba(124, 92, 191, 0.25)';
        this.ctx.fill();
      }

      // Node Circle
      this.ctx.beginPath();
      this.ctx.arc(node.x, node.y, node.radius, 0, 2 * Math.PI);
      
      if (node.state === 'start') {
        this.ctx.fillStyle = '#f59e0b'; // Amber start
      } else if (node.state === 'active') {
        this.ctx.fillStyle = '#10b981'; // Emerald active
      } else if (node.state === 'visited') {
        this.ctx.fillStyle = '#9d78e6'; // Lavender light visited
      } else {
        this.ctx.fillStyle = '#7c5cbf'; // Lavender default
      }
      this.ctx.fill();

      this.ctx.strokeStyle = '#ffffff';
      this.ctx.lineWidth = 2.5;
      this.ctx.stroke();

      // Node ID / Number inside
      this.ctx.fillStyle = '#ffffff';
      this.ctx.font = 'bold 11px Inter, sans-serif';
      this.ctx.textAlign = 'center';
      this.ctx.textBaseline = 'middle';
      this.ctx.fillText(`#${node.id}`, node.x, node.y);

      // Node Title Below
      this.ctx.fillStyle = '#271e3d';
      this.ctx.font = '600 11.5px Inter, sans-serif';
      this.ctx.textBaseline = 'top';
      const label = node.label.length > 20 ? node.label.slice(0, 18) + '...' : node.label;
      this.ctx.fillText(label, node.x, node.y + node.radius + 5);
    });
  }

  async animateTraversal(traversalData, type = 'BFS') {
    this.resetStates();
    if (!this.logContainer) return;
    this.logContainer.innerHTML = '';

    const startNode = this.nodeMap.get(traversalData.start_node);
    if (startNode) {
      startNode.state = 'start';
    }
    this.draw();

    this.addLog(`<strong>Starting ${type} Traversal:</strong> Root Book: #${traversalData.start_node}`, 'info');

    for (let i = 0; i < traversalData.steps.length; i++) {
      const step = traversalData.steps[i];
      const node = this.nodeMap.get(step.node_id);

      if (node) {
        node.state = (step.step === 1) ? 'start' : 'active';
      }

      // Mark traversed edge if exists
      if (i > 0 && traversalData.traversed_edges[i - 1]) {
        const edge = traversalData.traversed_edges[i - 1];
        this.activeEdges.add(`${edge.source}-${edge.target}`);
      }

      this.draw();

      let queueStackInfo = '';
      if (type === 'BFS' && step.queue_state) {
        queueStackInfo = `<br><span style="font-size:11px; color:#5e5477;">FIFO Queue: [${step.queue_state.map(id => '#' + id).join(', ')}]</span>`;
      }

      this.addLog(`<strong>Step ${step.step}:</strong> ${step.action}${queueStackInfo}`);

      await new Promise(r => setTimeout(r, 650));

      if (node && node.state !== 'start') {
        node.state = 'visited';
      }
      this.draw();
    }

    this.addLog(`<strong>${type} Completed!</strong> Traversed ${traversalData.visited_count} connected books.`, 'success');
  }

  resetStates() {
    this.nodes.forEach(n => n.state = 'default');
    this.activeEdges.clear();
    this.draw();
  }

  addLog(html, type = 'normal') {
    if (!this.logContainer) return;
    const entry = document.createElement('div');
    entry.style.padding = '8px 12px';
    entry.style.borderRadius = '6px';
    entry.style.marginBottom = '6px';
    entry.style.fontSize = '12px';
    entry.style.lineHeight = '1.4';

    if (type === 'success') {
      entry.style.background = '#ecfdf5';
      entry.style.color = '#065f46';
      entry.style.border = '1px solid #a7f3d0';
    } else if (type === 'info') {
      entry.style.background = '#f1ecfa';
      entry.style.color = '#543793';
      entry.style.border = '1px solid #ded3f5';
    } else {
      entry.style.background = '#faf8fe';
      entry.style.color = '#271e3d';
      entry.style.border = '1px solid #e6def7';
    }

    entry.innerHTML = html;
    this.logContainer.appendChild(entry);
    this.logContainer.scrollTop = this.logContainer.scrollHeight;
  }
}

// Global initializer
window.InteractiveGraphVis = InteractiveGraphVis;
