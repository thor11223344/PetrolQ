import React, { useState, useEffect, useRef } from 'react';
import { 
  Activity, 
  Map as MapIcon, 
  Settings, 
  Bell, 
  ChevronDown, 
  Database,
  AlertTriangle,
  XCircle,
  TrendingDown
} from 'lucide-react';
import axios from 'axios';
import Plot from 'react-plotly.js';

import WellMap from './components/WellMap';

function App() {
  const [selectedWell, setSelectedWell] = useState('OIL-BAGHJAN-1');
  const [telemetryData, setTelemetryData] = useState(null);
  const [trajectoryData, setTrajectoryData] = useState({ depth: [], torque: [], rop: [] });
  const [alertState, setAlertState] = useState({ active: false, prediction: null });
  const [ragContext, setRagContext] = useState(null);
  const wsRef = useRef(null);

  useEffect(() => {
    // Connect to WebSocket
    wsRef.current = new WebSocket('ws://localhost:8000/api/ws/telemetry');

    wsRef.current.onopen = () => {
      console.log("WebSocket Connected");
    };

    wsRef.current.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.status === 'success') {
          const currentTelemetry = data.data;
          const prediction = data.prediction;
          
          setTelemetryData(currentTelemetry);
          
          // Update Trajectory Data for plotting (keep last 50 points to prevent lag)
          setTrajectoryData(prev => {
            const newDepth = [...prev.depth, currentTelemetry.depth_tvd].slice(-50);
            const newTorque = [...prev.torque, currentTelemetry.torque].slice(-50);
            const newRop = [...prev.rop, currentTelemetry.rop].slice(-50);
            return { depth: newDepth, torque: newTorque, rop: newRop };
          });

          // Check for High Risk
          if (prediction?.risk_level === 'HIGH' || prediction?.risk_level === 'CRITICAL') {
            if (!alertState.active) {
                // We use functional state update here to ensure we don't spam API
                setAlertState(prev => {
                    if (!prev.active) {
                        fetchRagContext(prediction);
                        return { active: true, prediction };
                    }
                    return prev;
                });
            }
          }
        }
      } catch (err) {
        console.error("Error parsing websocket message", err);
      }
    };

    wsRef.current.onclose = () => {
      console.log("WebSocket Disconnected");
    };

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [alertState.active]);

  const fetchRagContext = async (prediction) => {
      try {
          // Construct a dynamic query based on top factors
          let query = "high surface torque and drilling hazard";
          if (prediction?.top_factors?.length > 0) {
              const topFactor = prediction.top_factors[0].feature;
              query = `Elevated ${topFactor} causing potential hazard during drilling`;
          }
          
          const response = await axios.get(`http://localhost:8000/api/events/search`, {
              params: { query, limit: 1 }
          });
          
          if (response.data && response.data.length > 0) {
              setRagContext(response.data[0]);
          }
      } catch (err) {
          console.error("Failed to fetch RAG context", err);
      }
  };

  const dismissAlert = () => {
      setAlertState({ active: false, prediction: null });
      setRagContext(null);
  };

  return (
    <div className="h-screen w-screen flex flex-col bg-slate-950 text-slate-200 overflow-hidden font-sans">
      
      {/* Top Navigation Bar */}
      <header className="h-14 border-b border-slate-800 bg-slate-900 flex items-center justify-between px-6 z-20 shrink-0 shadow-md">
        <div className="flex items-center space-x-4">
          <div className="flex items-center justify-center w-8 h-8 rounded bg-status-active/20 text-status-active">
            <Activity size={18} />
          </div>
          <h1 className="text-lg font-semibold tracking-wide">
            eRTMAC-NWIS <span className="text-slate-500 font-normal ml-2">| Offset Well Intelligence Platform</span>
          </h1>
        </div>

        <div className="flex items-center space-x-6">
          {/* Status Indicator */}
          <div className="flex items-center space-x-2 bg-slate-800/50 px-3 py-1.5 rounded-full border border-slate-700/50">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-status-active opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-status-active"></span>
            </span>
            <span className="text-xs font-medium text-slate-300">eRTMAC Feed: Connected</span>
          </div>

          {/* Active Well Selector */}
          <div className="flex items-center space-x-3 border-l border-slate-800 pl-6">
            <span className="text-sm text-slate-400">Active Target:</span>
            <button className="flex items-center space-x-2 bg-slate-800 hover:bg-slate-700 px-3 py-1.5 rounded transition-colors text-sm font-medium border border-slate-700">
              <Database size={14} className="text-status-fluid" />
              <span>{selectedWell}</span>
              <ChevronDown size={14} className="text-slate-400" />
            </button>
          </div>

          {/* Tools */}
          <div className="flex items-center space-x-3 text-slate-400 border-l border-slate-800 pl-6">
            <button className="hover:text-white transition-colors"><Bell size={18} /></button>
            <button className="hover:text-white transition-colors"><Settings size={18} /></button>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 relative flex">
        
        {/* Map Container */}
        <div className="flex-1 bg-slate-900 relative overflow-hidden flex flex-col">
          
          {/* Active Drilling Status Card overlay */}
          <div className="absolute top-4 left-4 z-10 flex gap-4">
            <div className="bg-slate-900/90 backdrop-blur border border-slate-700 p-4 rounded-lg shadow-xl min-w-[200px]">
              <h3 className="text-xs uppercase text-slate-400 font-bold mb-2">Current TVD</h3>
              <div className="text-3xl font-light text-white">
                {telemetryData ? telemetryData.depth_tvd.toFixed(1) : "---"} <span className="text-sm text-slate-500">m</span>
              </div>
            </div>
            
            <div className="bg-slate-900/90 backdrop-blur border border-slate-700 p-4 rounded-lg shadow-xl min-w-[150px]">
              <h3 className="text-xs uppercase text-slate-400 font-bold mb-2">ROP</h3>
              <div className="text-2xl font-light text-status-active">
                {telemetryData ? telemetryData.rop.toFixed(1) : "---"} <span className="text-sm text-slate-500">m/h</span>
              </div>
            </div>

            <div className={`bg-slate-900/90 backdrop-blur border ${alertState.active ? 'border-status-danger bg-status-danger/10' : 'border-slate-700'} p-4 rounded-lg shadow-xl min-w-[150px] transition-colors duration-500`}>
              <h3 className="text-xs uppercase text-slate-400 font-bold mb-2">Torque</h3>
              <div className={`text-2xl font-light ${alertState.active ? 'text-status-danger animate-pulse' : 'text-status-warning'}`}>
                {telemetryData ? telemetryData.torque.toFixed(0) : "---"} <span className="text-sm text-slate-500">lbf-ft</span>
              </div>
            </div>
          </div>

          <WellMap 
             activeWellId={selectedWell} 
             onSelectWell={setSelectedWell} 
          />
        </div>

        {/* Right-Hand Drawer */}
        <aside className="w-[450px] border-l border-slate-800 bg-slate-950 flex flex-col shadow-2xl z-20 shrink-0 relative">
          
          {/* Hazard Alert Banner */}
          {alertState.active && (
            <div className="bg-status-danger text-white p-4 border-b-4 border-red-900 shadow-lg animate-in slide-in-from-top-4 relative">
              <button 
                onClick={dismissAlert}
                className="absolute top-2 right-2 text-white/70 hover:text-white transition-colors"
              >
                <XCircle size={20} />
              </button>
              <div className="flex items-center gap-3 mb-2">
                <AlertTriangle size={24} className="animate-pulse" />
                <h2 className="font-bold text-lg tracking-wide uppercase">Proactive Hazard Alert</h2>
              </div>
              <div className="bg-black/20 p-3 rounded text-sm mb-3">
                 <p className="font-medium text-red-100">
                   Probability: <span className="text-white text-base">{(alertState.prediction.risk_probability * 100).toFixed(1)}%</span>
                 </p>
                 {alertState.prediction.top_factors && alertState.prediction.top_factors.length > 0 && (
                   <p className="mt-1">
                     <span className="text-red-200">Risk driven by:</span> {alertState.prediction.top_factors[0].feature.replace('_', ' ').toUpperCase()} 
                     ({alertState.prediction.top_factors[0].direction === 'INCREASES_RISK' ? 'Elevated' : 'Reduced'})
                   </p>
                 )}
              </div>
              
              {/* RAG Context Display */}
              {ragContext ? (
                <div className="bg-slate-900 text-slate-200 p-3 rounded text-sm border border-slate-700 shadow-inner">
                  <div className="flex items-center gap-2 mb-2 text-status-warning">
                    <TrendingDown size={16} />
                    <span className="font-bold uppercase text-xs">Offset Well Intelligence</span>
                  </div>
                  <p className="mb-2"><span className="text-slate-400">Historical Match:</span> Offset well <span className="font-mono text-xs text-blue-300">{ragContext.well_id}</span> experienced <strong className="text-white">{ragContext.event_type}</strong> at {ragContext.depth_tvd}m.</p>
                  <p><span className="text-slate-400">Recommended Mitigation:</span> <span className="text-emerald-400 font-medium">{ragContext.mitigation_applied}</span></p>
                </div>
              ) : (
                <div className="text-sm text-red-200 animate-pulse">Fetching offset well intelligence...</div>
              )}
            </div>
          )}

          <div className="p-4 border-b border-slate-800 flex items-center justify-between">
            <h2 className="font-medium text-slate-200">Real-Time Telemetry</h2>
            <div className="flex space-x-1">
              <div className="w-2 h-2 rounded-full bg-status-danger mt-1"></div>
              <div className="w-2 h-2 rounded-full bg-status-warning mt-1"></div>
            </div>
          </div>
          
          <div className="flex-1 p-4 overflow-y-auto custom-scrollbar">
            
            {/* Real-time Trajectory Widget */}
            <div className="bg-slate-900 border border-slate-800 rounded p-4 mb-4">
              <h3 className="text-xs uppercase font-bold text-slate-500 mb-3">Torque vs Depth (TVD)</h3>
              <div className="h-64 flex items-center justify-center rounded overflow-hidden">
                <Plot
                  data={[
                    {
                      x: trajectoryData.torque,
                      y: trajectoryData.depth,
                      type: 'scatter',
                      mode: 'lines+markers',
                      line: { color: alertState.active ? '#ef4444' : '#3b82f6', width: 2 },
                      marker: { size: 4, color: alertState.active ? '#ef4444' : '#60a5fa' }
                    }
                  ]}
                  layout={{
                    width: 380,
                    height: 250,
                    margin: { t: 10, r: 10, l: 50, b: 30 },
                    paper_bgcolor: 'transparent',
                    plot_bgcolor: 'transparent',
                    xaxis: { 
                      title: 'Torque (lbf-ft)', 
                      gridcolor: '#334155',
                      zerolinecolor: '#334155',
                      color: '#94a3b8' 
                    },
                    yaxis: { 
                      title: 'Depth (m)', 
                      autorange: 'reversed',
                      gridcolor: '#334155',
                      zerolinecolor: '#334155',
                      color: '#94a3b8'
                    }
                  }}
                  config={{ responsive: true, displayModeBar: false }}
                />
              </div>
            </div>

            {/* Event Log */}
            <div className="bg-slate-900 border border-slate-800 rounded p-4">
              <h3 className="text-xs uppercase font-bold text-slate-500 mb-3">Recent Offset Events</h3>
              <div className="space-y-3">
                {[
                    { id: 1, type: "Severe Lost Circulation", depth: "2,450m" },
                    { id: 2, type: "Pack-off / Stuck Pipe", depth: "2,870m" },
                    { id: 3, type: "Kick Detected", depth: "3,100m" }
                ].map((event, i) => (
                  <div key={event.id} className="flex items-start space-x-3 p-3 bg-slate-950/50 rounded border border-slate-800/50 hover:border-slate-600 transition-colors cursor-pointer">
                    <div className={`w-1.5 h-1.5 rounded-full mt-1.5 shrink-0 ${i === 0 ? 'bg-status-danger' : 'bg-status-warning'}`}></div>
                    <div>
                      <p className="text-sm font-medium text-slate-300">{event.type}</p>
                      <p className="text-xs text-slate-500 mt-1">Depth: {event.depth} TVD</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </aside>
      </main>
    </div>
  );
}

export default App;
