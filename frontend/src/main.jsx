import React, { useEffect, useMemo, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { Activity, AlertTriangle, HeartPulse, RotateCcw, Sparkles } from 'lucide-react';
import './styles.css';

const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';
const DISCLAIMER = 'For decision support / educational purposes only. Not a substitute for formal diagnostic imaging.';
const TARGETS = [
  ['cad', 'Overall CAD'],
  ['lad', 'LAD stenosis'],
  ['lcx', 'LCX stenosis'],
  ['rca', 'RCA stenosis'],
];

function emptyPatient(schema) {
  return Object.fromEntries(schema.map((feature) => [feature.name, feature.default]));
}

function riskColor(probability = 0) {
  if (probability >= 0.7) return '#d94b4b';
  if (probability >= 0.4) return '#d8a63a';
  return '#2f9f72';
}

function App() {
  const [schema, setSchema] = useState([]);
  const [samples, setSamples] = useState([]);
  const [metrics, setMetrics] = useState(null);
  const [patient, setPatient] = useState({});
  const [prediction, setPrediction] = useState(null);
  const [selected, setSelected] = useState('lad');
  const [explain, setExplain] = useState(null);
  const [counterfactual, setCounterfactual] = useState(null);
  const [busy, setBusy] = useState(true);
  const [error, setError] = useState('');
  const [plain, setPlain] = useState(false);

  useEffect(() => {
    Promise.all([
      fetch(`${API_URL}/schema`).then((res) => res.json()),
      fetch(`${API_URL}/sample-patients`).then((res) => res.json()),
      fetch(`${API_URL}/metrics`).then((res) => res.json()),
    ])
      .then(([schemaData, sampleData, metricData]) => {
        setSchema(schemaData.features);
        setSamples(sampleData.patients);
        setMetrics(metricData);
        setPatient(emptyPatient(schemaData.features));
      })
      .catch(() => setError('Backend is not reachable. Start the FastAPI server and refresh.'))
      .finally(() => setBusy(false));
  }, []);

  useEffect(() => {
    if (!schema.length) return;
    const timer = window.setTimeout(() => {
      setError('');
      fetch(`${API_URL}/predict`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ patient }),
      })
        .then((res) => res.json())
        .then(setPrediction)
        .catch(() => setError('Prediction request failed. The server may still be waking up.'));
    }, 350);
    return () => window.clearTimeout(timer);
  }, [patient, schema]);

  useEffect(() => {
    if (!prediction) return;
    fetch(`${API_URL}/explain`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ patient, target: selected }),
    })
      .then((res) => res.json())
      .then(setExplain)
      .catch(() => setExplain(null));
  }, [patient, selected, prediction]);

  const groups = useMemo(() => {
    return schema.reduce((acc, feature) => {
      acc[feature.group] ||= [];
      acc[feature.group].push(feature);
      return acc;
    }, {});
  }, [schema]);

  function updateFeature(name, value) {
    setPatient((current) => ({ ...current, [name]: value }));
    setCounterfactual(null);
  }

  function loadSample(id) {
    const sample = samples.find((item) => item.id === id);
    if (sample) {
      setPatient(sample.patient);
      setCounterfactual(null);
    }
  }

  function resetPatient() {
    setPatient(emptyPatient(schema));
    setCounterfactual(null);
  }

  function runCounterfactual() {
    fetch(`${API_URL}/counterfactual`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ patient, target: selected }),
    })
      .then((res) => res.json())
      .then(setCounterfactual)
      .catch(() => setError('What-if request failed.'));
  }

  if (busy) {
    return <main className="loading">Loading Hriday.Ai...</main>;
  }

  return (
    <main>
      <header className="topbar">
        <div>
          <span className="brand">Hriday.Ai</span>
          <p>Cardiovascular risk visualization dashboard</p>
        </div>
        <button className="ghost" onClick={() => setPlain((value) => !value)}>
          {plain ? 'Clinician view' : 'Plain-language view'}
        </button>
      </header>

      <section className="disclaimer">
        <AlertTriangle size={18} />
        <span>{DISCLAIMER}</span>
      </section>

      {error && <section className="error">{error}</section>}

      <section className="shell">
        <div className="visualPanel">
          <HeartScene prediction={prediction} selected={selected} onSelect={setSelected} />
          <div className="sampleBar">
            <select onChange={(event) => loadSample(event.target.value)} defaultValue="">
              <option value="" disabled>Load sample patient</option>
              {samples.map((sample) => <option key={sample.id} value={sample.id}>{sample.label}</option>)}
            </select>
            <button onClick={resetPatient}><RotateCcw size={16} />Reset</button>
            <button onClick={runCounterfactual}><Sparkles size={16} />Suggest changes</button>
          </div>
        </div>

        <aside className="dashboard">
          <section className="cards">
            {TARGETS.map(([key, label]) => (
              <RiskCard
                key={key}
                id={key}
                label={label}
                active={selected === key}
                value={prediction?.targets?.[key]}
                onClick={() => setSelected(key)}
              />
            ))}
          </section>

          <section className="detail">
            <h2>{TARGETS.find(([key]) => key === selected)?.[1]}</h2>
            <p className="muted">{plain ? 'Top factors that moved this estimate.' : 'Prototype explanation components. Dataset-trained SHAP values will replace these.'}</p>
            <div className="bars">
              {explain?.contributions?.map((item) => (
                <div className="barRow" key={item.feature}>
                  <span>{item.label}</span>
                  <div className="barTrack">
                    <div
                      className={item.impact >= 0 ? 'bar plus' : 'bar minus'}
                      style={{ width: `${Math.min(100, Math.abs(item.impact) * 70)}%` }}
                    />
                  </div>
                  <strong>{item.impact}</strong>
                </div>
              ))}
            </div>
            {patient.region_rwma !== 'none' && <p className="hint">RWMA is shown only as a clinical hint, not anatomical lesion evidence.</p>}
            {counterfactual && (
              <div className="whatif">
                <strong>What-if change: {(counterfactual.delta * 100).toFixed(1)} percentage points</strong>
                <p>Before {Math.round(counterfactual.before * 100)}%, after {Math.round(counterfactual.after * 100)}%.</p>
              </div>
            )}
          </section>
        </aside>
      </section>

      <section className="formAndMetrics">
        <section className="formPanel">
          <h2>Patient inputs</h2>
          {Object.entries(groups).map(([group, features]) => (
            <fieldset key={group}>
              <legend>{group}</legend>
              <div className="fieldGrid">
                {features.map((feature) => (
                  <FeatureInput key={feature.name} feature={feature} value={patient[feature.name]} onChange={updateFeature} />
                ))}
              </div>
            </fieldset>
          ))}
        </section>

        <section className="metricsPanel">
          <h2>Validation status</h2>
          <p>{metrics?.note}</p>
          <table>
            <thead><tr><th>Target</th><th>ROC-AUC</th><th>F1</th><th>Recall</th></tr></thead>
            <tbody>
              {Object.entries(metrics?.targets || {}).map(([key, row]) => (
                <tr key={key}><td>{key.toUpperCase()}</td><td>{row.roc_auc}</td><td>{row.f1}</td><td>{row.recall}</td></tr>
              ))}
            </tbody>
          </table>
        </section>
      </section>

      <footer>{DISCLAIMER}</footer>
    </main>
  );
}

