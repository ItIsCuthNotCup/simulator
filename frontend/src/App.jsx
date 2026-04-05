import { useState, useRef, useCallback, useEffect } from 'react';
import SimulationCanvas from './components/SimulationCanvas';
import ParameterPanel from './components/ParameterPanel';
import MetricsPanel from './components/MetricsPanel';
import './App.css';

const API_URL = 'http://localhost:8000';

const EXAMPLE_PROMPTS = [
  'simulate people spreading a rumor in a crowded space',
  'simulate aggressive drivers on a highway',
  'simulate a crowd evacuating a building',
  'simulate product adoption in a market',
];

export default function App() {
  const [prompt, setPrompt] = useState('');
  const [loading, setLoading] = useState(false);
  const [spec, setSpec] = useState(null);
  const [result, setResult] = useState(null);
  const [currentStep, setCurrentStep] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [paramValues, setParamValues] = useState({});
  const animRef = useRef(null);
  const playRef = useRef(false);

  const frames = result?.frames || [];
  const metadata = result?.metadata || null;
  const metrics = result?.metrics || [];

  // Animation loop
  useEffect(() => {
    if (!playing || frames.length === 0) return;

    playRef.current = true;
    let step = currentStep;

    const tick = () => {
      if (!playRef.current) return;
      step = (step + 1) % frames.length;
      setCurrentStep(step);
      animRef.current = requestAnimationFrame(() => {
        setTimeout(() => {
          if (playRef.current) tick();
        }, 50);
      });
    };

    tick();

    return () => {
      playRef.current = false;
      if (animRef.current) cancelAnimationFrame(animRef.current);
    };
  }, [playing, frames.length]);

  const generate = useCallback(async (promptText) => {
    if (!promptText.trim()) return;
    setLoading(true);
    setPlaying(false);
    playRef.current = false;

    try {
      const res = await fetch(`${API_URL}/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: promptText, steps: 100 }),
      });
      const data = await res.json();
      setSpec(data.spec);
      setResult(data.result);
      setCurrentStep(0);

      const defaults = {};
      for (const p of data.spec.parameters) {
        defaults[p.name] = p.default;
      }
      setParamValues(defaults);

      setPlaying(true);
    } catch (err) {
      console.error('Generate failed:', err);
      alert('Failed to connect to backend. Is the server running on port 8000?');
    } finally {
      setLoading(false);
    }
  }, []);

  const rerun = useCallback(async () => {
    if (!spec) return;
    setLoading(true);
    setPlaying(false);
    playRef.current = false;

    try {
      const res = await fetch(`${API_URL}/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ spec, params: paramValues, steps: 100 }),
      });
      const data = await res.json();
      setResult(data.result);
      setCurrentStep(0);
      setPlaying(true);
    } catch (err) {
      console.error('Run failed:', err);
    } finally {
      setLoading(false);
    }
  }, [spec, paramValues]);

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') generate(prompt);
  };

  const handleParamChange = (name, value) => {
    setParamValues((prev) => ({ ...prev, [name]: value }));
  };

  const togglePlay = () => {
    setPlaying((p) => !p);
  };

  return (
    <div className="app">
      <div className="header">
        <h1>Prompt Simulator</h1>
        <p>Describe a system. Watch it simulate. Tweak it live.</p>
      </div>

      <div className="prompt-section">
        <input
          className="prompt-input"
          placeholder="e.g. simulate people spreading a rumor in a crowded space..."
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={loading}
        />
        <button className="run-btn" onClick={() => generate(prompt)} disabled={loading || !prompt.trim()}>
          {loading ? 'Generating...' : 'Run Simulation'}
        </button>
      </div>

      {!result && !loading && (
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 16 }}>
          {EXAMPLE_PROMPTS.map((ex) => (
            <button
              key={ex}
              onClick={() => { setPrompt(ex); generate(ex); }}
              style={{
                padding: '8px 14px', fontSize: 13, border: '1px solid #333', borderRadius: 8,
                background: '#1a1a24', color: '#aaa', cursor: 'pointer',
              }}
            >
              {ex}
            </button>
          ))}
        </div>
      )}

      <div className="main-content">
        <div className="canvas-section">
          <div className="canvas-wrapper">
            {loading ? (
              <div className="loading-spinner">
                <div className="spinner" />
                <span>Running simulation...</span>
              </div>
            ) : (
              <SimulationCanvas
                frame={frames[currentStep] || null}
                metadata={metadata}
              />
            )}
          </div>

          {frames.length > 0 && (
            <div className="playback-controls">
              <button className="playback-btn" onClick={togglePlay}>
                {playing ? 'Pause' : 'Play'}
              </button>
              <input
                type="range"
                className="step-slider"
                min={0}
                max={frames.length - 1}
                value={currentStep}
                onChange={(e) => {
                  setPlaying(false);
                  playRef.current = false;
                  setCurrentStep(parseInt(e.target.value, 10));
                }}
              />
              <span className="step-label">
                Step {currentStep + 1} / {frames.length}
              </span>
            </div>
          )}
        </div>

        <div className="sidebar">
          {spec && (
            <div className="panel">
              <h3>Simulation</h3>
              <span className="sim-type-badge">{spec.type}</span>
              <p style={{ fontSize: 13, color: '#888', marginTop: 4 }}>{spec.prompt}</p>
            </div>
          )}

          <ParameterPanel
            parameters={spec?.parameters || []}
            values={paramValues}
            onChange={handleParamChange}
            onRerun={rerun}
            loading={loading}
          />

          <MetricsPanel
            metrics={metrics}
            colors={metadata?.colors || {}}
            currentStep={currentStep}
          />
        </div>
      </div>
    </div>
  );
}
