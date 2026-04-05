export default function ParameterPanel({ parameters, values, onChange, onRerun, loading }) {
  if (!parameters || parameters.length === 0) return null;

  return (
    <div className="panel">
      <h3>Parameters</h3>
      {parameters.map((param) => {
        const value = values[param.name] ?? param.default;
        const isFloat = param.step < 1;
        return (
          <div key={param.name} className="param-row">
            <div className="param-label">
              <span>{param.label}</span>
              <span className="param-value">{isFloat ? value.toFixed(2) : value}</span>
            </div>
            <input
              type="range"
              className="param-slider"
              min={param.min}
              max={param.max}
              step={param.step}
              value={value}
              onChange={(e) => {
                const v = isFloat ? parseFloat(e.target.value) : parseInt(e.target.value, 10);
                onChange(param.name, v);
              }}
            />
          </div>
        );
      })}
      <button className="rerun-btn" onClick={onRerun} disabled={loading}>
        {loading ? 'Running...' : 'Re-run Simulation'}
      </button>
    </div>
  );
}