function HeartScene({ prediction, selected, onSelect }) {
  const vessel = (id) => prediction?.targets?.[id]?.probability || 0.2;
  const vessels = [
    ['lad', 'M 240 110 C 225 165 222 225 240 310', 'LAD'],
    ['lcx', 'M 215 170 C 150 168 115 215 102 270', 'LCX'],
    ['rca', 'M 265 160 C 335 172 356 235 326 302', 'RCA'],
  ];
  return (
    <section className="heartStage">
      <div className="sceneTitle"><HeartPulse size={20} />Interactive vessel risk map</div>
      <svg viewBox="0 0 460 420" role="img" aria-label="Heart and coronary arteries">
        <path className="heartShape" d="M230 112 C190 55 94 74 80 165 C65 265 160 333 230 378 C300 333 395 265 380 165 C366 74 270 55 230 112 Z" />
        <path className="heartShade" d="M230 126 C208 89 146 96 130 155 C111 225 180 298 230 336 C280 298 349 225 330 155 C314 96 252 89 230 126 Z" />
        {vessels.map(([id, path, label]) => (
          <g key={id} onClick={() => onSelect(id)} className={selected === id ? 'vessel active' : 'vessel'}>
            <path d={path} stroke={riskColor(vessel(id))} strokeWidth={8 - vessel(id) * 3} />
            <circle cx={id === 'lad' ? 240 : id === 'lcx' ? 104 : 326} cy={id === 'lad' ? 310 : id === 'lcx' ? 270 : 302} r="6" fill={riskColor(vessel(id))} />
            <text x={id === 'lad' ? 250 : id === 'lcx' ? 72 : 334} y={id === 'lad' ? 318 : id === 'lcx' ? 276 : 308}>{label} {Math.round(vessel(id) * 100)}%</text>
          </g>
        ))}
      </svg>
      <p>Click a vessel or card to focus its explanation.</p>
    </section>
  );
}

function RiskCard({ id, label, value, active, onClick }) {
  const probability = value?.probability || 0;
  return (
    <button className={active ? 'riskCard active' : 'riskCard'} onClick={onClick}>
      <span>{label}</span>
      <strong style={{ color: riskColor(probability) }}>{Math.round(probability * 100)}%</strong>
      <small>{value ? `${Math.round(value.ci_low * 100)}-${Math.round(value.ci_high * 100)}% CI` : 'Waiting'}</small>
      {value?.low_confidence && <em>wide CI</em>}
    </button>
  );
}

function FeatureInput({ feature, value, onChange }) {
  if (feature.type === 'boolean') {
    return (
      <label className="toggle">
        <input type="checkbox" checked={Boolean(value)} onChange={(event) => onChange(feature.name, event.target.checked)} />
        <span>{feature.label}</span>
      </label>
    );
  }
  if (feature.type === 'category') {
    return (
      <label>
        <span>{feature.label}</span>
        <select value={value} onChange={(event) => onChange(feature.name, event.target.value)}>
          {feature.allowed_values.map((option) => <option key={option} value={option}>{option}</option>)}
        </select>
      </label>
    );
  }
  return (
    <label>
      <span>{feature.label} <small>{feature.unit}</small></span>
      <input
        type="range"
        min={feature.min}
        max={feature.max}
        value={value}
        onChange={(event) => onChange(feature.name, Number(event.target.value))}
      />
      <strong>{value}</strong>
    </label>
  );
}

createRoot(document.getElementById('root')).render(<App />);
