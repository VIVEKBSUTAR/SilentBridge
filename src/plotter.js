/**
   High-Performance Canvas-based Real-time Oscilloscope Plotter
   Optimized for high-frequency (20Hz) incoming serial data.
 */
export class RealtimePlotter {
  /**
   * @param {HTMLCanvasElement} canvas - The canvas element to draw on
   * @param {number} maxPoints - Maximum history length (horizontal resolution)
   */
  constructor(canvas, maxPoints = 250) {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d');
    this.maxPoints = maxPoints;
    
    // Set up channel buffers
    this.channels = {
      thumb:  { data: [], color: '#ec4899', width: 2, dashed: false },
      index:  { data: [], color: '#3b82f6', width: 2, dashed: false },
      middle: { data: [], color: '#06b6d4', width: 2, dashed: false },
      ring:   { data: [], color: '#eab308', width: 2, dashed: false },
      pinky:  { data: [], color: '#8b5cf6', width: 2, dashed: false },
      roll:   { data: [], color: '#06b6d4', width: 1.5, dashed: true },
      pitch:  { data: [], color: '#a855f7', width: 1.5, dashed: true }
    };

    this.resize();
  }

  /**
   * Resizes the canvas mapping to support high-DPI (Retina) screens without blurring.
   */
  resize() {
    const rect = this.canvas.parentElement.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    
    this.canvas.width = rect.width * dpr;
    this.canvas.height = rect.height * dpr;
    this.canvas.style.width = `${rect.width}px`;
    this.canvas.style.height = `${rect.height}px`;
    
    this.ctx.scale(dpr, dpr);
    this.width = rect.width;
    this.height = rect.height;
  }

  /**
   * Pushes a new dataset frame into the scrolling buffers.
   * @param {object} values - Object containing channel values { thumb, index, middle, ring, pinky, roll, pitch }
   */
  addData(values) {
    Object.keys(this.channels).forEach((key) => {
      const channel = this.channels[key];
      const val = values[key];
      
      if (typeof val === 'number' && !isNaN(val)) {
        channel.data.push(val);
        if (channel.data.length > this.maxPoints) {
          channel.data.shift();
        }
      }
    });

    this.draw();
  }

  /**
   * Draws the background oscilloscope grid lines and text markers.
   */
  drawGrid() {
    const ctx = this.ctx;
    const w = this.width;
    const h = this.height;

    // Draw background
    ctx.fillStyle = '#080c14'; // Matching CSS body
    ctx.fillRect(0, 0, w, h);

    // Draw Grid Lines (Vertical columns)
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.03)';
    ctx.lineWidth = 1;
    ctx.setLineDash([]);
    
    const numCols = 10;
    for (let i = 1; i < numCols; i++) {
      const x = (w / numCols) * i;
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, h);
      ctx.stroke();
    }

    // Draw Grid Lines (Horizontal rows)
    const numRows = 6;
    for (let i = 1; i < numRows; i++) {
      const y = (h / numRows) * i;
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(w, y);
      ctx.stroke();
    }

    // Zero-axis dashed divider line for Roll/Pitch (center)
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.08)';
    ctx.setLineDash([4, 4]);
    ctx.beginPath();
    ctx.moveTo(0, h / 2);
    ctx.lineTo(w, h / 2);
    ctx.stroke();
    ctx.setLineDash([]);

    // Draw text indicators
    ctx.fillStyle = 'rgba(148, 163, 184, 0.4)';
    ctx.font = '9px monospace';
    ctx.fillText('ORIENTATION (+180°)', 10, 15);
    ctx.fillText('0° (CENTER)', 10, h / 2 - 5);
    ctx.fillText('ORIENTATION (-180°)', 10, h - 8);

    ctx.textAlign = 'right';
    ctx.fillText('FINGERS (100% BENT)', w - 10, 15);
    ctx.fillText('FINGERS (STRAIGHT)', w - 10, h - 8);
    ctx.textAlign = 'left';
  }

  /**
   * Main render method. Draws the oscilloscope background grid and plots all active channels.
   */
  draw() {
    const ctx = this.ctx;
    const w = this.width;
    const h = this.height;

    // 1. Reset and draw grid
    ctx.clearRect(0, 0, w, h);
    this.drawGrid();

    // 2. Draw lines for each channel
    Object.keys(this.channels).forEach((key) => {
      const channel = this.channels[key];
      const buffer = channel.data;
      if (buffer.length < 2) return;

      ctx.beginPath();
      ctx.strokeStyle = channel.color;
      ctx.lineWidth = channel.width;
      
      // Cyberpunk trace neon glow effect
      ctx.shadowBlur = 4;
      ctx.shadowColor = channel.color;

      if (channel.dashed) {
        ctx.setLineDash([3, 3]);
      } else {
        ctx.setLineDash([]);
      }

      // Plot points
      for (let i = 0; i < buffer.length; i++) {
        const val = buffer[i];
        
        // Calculate X coordinate (scroll right to left)
        // Ensure the graph scales to fit the width cleanly
        const x = (i / (this.maxPoints - 1)) * w;
        
        // Calculate Y coordinate based on variable type
        let y = h / 2;
        if (key === 'roll' || key === 'pitch') {
          // Range: -180 to 180 degrees. Map directly to full height (center is 0)
          // Clamped to avoid line bleeding
          const clamped = Math.max(-180, Math.min(180, val));
          // -180 is bottom (h - margin), +180 is top (margin)
          y = h / 2 - (clamped / 180.0) * (h / 2 - 12);
        } else {
          // Range: 0.0 to 1.0 (normalized finger bending factor)
          // Map to 80% height with margins to avoid drawing on outer boundaries
          const clamped = Math.max(0, Math.min(1, val));
          y = h - (clamped * (h - 24)) - 12;
        }

        if (i === 0) {
          ctx.moveTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }
      }
      
      ctx.stroke();
    });

    // Reset shadow properties to avoid affecting other operations
    ctx.shadowBlur = 0;
    ctx.setLineDash([]);
  }

  /**
   * Resets all buffer histories.
   */
  clear() {
    Object.keys(this.channels).forEach((key) => {
      this.channels[key].data = [];
    });
    this.draw();
  }
}
