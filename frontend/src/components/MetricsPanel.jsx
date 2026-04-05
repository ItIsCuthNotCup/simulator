import { useRef, useEffect } from 'react';

export default function MetricsPanel({ metrics, colors, currentStep }) {
  const canvasRef = useRef(null);

  useEffect(() => {
    if (!metrics || metrics.length === 0) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    const w = canvas.width;
    const h = canvas.height;

    ctx.fillStyle = '#111118';
    ctx.fillRect(0, 0, w, h);

    // Get all state keys (exclude 'step')
    const keys = Object.keys(metrics[0]).filter((k) => k !== 'step');
    const maxVal = Math.max(...metrics.map((m) => Math.max(...keys.map((k) => m[k] || 0))));

    if (maxVal === 0) return;

    const stepW = w / metrics.length;

    for (const key of keys) {
      const color = colors[key] || '#888';
      ctx.strokeStyle = color;
      ctx.lineWidth = 2;
      ctx.beginPath();

      for (let i = 0; i < metrics.length; i++) {
        const x = i * stepW;
        const y = h - (metrics[i][key] / maxVal) * (h - 10) - 5;
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      }
      ctx.stroke();
    }

    // Current step indicator
    if (currentStep >= 0 && currentStep < metrics.length) {
      const x = currentStep * stepW;
      ctx.strokeStyle = '#ffffff44';
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, h);
      ctx.stroke();
    }
  }, [metrics, colors, currentStep]);

  if (!metrics || metrics.length === 0) return null;

  const keys = Object.keys(metrics[0]).filter((k) => k !== 'step');

  return (
    <div className="panel">
      <h3>Metrics</h3>
      <div className="legend">
        {keys.map((key) => (
          <div key={key} className="legend-item">
            <div className="legend-dot" style={{ background: colors[key] || '#888' }} />
            <span>{key}</span>
          </div>
        ))}
      </div>
      <div className="metrics-chart">
        <canvas ref={canvasRef} width={268} height={120} style={{ width: '100%', height: '120px' }} />
      </div>
    </div>
  );
}
