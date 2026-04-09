import { useEffect, useState, useRef, useCallback } from "react";
import { getMetrics, startSimulation } from "./Services/api";
import "./App.css";

// ─── tiny sparkline component ───────────────────────────────────────────────
function Sparkline({ data, color, height = 48, fill = true }) {
  const canvasRef = useRef(null);
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !data || data.length < 2) return;
    const ctx = canvas.getContext("2d");
    const W = canvas.width, H = canvas.height;
    ctx.clearRect(0, 0, W, H);
    const min = Math.min(...data), max = Math.max(...data);
    const range = max - min || 1;
    const pts = data.map((v, i) => ({
      x: (i / (data.length - 1)) * W,
      y: H - ((v - min) / range) * (H - 4) - 2,
    }));
    ctx.beginPath();
    pts.forEach((p, i) => (i === 0 ? ctx.moveTo(p.x, p.y) : ctx.lineTo(p.x, p.y)));
    if (fill) {
      ctx.lineTo(W, H); ctx.lineTo(0, H); ctx.closePath();
      ctx.fillStyle = color + "22";
      ctx.fill();
      ctx.beginPath();
      pts.forEach((p, i) => (i === 0 ? ctx.moveTo(p.x, p.y) : ctx.lineTo(p.x, p.y)));
    }
    ctx.strokeStyle = color;
    ctx.lineWidth = 1.5;
    ctx.stroke();
  }, [data, color, fill]);
  return <canvas ref={canvasRef} width={200} height={height} style={{ width: "100%", height }} />;
}

// ─── radial gauge ────────────────────────────────────────────────────────────
function RadialGauge({ value, max, label, color, unit = "" }) {
  const pct = Math.min(value / max, 1);
  const angle = pct * 270 - 135;
  const r = 38, cx = 50, cy = 54;
  const toXY = (deg) => {
    const rad = (deg * Math.PI) / 180;
    return { x: cx + r * Math.cos(rad), y: cy + r * Math.sin(rad) };
  };
  const start = toXY(-225), end = toXY(angle);
  const large = pct * 270 > 180 ? 1 : 0;
  const bgEnd = toXY(45);
  return (
    <svg viewBox="0 0 100 70" className="gauge-svg">
      <path d={`M ${toXY(-225).x} ${toXY(-225).y} A ${r} ${r} 0 1 1 ${bgEnd.x} ${bgEnd.y}`}
        fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="6" strokeLinecap="round" />
      {pct > 0 && (
        <path d={`M ${start.x} ${start.y} A ${r} ${r} 0 ${large} 1 ${end.x} ${end.y}`}
          fill="none" stroke={color} strokeWidth="6" strokeLinecap="round"
          style={{ filter: `drop-shadow(0 0 4px ${color})` }} />
      )}
      <text x="50" y="52" textAnchor="middle" fill={color} fontSize="13" fontWeight="700" fontFamily="'IBM Plex Mono',monospace">
        {typeof value === "number" ? value.toFixed(1) : "–"}{unit}
      </text>
      <text x="50" y="63" textAnchor="middle" fill="rgba(255,255,255,0.35)" fontSize="7" fontFamily="'IBM Plex Mono',monospace">
        {label}
      </text>
    </svg>
  );
}

// ─── heatmap for queue N/S/E/W ───────────────────────────────────────────────
function QueueHeatmap({ queue }) {
  const dirs = ["N", "S", "E", "W"];
  const max = Math.max(...dirs.map((d) => queue?.[d] ?? 0), 1);
  const colors = ["#00e5a0", "#4cff91", "#ffb830", "#ff4757"];
  return (
    <div className="heatmap-grid">
      {dirs.map((d, i) => {
        const val = queue?.[d] ?? 0;
        const pct = val / max;
        const alpha = 0.1 + pct * 0.7;
        return (
          <div key={d} className="heatmap-cell" style={{ background: `rgba(${i < 2 ? "0,229,160" : i === 2 ? "255,184,48" : "255,71,87"},${alpha})`, border: `1px solid rgba(${i < 2 ? "0,229,160" : i === 2 ? "255,184,48" : "255,71,87"},${0.2 + pct * 0.5})` }}>
            <span className="hm-dir">{d}</span>
            <span className="hm-val">{val}</span>
            <div className="hm-bar" style={{ width: `${pct * 100}%`, background: colors[i] }} />
          </div>
        );
      })}
    </div>
  );
}

