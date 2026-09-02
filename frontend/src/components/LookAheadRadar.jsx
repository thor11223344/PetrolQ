import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { 
  Radar, 
  AlertTriangle, 
  ShieldAlert, 
  Layers, 
  CheckCircle2, 
  ArrowRight, 
  Sliders, 
  RefreshCw, 
  X,
  Compass,
  Zap,
  Info
} from 'lucide-react';

const LookAheadRadar = ({ isOpen, onClose, activeWellId = 'OIL-BAGHJAN-1', currentDepth = 2240.0 }) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [windowMeters, setWindowMeters] = useState(250);
  const [simulatedDepth, setSimulatedDepth] = useState(currentDepth);

  useEffect(() => {
    setSimulatedDepth(currentDepth);
  }, [currentDepth]);

  const fetchLookAhead = async () => {
    if (!isOpen) return;
    setLoading(true);
    try {
      const res = await axios.get(`http://localhost:8000/api/wells/${activeWellId}/lookahead`, {
        params: {
          current_depth: simulatedDepth,
          window_meters: windowMeters
        }
      });
      setData(res.data);
    } catch (err) {
      console.error('Failed to fetch lookahead data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLookAhead();
  }, [isOpen, activeWellId, simulatedDepth, windowMeters]);

  if (!isOpen) return null;

  const ml = data?.ml_risk_assessment || {};
  const riskScore = ml.risk_score !== undefined ? ml.risk_score : 0.45;
  const isHighRisk = riskScore > 0.65;
  const isModerateRisk = riskScore >= 0.35 && riskScore <= 0.65;

  const riskColor = isHighRisk ? '#EF4444' : (isModerateRisk ? '#F59E0B' : '#10B981');
  const riskLabel = isHighRisk ? 'CRITICAL AHEAD' : (isModerateRisk ? 'ELEVATED HAZARD' : 'SAFE CORRIDOR');

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 animate-in fade-in duration-200">
      <div className="bg-slate-900 border border-slate-700 w-full max-w-5xl rounded-xl shadow-2xl overflow-hidden flex flex-col max-h-[92vh]">
        
        {/* Header */}
        <div className="px-6 py-4 bg-slate-950 border-b border-slate-800 flex justify-between items-center">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-amber-500/10 rounded-lg border border-amber-500/20 text-amber-400">
              <Radar size={22} className="animate-spin-slow" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h2 className="text-lg font-bold text-white tracking-wide">
                  Ahead-of-the-Bit Hazard Radar
                </h2>
                <span className="text-xs px-2.5 py-0.5 rounded-full bg-cyan-950 border border-cyan-800 text-cyan-300 font-mono">
                  {activeWellId}
                </span>
                <span className="text-xs px-2.5 py-0.5 rounded-full bg-slate-800 border border-slate-700 text-slate-300 font-mono">
                  Bit TVD: {Math.round(simulatedDepth)}m
                </span>
              </div>
              <p className="text-xs text-slate-400">
                Proactive offset well correlation scanning {windowMeters}m ahead of the current bit position
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <button 
              onClick={fetchLookAhead}
              className="p-1.5 rounded-lg border border-slate-700 hover:bg-slate-800 text-slate-400 hover:text-white transition"
              title="Refresh Radar Scan"
            >
              <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
            </button>
            <button 
              onClick={onClose}
              className="p-1.5 rounded-lg border border-slate-700 hover:bg-slate-800 text-slate-400 hover:text-white transition"
            >
              <X size={18} />
            </button>
          </div>
        </div>

        {/* Controls Bar */}
        <div className="px-6 py-3 bg-slate-950/60 border-b border-slate-800 flex flex-wrap items-center justify-between gap-4 text-xs">
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2 text-slate-300">
              <Sliders size={14} className="text-cyan-400" />
              <span>Look-Ahead Horizon:</span>
              <div className="flex items-center space-x-1 bg-slate-900 border border-slate-800 rounded-md p-1">
                {[150, 250, 350, 500].map(dist => (
                  <button
                    key={dist}
                    onClick={() => setWindowMeters(dist)}
                    className={`px-2.5 py-1 rounded font-medium transition ${
                      windowMeters === dist 
                        ? 'bg-cyan-500 text-slate-950 font-bold' 
                        : 'text-slate-400 hover:text-white'
                    }`}
                  >
                    +{dist}m
                  </button>
                ))}
              </div>
            </div>

            <div className="flex items-center space-x-2 text-slate-300">
              <span>Simulated Bit Depth:</span>
              <input 
                type="range" 
                min="1000" 
                max="3200" 
                step="20"
                value={simulatedDepth}
                onChange={(e) => setSimulatedDepth(parseFloat(e.target.value))}
                className="w-32 accent-cyan-500 cursor-pointer"
              />
              <span className="font-mono text-cyan-400 font-bold w-16">{Math.round(simulatedDepth)}m</span>
            </div>
          </div>

          {/* Quick Metrics */}
          <div className="flex items-center space-x-4 font-mono">
            <span className="text-slate-400">
              Scan Range: <strong className="text-white">{Math.round(simulatedDepth)}m → {Math.round(simulatedDepth + windowMeters)}m</strong>
            </span>
            <span className="text-slate-400">
              Correlated Offset Incidents: <strong className="text-amber-400">{data?.horizon_events_count || 0}</strong>
            </span>
          </div>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          
          {/* Top Row: Predictive Horizon Status Card */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            
            {/* Horizon Threat Gauge */}
            <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 flex flex-col justify-between">
              <div>
                <span className="text-xs uppercase tracking-wider text-slate-400 font-medium">Unified ML Hazard Forecast</span>
                <div className="flex items-baseline justify-between mt-2">
                  <span className="text-2xl font-black font-mono" style={{ color: riskColor }}>
                    {(riskScore * 100).toFixed(0)}%
                  </span>
                  <span className="text-xs px-2.5 py-1 rounded-full font-bold border" style={{ color: riskColor, borderColor: `${riskColor}50`, backgroundColor: `${riskColor}15` }}>
                    {riskLabel}
                  </span>
                </div>
                <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden mt-3">
                  <div 
                    className="h-full transition-all duration-500 rounded-full" 
                    style={{ width: `${Math.min(100, Math.max(5, riskScore * 100))}%`, backgroundColor: riskColor }}
                  />
                </div>
              </div>
              <div className="mt-4 pt-3 border-t border-slate-800/80 text-[11px] text-slate-400 flex items-center justify-between">
                <span>Primary Ahead Threat:</span>
                <span className="font-bold text-slate-200 uppercase">{ml.dominant_threat || 'NORMAL'}</span>
              </div>
            </div>

            {/* Upcoming Formation Top */}
            <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 flex flex-col justify-between">
              <div>
                <span className="text-xs uppercase tracking-wider text-slate-400 font-medium flex items-center space-x-1.5">
                  <Layers size={14} className="text-amber-400" />
                  <span>Next Stratigraphic Transition</span>
                </span>
                
                {data?.next_formation ? (
                  <div className="mt-2">
                    <div className="text-lg font-bold text-white">
                      {data.next_formation}
                    </div>
                    <div className="flex items-center space-x-2 mt-1">
                      <span className="text-sm font-mono text-cyan-400 font-bold">
                        {data.distance_to_next_formation_m > 0 ? `In ${data.distance_to_next_formation_m}m` : 'Penetrated'}
                      </span>
                      <span className="text-xs text-slate-400">
                        (Top at {data.upcoming_formations?.[0]?.tvd_top || 2400}m TVD)
                      </span>
                    </div>
                  </div>
                ) : (
                  <div className="mt-3 text-sm text-slate-400">
                    No major stratigraphic boundary in immediate {windowMeters}m horizon
                  </div>
                )}
              </div>

              <div className="mt-4 pt-3 border-t border-slate-800/80 text-[11px] text-slate-400">
                {data?.upcoming_formations?.[0]?.primary_risk ? (
                  <span className="text-amber-300/90 font-medium">
                    ⚠️ {data.upcoming_formations[0].primary_risk}
                  </span>
                ) : (
                  <span>Consistent formation lithology</span>
                )}
              </div>
            </div>

            {/* Historical Incident Breakdown */}
            <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 flex flex-col justify-between">
              <div>
                <span className="text-xs uppercase tracking-wider text-slate-400 font-medium flex items-center space-x-1.5">
                  <Compass size={14} className="text-cyan-400" />
                  <span>Offset Well Incidents in Horizon</span>
                </span>

                <div className="grid grid-cols-3 gap-2 mt-3 text-center">
                  <div className="p-2 rounded-lg bg-red-950/30 border border-red-900/40">
                    <span className="text-xs text-red-400 block font-medium">Kicks</span>
                    <strong className="text-lg font-mono text-red-300">{data?.kick_events_count || 0}</strong>
                  </div>
                  <div className="p-2 rounded-lg bg-amber-950/30 border border-amber-900/40">
                    <span className="text-xs text-amber-400 block font-medium">Losses</span>
                    <strong className="text-lg font-mono text-amber-300">{data?.loss_events_count || 0}</strong>
                  </div>
                  <div className="p-2 rounded-lg bg-purple-950/30 border border-purple-900/40">
                    <span className="text-xs text-purple-400 block font-medium">Stuck</span>
                    <strong className="text-lg font-mono text-purple-300">{data?.stuck_events_count || 0}</strong>
                  </div>
                </div>
              </div>

              <div className="mt-3 pt-2 text-[11px] text-slate-400 text-center">
                Total Correlated Offset Incidents: <strong className="text-white font-mono">{data?.horizon_events_count || 0}</strong>
              </div>
            </div>

          </div>

          {/* Driller Proactive Advisory Action Plan */}
          <div className="p-5 rounded-xl bg-slate-950/90 border border-slate-800">
            <div className="flex items-center space-x-2 mb-4">
              <Zap size={18} className="text-amber-400" />
              <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                Proactive Driller Advisory & Preventive Checklist
              </h3>
              <span className="text-xs px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30 font-medium">
                Mandatory Prior to {Math.round(simulatedDepth + 100)}m
              </span>
            </div>

            <div className="space-y-2.5">
              {data?.advisory_actions?.map((adv, idx) => {
                const isCrit = adv.priority === 'CRITICAL' || adv.priority === 'HIGH';
                return (
                  <div 
                    key={idx}
                    className={`p-3.5 rounded-lg border flex items-start space-x-3 transition ${
                      isCrit 
                        ? 'bg-red-950/20 border-red-900/50 text-red-100' 
                        : 'bg-slate-900/80 border-slate-800 text-slate-200'
                    }`}
                  >
                    <div className="mt-0.5">
                      {isCrit ? (
                        <ShieldAlert size={18} className="text-red-400 flex-shrink-0" />
                      ) : (
                        <CheckCircle2 size={18} className="text-emerald-400 flex-shrink-0" />
                      )}
                    </div>
                    <div className="flex-1 text-xs">
                      <div className="flex items-center space-x-2 mb-1">
                        <span className="font-mono font-bold uppercase tracking-wider text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                          {adv.category}
                        </span>
                        <span className={`text-[10px] font-bold uppercase ${isCrit ? 'text-red-400' : 'text-emerald-400'}`}>
                          {adv.priority} PRIORITY
                        </span>
                      </div>
                      <p className="leading-relaxed font-medium">{adv.action}</p>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Correlated Historical Incidents in the Upcoming Horizon */}
          <div className="p-5 rounded-xl bg-slate-950/90 border border-slate-800">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-2">
                <AlertTriangle size={18} className="text-cyan-400" />
                <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                  Nearby Offset Incidents in This Depth Corridor ({Math.round(simulatedDepth)}m – {Math.round(simulatedDepth + windowMeters)}m)
                </h3>
              </div>
              <span className="text-xs text-slate-400">
                Institutional Memory RAG Query
              </span>
            </div>

            {data?.events && data.events.length > 0 ? (
              <div className="space-y-3">
                {data.events.map((ev, i) => (
                  <div key={i} className="p-3.5 rounded-lg bg-slate-900 border border-slate-800 text-xs hover:border-slate-700 transition">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center space-x-2">
                        <span className="font-mono font-bold text-white text-sm">
                          {ev.well_id}
                        </span>
                        <span className="text-xs px-2 py-0.5 rounded bg-slate-800 text-cyan-300 font-mono">
                          {ev.formation} @ {ev.depth_tvd}m TVD
                        </span>
                        <span className="text-xs px-2 py-0.5 rounded font-bold uppercase" style={{
                          backgroundColor: ev.severity === 'CRITICAL' ? '#EF444420' : '#F59E0B20',
                          color: ev.severity === 'CRITICAL' ? '#EF4444' : '#F59E0B',
                          borderColor: ev.severity === 'CRITICAL' ? '#EF444450' : '#F59E0B50'
                        }}>
                          {ev.event_type}
                        </span>
                      </div>
                      <span className="font-mono text-slate-400 text-[11px]">
                        NPT: <strong className="text-amber-400">{ev.npt_hours}h</strong>
                      </span>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-slate-300 text-[11px] bg-slate-950/60 p-2.5 rounded border border-slate-800/80">
                      <div>
                        <strong className="text-slate-400 block mb-0.5">Root Cause:</strong>
                        <span>{ev.root_cause}</span>
                      </div>
                      <div>
                        <strong className="text-emerald-400 block mb-0.5">Field Mitigation Applied:</strong>
                        <span>{ev.mitigation}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="py-8 text-center text-slate-400 text-xs">
                No major NPT events recorded in offset wells within the immediate {windowMeters}m depth corridor.
              </div>
            )}
          </div>

        </div>

        {/* Footer */}
        <div className="px-6 py-3.5 bg-slate-950 border-t border-slate-800 flex justify-between items-center text-xs text-slate-400">
          <div className="flex items-center space-x-2">
            <Info size={14} className="text-cyan-400" />
            <span>Look-Ahead Radar updates in real-time as bit advances via eRTMAC WITSML telemetry feed.</span>
          </div>
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-white font-medium transition"
          >
            Close Radar
          </button>
        </div>

      </div>
    </div>
  );
};

export default LookAheadRadar;
