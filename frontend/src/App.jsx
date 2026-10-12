import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { HeartScene } from './HeartScene';
import {
  API_URL,
  DISCLAIMER,
  figureUrl,
  getMetrics,
  getSamples,
  getSchema,
  postCounterfactual,
  postExplain,
  postPredict,
} from './api';
import { COPY } from './i18n';

const TARGETS = [
  ['cad', 'cad'],
  ['lad', 'lad'],
  ['lcx', 'lcx'],
  ['rca', 'rca'],
];

function emptyPatient(schema) {
  return Object.fromEntries(schema.map((f) => [f.name, f.default]));
}

function fmtPct(p) {
  if (p == null || Number.isNaN(p)) return '—';
  return `${Math.round(p * 100)}%`;
}

function meanStd(obj) {
  if (!obj) return '—';
  if (typeof obj.mean === 'number') return `${obj.mean.toFixed(3)} ± ${obj.std.toFixed(3)}`;
  return String(obj);
}

export default function App() {
  const [lang, setLang] = useState('en');
  const [plain, setPlain] = useState(false);
  const [theme, setTheme] = useState('dark');
  const [tab, setTab] = useState('live');
  const [schema, setSchema] = useState([]);
  const [samples, setSamples] = useState([]);
  const [metrics, setMetrics] = useState(null);
  const [patient, setPatient] = useState({});
  const [baseline, setBaseline] = useState(null);
  const [baselinePrediction, setBaselinePrediction] = useState(null);
  const [prediction, setPrediction] = useState(null);
  const [selected, setSelected] = useState('lad');
  const [explain, setExplain] = useState(null);
  const [counterfactual, setCounterfactual] = useState(null);
  const [busy, setBusy] = useState(true);
  const [error, setError] = useState('');
  const [waking, setWaking] = useState(false);
  const [pulseOn, setPulseOn] = useState(true);
  const [autoRotate, setAutoRotate] = useState(false);
  const [demoCaption, setDemoCaption] = useState('');
  const demoTimer = useRef([]);
  const t = COPY[lang] || COPY.en;

  const loadCore = useCallback(async () => {
    setWaking(true);
    try {
      const [schemaData, sampleData, metricData] = await Promise.all([
        getSchema(),
        getSamples(),
        getMetrics(),
      ]);
      setSchema(schemaData.features);
      setSamples(sampleData.patients);
      setMetrics(metricData);
      const next = emptyPatient(schemaData.features);
      setPatient(next);
      setError('');
    } catch (err) {
      setError(err.message || t.waking);
    } finally {
      setBusy(false);
      setWaking(false);
    }
  }, [t.waking]);

  useEffect(() => {
    loadCore();
  }, [loadCore]);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
  }, [theme]);

  useEffect(() => {
    if (!schema.length) return undefined;
    const timer = window.setTimeout(async () => {
      try {
        const pred = await postPredict(patient);
        setPrediction(pred);
        setError('');
      } catch (err) {
        setError(err.message.includes('Failed') ? t.waking : err.message);
      }
    }, 400);
    return () => window.clearTimeout(timer);
  }, [patient, schema, t.waking]);

  useEffect(() => {
    if (!prediction) return undefined;
    let cancelled = false;
    postExplain(patient, selected)
      .then((data) => {
        if (!cancelled) setExplain(data);
      })
      .catch(() => {
        if (!cancelled) setExplain(null);
      });
    return () => {
      cancelled = true;
    };
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
      setPatient({ ...emptyPatient(schema), ...sample.patient });
      setCounterfactual(null);
    }
  }

  function resetPatient() {
    setPatient(emptyPatient(schema));
    setCounterfactual(null);
    setBaseline(null);
  }

  async function runCounterfactual() {
    try {
      const data = await postCounterfactual(patient, selected);
      setCounterfactual(data);
      if (!baseline) {
        setBaseline(patient);
        setBaselinePrediction(prediction);
      }
      setPatient(data.patient);
    } catch (err) {
      setError(err.message);
    }
  }

  function toggleWhatIf() {
    if (baseline) {
      setPatient(baseline);
      setBaseline(null);
      setBaselinePrediction(null);
      setCounterfactual(null);
    } else {
      setBaseline(patient);
      setBaselinePrediction(prediction);
    }
  }

  function clearDemo() {
    demoTimer.current.forEach((id) => window.clearTimeout(id));
    demoTimer.current = [];
    setAutoRotate(false);
    setDemoCaption('');
  }

  function startGuidedDemo() {
    clearDemo();
    const high = samples.find((s) => s.id === 'sample-high') || samples[samples.length - 1];
    if (!high) return;
    const later = (ms, fn) => {
      const id = window.setTimeout(fn, ms);
      demoTimer.current.push(id);
    };
    setDemoCaption('1/6 Loading a higher-risk synthetic example.');
    loadSample(high.id);
    setAutoRotate(true);
    later(5000, () => {
      setAutoRotate(false);
      setSelected('lad');
      setDemoCaption('2/6 Focus LAD — front groove, stenosis probability mapped as color + local narrowing.');
    });
    later(10000, () => {
      setSelected('lcx');
      setDemoCaption('3/6 Focus LCX — wraps left and back.');
    });
    later(15000, () => {
      setSelected('rca');
      setDemoCaption('4/6 Focus RCA — right AV groove. Click any vessel anytime.');
    });
    later(20000, () => {
      setSelected('cad');
      setTab('live');
      setDemoCaption('5/6 SHAP explanation for overall CAD — why this score moved.');
    });
    later(26000, () => {
      setDemoCaption('6/6 Illustrative what-if on modifiable labs/BP. Not medical advice.');
      runCounterfactual();
    });
    later(34000, () => {
      setDemoCaption('Demo complete. Explore the form, metrics tab, and 3D view.');
      setAutoRotate(false);
    });
  }

  if (busy) {
    return (
      <main className="loading">
        <div className="skeleton title" />
        <p>{waking ? t.waking : 'Loading HRIDAYA.AI…'}</p>
      </main>
    );
  }

  const delta = baseline && prediction && baselinePrediction
    ? Object.fromEntries(
        TARGETS.map(([key]) => {
          const now = prediction.targets?.[key]?.probability;
          const before = baselinePrediction.targets?.[key]?.probability;
          return [key, typeof now === 'number' && typeof before === 'number' ? now - before : null];
        }),
      )
    : null;

  return (
    <main>
      <header className="topbar">
        <div>
          <span className="brand">HRIDAYA.AI</span>
          <p>{t.brandSub}</p>
        </div>
        <div className="topActions">
          <button type="button" className="ghost" onClick={() => setPlain((v) => !v)}>
            {plain ? t.clinician : t.plain}
          </button>
          <button type="button" className="ghost" onClick={() => setLang((v) => (v === 'en' ? 'hi' : 'en'))}>
            {t.hindi}
          </button>
          <button type="button" className="ghost" onClick={() => setTheme((v) => (v === 'dark' ? 'light' : 'dark'))}>
            {theme === 'dark' ? 'Light' : 'Dark'}
          </button>
        </div>
      </header>

      <section className="disclaimer" role="note">
        <strong>Disclaimer.</strong> {DISCLAIMER}
      </section>

      {error && (
        <section className="error">
          {error}
          <button type="button" onClick={loadCore}>
            Retry
          </button>
        </section>
      )}
      {demoCaption && <section className="demoBanner">{demoCaption}</section>}

      <nav className="tabs" aria-label="Views">
        <button type="button" className={tab === 'live' ? 'on' : ''} onClick={() => setTab('live')}>
          Live
        </button>
        <button type="button" className={tab === 'metrics' ? 'on' : ''} onClick={() => setTab('metrics')}>
          {t.metrics}
        </button>
      </nav>

      {tab === 'live' ? (
        <section className="shell">
          <div className="visualPanel">
            <HeartScene
              prediction={prediction}
              selected={selected}
              onSelect={setSelected}
              pulseRate={patient.PR}
              pulseOn={pulseOn}
              autoRotate={autoRotate}
            />
            <div className="sampleBar">
              <select onChange={(e) => loadSample(e.target.value)} defaultValue="" aria-label={t.loadSample}>
                <option value="" disabled>
                  {t.loadSample}
                </option>
                {samples.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.label}
                  </option>
                ))}
              </select>
              <button type="button" onClick={resetPatient}>
                {t.reset}
              </button>
              <button type="button" onClick={toggleWhatIf}>
                {baseline ? t.exitWhatIf : t.whatIf}
              </button>
              <button type="button" onClick={runCounterfactual}>
                {t.suggest}
              </button>
              <button type="button" className="accent" onClick={startGuidedDemo}>
                {t.guided}
              </button>
              <label className="toggle compact">
                <input type="checkbox" checked={pulseOn} onChange={(e) => setPulseOn(e.target.checked)} />
                {t.pulse}
              </label>
            </div>
          </div>

          <aside className="dashboard">
            <section className="cards">
              {TARGETS.map(([key, copyKey]) => (
                <RiskCard
                  key={key}
                  id={key}
                  label={t[copyKey]}
                  active={selected === key}
                  value={prediction?.targets?.[key]}
                  onClick={() => setSelected(key)}
                />
              ))}
            </section>
            <section className="detail">
              <h2>{t.detail} — {t[selected]}</h2>
              <p className="muted">
                {plain
                  ? 'These are the strongest factors that pushed this estimate up or down.'
                  : 'SHAP values for this patient and target. Positive values increase predicted probability.'}
              </p>
              {explain?.contributions ? (
                <ResponsiveContainer width="100%" height={220}>
                  <BarChart
                    data={explain.contributions.map((c) => ({
                      name: c.label,
                      shap: c.shap,
                    }))}
                    layout="vertical"
                    margin={{ left: 8, right: 12, top: 8, bottom: 8 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
                    <XAxis type="number" />
                    <YAxis type="category" dataKey="name" width={118} tick={{ fontSize: 11 }} />
                    <Tooltip />
                    <Bar dataKey="shap">
                      {explain.contributions.map((c) => (
                        <Cell key={c.feature} fill={c.shap >= 0 ? '#d94b4b' : '#2f9f72'} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="skeleton chart" />
              )}
              <ul className="sentences">
                {(explain?.sentences || []).map((s) => (
                  <li key={s}>{s}</li>
                ))}
              </ul>
              {Number(patient.Region_RWMA) > 0 && <p className="hint">{t.rwma}</p>}
              {counterfactual && (
                <div className="whatif">
                  <strong>
                    {counterfactual.disclaimer} Δ {(counterfactual.delta * 100).toFixed(1)} pp
                  </strong>
                  <p>
                    Before {fmtPct(counterfactual.before)} → after {fmtPct(counterfactual.after)}
                  </p>
                </div>
              )}
              {baseline && delta && (
                <div className="whatif" aria-live="polite">
                  <strong>Change from baseline (percentage points)</strong>
                  <ul>
                    {TARGETS.map(([key]) => (
                      <li key={key}>
                        {t[key]}: {delta[key] == null ? '—' : `${delta[key] > 0 ? '+' : ''}${(delta[key] * 100).toFixed(1)} pp`}
                      </li>
                    ))}
                  </ul>
                  <p className="muted">Changed fields are highlighted in the form.</p>
                </div>
              )}
            </section>
          </aside>
        </section>
      ) : (
        <MetricsPanel metrics={metrics} t={t} />
      )}

      {tab === 'live' && (
        <section className="formPanel">
          <h2>{t.inputs}</h2>
          {Object.entries(groups).map(([group, features]) => (
            <fieldset key={group}>
              <legend>{group}</legend>
              <div className="fieldGrid">
                {features.map((feature) => (
                  <FeatureInput
                    key={feature.name}
                    feature={feature}
                    value={patient[feature.name]}
                    changed={baseline ? baseline[feature.name] !== patient[feature.name] : false}
                    onChange={updateFeature}
                  />
                ))}
              </div>
            </fieldset>
          ))}
        </section>
      )}

      <footer>
        <p>{DISCLAIMER}</p>
        <p className="muted">{t.limitations} API {API_URL}</p>
      </footer>
    </main>
  );
}

function RiskCard({ id, label, value, active, onClick }) {
  const p = value?.probability || 0;
  return (
    <button type="button" className={active ? 'riskCard active' : 'riskCard'} onClick={onClick}>
      <span>
        {label} <em className="icon">{id === 'cad' ? '♥' : id.toUpperCase()}</em>
      </span>
      <strong>{fmtPct(p)}</strong>
      <small>{value ? `${fmtPct(value.ci_low)}–${fmtPct(value.ci_high)} CI` : 'Waiting'}</small>
      {value?.low_confidence && <em className="badge">wide CI</em>}
    </button>
  );
}

function FeatureInput({ feature, value, onChange, changed }) {
  const hint = feature.hint ? <em className="hintInline">{feature.hint}</em> : null;
  if (feature.type === 'boolean') {
    return (
      <label className={changed ? 'toggle changed' : 'toggle'}>
        <input
          type="checkbox"
          checked={Boolean(Number(value))}
          onChange={(e) => onChange(feature.name, e.target.checked ? 1 : 0)}
        />
        <span>
          {feature.label} {hint}
        </span>
      </label>
    );
  }
  if (feature.type === 'category') {
    return (
      <label className={changed ? 'changed' : ''}>
        <span>
          {feature.label} {hint}
        </span>
        <select value={value} onChange={(e) => onChange(feature.name, e.target.value)}>
          {(feature.allowed_values || []).map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </select>
      </label>
    );
  }
  return (
    <label className={changed ? 'changed' : ''}>
      <span>
        {feature.label} <small>{feature.unit}</small> {hint}
      </span>
      <input
        type="range"
        min={feature.min}
        max={feature.max}
        step={feature.name === 'BMI' || feature.name === 'CR' ? 0.1 : 1}
        value={value ?? feature.default}
        onChange={(e) => onChange(feature.name, Number(e.target.value))}
      />
      <strong>{value}</strong>
    </label>
  );
}

function MetricsPanel({ metrics, t }) {
  const figures = metrics?.figures || [];
  return (
    <section className="metricsPanel wide">
      <h2>{t.metrics}</h2>
      <p>{t.limitations}</p>
      <table>
        <thead>
          <tr>
            <th>Target</th>
            <th>Model</th>
            <th>ROC-AUC</th>
            <th>F1</th>
            <th>Recall</th>
            <th>Accuracy</th>
            <th>Precision</th>
          </tr>
        </thead>
        <tbody>
          {Object.entries(metrics?.targets || {}).map(([key, row]) => (
            <tr key={key}>
              <td>{key.toUpperCase()}</td>
              <td>{row.chosen_model}</td>
              <td>{meanStd(row.roc_auc)}</td>
              <td>{meanStd(row.f1)}</td>
              <td>{meanStd(row.recall)}</td>
              <td>{meanStd(row.accuracy)}</td>
              <td>{meanStd(row.precision)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <div className="figureGrid">
        {figures.map((name) => (
          <figure key={name}>
            <img src={figureUrl(name)} alt={name} />
            <figcaption>{name}</figcaption>
          </figure>
        ))}
      </div>
    </section>
  );
}