// ─── episode timeline for AI/MOCK ───────────────────────────────────────────
function EpisodeTimeline({ episodes }) {
  if (!episodes || episodes.length === 0)
    return <div className="episode-empty">Waiting for training data…</div>;
  const maxAbs = Math.max(...episodes.map((e) => Math.abs(e.reward)), 1);
  return (
    <div className="ep-timeline">
      {episodes.slice(-12).map((ep, i) => {
        const h = (Math.abs(ep.reward) / maxAbs) * 52 + 4;
        const good = ep.avgWait < 2.5;
        return (
          <div key={i} className="ep-bar-wrap" title={`Ep ${ep.episode} | Reward: ${ep.reward.toFixed(0)} | Wait: ${ep.avgWait}s`}>
            <div className="ep-bar" style={{ height: h, background: good ? "#00e5a0" : ep.avgWait < 3.5 ? "#ffb830" : "#ff4757", boxShadow: good ? "0 0 6px #00e5a0aa" : "none" }} />
            <span className="ep-num">{ep.episode}</span>
          </div>
        );
      })}
    </div>
  );
}

// ─── mode transition overlay ─────────────────────────────────────────────────
function ModeTransition({ mode, visible }) {
  if (!visible) return null;
  const cfg = {
    AI: { label: "AI MODE", sub: "Q-Learning Agent Activated", color: "#a78bfa", icon: "◈" },
    MOCK: { label: "MOCK MODE", sub: "Simulation Engine Starting", color: "#3d8bff", icon: "⬡" },
    SUMO: { label: "SUMO MODE", sub: "TraCI Connection Established", color: "#00e5a0", icon: "⬢" },
    IDLE: { label: "SYSTEM IDLE", sub: "Select a mode to begin", color: "#7a8899", icon: "○" },
  };
  const c = cfg[mode] || cfg.IDLE;
  return (
    <div className="mode-overlay">
      <div className="mode-overlay-inner" style={{ "--mc": c.color }}>
        <div className="mode-icon">{c.icon}</div>
        <div className="mode-label">{c.label}</div>
        <div className="mode-sub">{c.sub}</div>
        <div className="mode-progress"><div className="mode-progress-fill" /></div>
      </div>
    </div>
  );
}

