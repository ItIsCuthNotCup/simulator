import { useRef, useEffect } from 'react';

const CANVAS_SIZE = 600;

export default function SimulationCanvas({ frame, metadata }) {
  const canvasRef = useRef(null);

  useEffect(() => {
    if (!frame || !metadata) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    const { width, height, colors } = metadata;

    const cellW = CANVAS_SIZE / width;
    const cellH = CANVAS_SIZE / height;

    // Clear
    ctx.fillStyle = '#111118';
    ctx.fillRect(0, 0, CANVAS_SIZE, CANVAS_SIZE);

    // Draw grid lines (subtle)
    ctx.strokeStyle = '#1a1a28';
    ctx.lineWidth = 0.5;
    for (let x = 0; x <= width; x++) {
      ctx.beginPath();
      ctx.moveTo(x * cellW, 0);
      ctx.lineTo(x * cellW, CANVAS_SIZE);
      ctx.stroke();
    }
    for (let y = 0; y <= height; y++) {
      ctx.beginPath();
      ctx.moveTo(0, y * cellH);
      ctx.lineTo(CANVAS_SIZE, y * cellH);
      ctx.stroke();
    }

    // Draw agents
    const radius = Math.max(2, Math.min(cellW, cellH) * 0.4);
    for (const agent of frame.agents) {
      const color = colors[agent.state] || '#ffffff';
      const cx = agent.x * cellW + cellW / 2;
      const cy = agent.y * cellH + cellH / 2;

      ctx.beginPath();
      ctx.arc(cx, cy, radius, 0, Math.PI * 2);
      ctx.fillStyle = color;
      ctx.fill();

      // Glow effect for certain states
      if (agent.state === 'infected' || agent.state === 'aggressive' || agent.state === 'adopted') {
        ctx.beginPath();
        ctx.arc(cx, cy, radius * 1.8, 0, Math.PI * 2);
        ctx.fillStyle = color.replace(')', ', 0.15)').replace('rgb', 'rgba');
        // Use hex alpha instead
        ctx.fillStyle = color + '26';
        ctx.fill();
      }
    }
  }, [frame, metadata]);

  if (!frame) {
    return (
      <div className="empty-state">
        <div className="icon">&#x1F52C;</div>
        <p>Enter a prompt and click "Run Simulation"</p>
      </div>
    );
  }

  return (
    <canvas
      ref={canvasRef}
      width={CANVAS_SIZE}
      height={CANVAS_SIZE}
      style={{ width: '100%', maxWidth: CANVAS_SIZE, height: 'auto', aspectRatio: '1' }}
    />
  );
}