// ─── MAIN APP ─────────────────────────────────────────────────────────────────
export default function App() {
  const [metrics, setMetrics] = useState(null);
  const [mode, setMode] = useState("IDLE");
  const [prevMode, setPrevMode] = useState("IDLE");
  const [transitioning, setTransitioning] = useState(false);
  const [simActive, setSimActive] = useState(false);

  // history arrays — only populate once simulation is active
  const [waitHistory, setWaitHistory] = useState([]);
  const [rewardHistory, setRewardHistory] = useState([]);
  const [throughHistory, setThroughHistory] = useState([]);
  const [episodes, setEpisodes] = useState([]);
  const [trainingStats, setTrainingStats] = useState(null); // latest episode stats
  const stepRef = useRef(0);

  const fetchMetrics = useCallback(async () => {
    try {
      const res = await getMetrics();
      const data = res.data;
      setMetrics(data);

      if (!simActive) return;

      // push rolling history only when sim is running
      setWaitHistory((h) => [...h.slice(-59), data.ai_avg_wait ?? 0]);
      setThroughHistory((h) => [...h.slice(-59), (data.queue_lengths?.N ?? 0) + (data.queue_lengths?.S ?? 0) + (data.queue_lengths?.E ?? 0) + (data.queue_lengths?.W ?? 0)]);
      stepRef.current += 1;

      // parse AI/MOCK episode data if backend exposes it
      if (data.episode != null) {
        setTrainingStats({
          episode: data.episode,
          reward: data.total_reward ?? 0,
          avgWait: data.avg_wait_time ?? 0,
          epsilon: data.epsilon ?? 0,
          qTableSize: data.q_table_size ?? 0,
          step: data.step ?? stepRef.current,
        });
        if (data.episode_complete) {
          setEpisodes((prev) => [...prev, { episode: data.episode, reward: data.total_reward ?? 0, avgWait: data.avg_wait_time ?? 0 }]);
          setRewardHistory((h) => [...h.slice(-19), data.total_reward ?? 0]);
        }
      }
    } catch (err) {
      console.error(err);
    }
  }, [simActive]);

  useEffect(() => {
    fetchMetrics();
    const iv = setInterval(fetchMetrics, 1500);
    return () => clearInterval(iv);
  }, [fetchMetrics]);

  const handleStartSimulation = async (m) => {
    setPrevMode(mode);
    setTransitioning(true);
    setSimActive(false);
    // clear history on mode switch
    setWaitHistory([]);
    setRewardHistory([]);
    setThroughHistory([]);
    setEpisodes([]);
    setTrainingStats(null);
    stepRef.current = 0;
    await startSimulation(m);
    setMode(m.toUpperCase());
    setTimeout(() => {
      setTransitioning(false);
      setSimActive(true);
    }, 1800);
  };

  if (!metrics) return <div className="loading"><span className="loading-icon">◈</span>Booting AI System…</div>;

  const isAI = mode === "AI";
  const isMock = mode === "MOCK";
  const isSumo = mode === "SUMO";
  const isIdle = mode === "IDLE";
  const modeClass = `mode-${mode.toLowerCase()}`;

  return (
    <div className={`app ${modeClass} ${simActive ? "sim-active" : ""}`}>
      <ModeTransition mode={mode} visible={transitioning} />

      {/* ── HEADER ── */}
      <div className="top-bar">
        <div className="top-bar-left">
          <div className="logo-mark">◈</div>
          <div>
            <h1>AI Traffic Intelligence System</h1>
            <div className="sub-title">VTCPS — Virtual Traffic Congestion Prevention</div>
          </div>
        </div>
        <div className="top-bar-right">
          <div className={`mode-badge ${modeClass}`}>
            <span className="mode-dot" />
            {mode}
          </div>
          {simActive && <div className="live-tag">● LIVE</div>}
        </div>
      </div>

      {/* ── CONTROLS ── */}
      <div className="controls">
        {["mock", "sumo", "ai"].map((m) => (
          <button key={m} onClick={() => handleStartSimulation(m)} className={`ctrl-btn ctrl-${m} ${mode === m.toUpperCase() ? "active" : ""}`}>
            <span className="ctrl-icon">{m === "mock" ? "⬡" : m === "sumo" ? "⬢" : "◈"}</span>
            <span className="ctrl-label">{m.toUpperCase()}</span>
            <span className="ctrl-desc">{m === "mock" ? "Synthetic" : m === "sumo" ? "TraCI" : "Q-Learn"}</span>
          </button>
        ))}
      </div>

      {/* ── TOP METRICS ── */}
      <div className="metrics-row">
        <div className={`metric-card ${isAI ? "accent-ai" : isSumo ? "accent-sumo" : "accent-mock"}`}>
          <div className="mc-label">AI AVG WAIT</div>
          <div className="mc-val">{metrics.ai_avg_wait?.toFixed(2) ?? "–"}<span className="mc-unit">s</span></div>
          <Sparkline data={waitHistory} color={isAI ? "#a78bfa" : isSumo ? "#00e5a0" : "#3d8bff"} height={32} />
        </div>
        <div className="metric-card">
          <div className="mc-label">FIXED WAIT</div>
          <div className="mc-val">{metrics.fixed_avg_wait?.toFixed(2) ?? "–"}<span className="mc-unit">s</span></div>
          <Sparkline data={waitHistory.map(v => v * 1.4)} color="#7a8899" height={32} />
        </div>
        <div className={`metric-card highlight`}>
          <div className="mc-label">EFFICIENCY</div>
          <div className="mc-val efficiency-val">{metrics.improvement?.toFixed(2) ?? "–"}<span className="mc-unit">%</span></div>
          <div className="efficiency-bar">
            <div className="efficiency-fill" style={{ width: `${Math.min(metrics.improvement ?? 0, 100)}%` }} />
          </div>
        </div>
        <div className="metric-card">
          <div className="mc-label">TOTAL QUEUE</div>
          <div className="mc-val">
            {((metrics.queue_lengths?.N ?? 0) + (metrics.queue_lengths?.S ?? 0) + (metrics.queue_lengths?.E ?? 0) + (metrics.queue_lengths?.W ?? 0))}
            <span className="mc-unit">veh</span>
          </div>
          <Sparkline data={throughHistory} color="#ffb830" height={32} />
        </div>
      </div>

      {/* ── MODE-SPECIFIC PANELS ── */}
      {(isAI || isMock) && (
        <div className={`mode-panel training-panel ${isAI ? "ai-colors" : "mock-colors"} ${simActive ? "panel-enter" : "panel-dormant"}`}>
          <div className="panel-header">
            <span className="ph-icon">{isAI ? "◈" : "⬡"}</span>
            <span>{isAI ? "Q-LEARNING TRAINING" : "MOCK SIMULATION"} — EPISODE TRACKER</span>
            {!simActive && <span className="dormant-tag">WAITING FOR SIM</span>}
          </div>
          <div className="training-grid">
            <div className="training-left">
              <div className="gauge-row">
                <RadialGauge value={trainingStats?.epsilon ?? 0} max={1} label="EPSILON ε" color={isAI ? "#a78bfa" : "#3d8bff"} />
                <RadialGauge value={trainingStats?.avgWait ?? 0} max={5} label="AVG WAIT" color="#ffb830" unit="s" />
                <RadialGauge value={trainingStats?.qTableSize ?? 0} max={50} label="Q-TABLE" color="#00e5a0" />
              </div>
              <div className="training-stats-row">
                <div className="ts-item">
                  <span className="ts-label">EPISODE</span>
                  <span className="ts-val">{trainingStats?.episode ?? "–"}<span className="ts-sub">/20</span></span>
                </div>
                <div className="ts-item">
                  <span className="ts-label">STEP</span>
                  <span className="ts-val">{trainingStats?.step ?? stepRef.current}</span>
                </div>
                <div className="ts-item">
                  <span className="ts-label">REWARD</span>
                  <span className="ts-val reward-neg">{trainingStats?.reward?.toFixed(0) ?? "–"}</span>
                </div>
              </div>
            </div>
            <div className="training-right">
              <div className="ep-label">EPISODE REWARD HISTORY</div>
              <EpisodeTimeline episodes={episodes} />
              {rewardHistory.length > 1 && (
                <div style={{ marginTop: 8 }}>
                  <Sparkline data={rewardHistory.map(Math.abs)} color={isAI ? "#a78bfa" : "#3d8bff"} height={40} />
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {isSumo && (
        <div className={`mode-panel sumo-panel ${simActive ? "panel-enter" : "panel-dormant"}`}>
          <div className="panel-header">
            <span className="ph-icon">⬢</span>
            <span>SUMO / TRACI — LIVE NETWORK FEED</span>
            {simActive && <span className="live-tag small">● TRACI CONNECTED</span>}
            {!simActive && <span className="dormant-tag">WAITING FOR SIM</span>}
          </div>
          <div className="sumo-info-row">
            <div className="sumo-info-item">
              <span className="si-label">GREEN PHASE</span>
              <span className={`si-val phase-${metrics.green_phase?.toLowerCase()}`}>{metrics.green_phase ?? "–"}</span>
            </div>
            <div className="sumo-info-item">
              <span className="si-label">NS LIGHT</span>
              <span className={`si-val ${metrics.green_phase === "NS" ? "col-green" : "col-red"}`}>{metrics.green_phase === "NS" ? "GREEN" : "RED"}</span>
            </div>
            <div className="sumo-info-item">
              <span className="si-label">EW LIGHT</span>
              <span className={`si-val ${metrics.green_phase === "EW" ? "col-green" : "col-red"}`}>{metrics.green_phase === "EW" ? "GREEN" : "RED"}</span>
            </div>
          </div>
        </div>
      )}

      {isIdle && (
        <div className="mode-panel idle-panel">
          <div className="idle-msg">◈ Select a simulation mode above to begin</div>
        </div>
      )}

      {/* ── JUNCTION + HEATMAP ROW ── */}
      <div className="junction-row">

        {/* Intersection Visual */}
        <div className={`junction ${!simActive ? "junction-off" : ""}`}>
          <div className="road vertical">
            <div className={`light ${metrics.green_phase === "NS" ? "green" : "red"}`} />
            <div className="cars vertical-flow" />
          </div>
          <div className="road horizontal">
            <div className={`light ${metrics.green_phase === "EW" ? "green" : "red"}`} />
            <div className="cars horizontal-flow" />
          </div>
          <div className="core">
            {isAI ? "AI" : isMock ? "SIM" : isSumo ? "TCI" : "—"}
            <div className="pulse" />
          </div>
          {!simActive && <div className="junction-idle-overlay">STANDBY</div>}
        </div>

        {/* Queue Heatmap */}
        <div className="heatmap-card">
          <div className="card-label">QUEUE HEATMAP</div>
          <QueueHeatmap queue={metrics.queue_lengths} />
          <div className="card-label" style={{ marginTop: 12 }}>WAIT TIME HEATMAP</div>
          <QueueHeatmap queue={metrics.waiting_times} />
        </div>

        {/* Right column: gauges or data */}
        <div className="right-col">
          <div className="data-card">
            <div className="card-label">QUEUE LENGTHS</div>
            {["N","S","E","W"].map(d => (
              <div key={d} className="data-row">
                <span className="dr-dir">{d}</span>
                <div className="dr-bar-wrap">
                  <div className="dr-bar" style={{ width: `${Math.min((metrics.queue_lengths?.[d] ?? 0) / 20 * 100, 100)}%` }} />
                </div>
                <span className="dr-val">{metrics.queue_lengths?.[d] ?? 0}</span>
              </div>
            ))}
          </div>
          <div className="data-card">
            <div className="card-label">WAIT TIMES</div>
            {["N","S","E","W"].map(d => (
              <div key={d} className="data-row">
                <span className="dr-dir">{d}</span>
                <div className="dr-bar-wrap">
                  <div className="dr-bar wait-bar" style={{ width: `${Math.min((metrics.waiting_times?.[d] ?? 0) / 60 * 100, 100)}%` }} />
                </div>
                <span className="dr-val">{metrics.waiting_times?.[d] ?? 0}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ── DECISION PANEL ── */}
      <div className="decision">
        <div className="decision-icon">⚡</div>
        <div>
          <h3>AI Decision Engine</h3>
          <p>
            {metrics.queue_lengths?.N > metrics.queue_lengths?.E
              ? "High congestion on North-South → Prioritizing NS flow"
              : "Balancing East-West traffic → Switching EW"}
          </p>
        </div>
        {simActive && (
          <div className="decision-indicator">
            <div className="di-dot" /><div className="di-dot" /><div className="di-dot" />
          </div>
        )}
      </div>

    </div>
  );
}