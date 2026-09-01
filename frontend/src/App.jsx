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
  TrendingDown,
  FileUp,
  Search,
  Download
} from 'lucide-react';
import axios from 'axios';
import Plot from 'react-plotly.js';

import WellMap from './components/WellMap';
import DocumentUploadModal from './components/DocumentUploadModal';
import KnowledgeSearch from './components/KnowledgeSearch';
import CorrelationPanel from './components/CorrelationPanel';

function App() {
  const [selectedWell, setSelectedWell] = useState('OIL-BAGHJAN-1');
  const [telemetryData, setTelemetryData] = useState(null);
  const [trajectoryData, setTrajectoryData] = useState({ depth: [], torque: [], rop: [] });
  const [alertState, setAlertState] = useState({ active: false, prediction: null });
  const [ragContext, setRagContext] = useState(null);
  const [recentEvents, setRecentEvents] = useState([]);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
  const [isKnowledgeSearchOpen, setIsKnowledgeSearchOpen] = useState(false);
  const [isCorrelationOpen, setIsCorrelationOpen] = useState(false);
  const [role, setRole] = useState('Field Engineer');
  const wsRef = useRef(null);

  const showAlerts = role === 'Field Engineer';

  const handleRoleChange = (e) => {
    const newRole = e.target.value;
    setRole(newRole);
    if (newRole === 'Office Reviewer') {
      setIsKnowledgeSearchOpen(true);
      setIsCorrelationOpen(true);
    }
  };

  const exportWellData = async () => {
    try {
        const res = await axios.get(`http://localhost:8000/api/wells/${selectedWell}/history`);
        const well = res.data;
        
        let csvContent = "data:text/csv;charset=utf-8,";
        
        csvContent += "Type,Timestamp,Depth(TVD),ROP,WOB,Torque,MudWeight\n";
        if (well.logs) {
            well.logs.forEach(p => {
                csvContent += `Param,${p.timestamp || ''},${p.depth_tvd || ''},${p.rop || ''},${p.wob || ''},${p.torque || ''},${p.mud_weight || ''}\n`;
            });
        }
        
        csvContent += "\nType,Depth(TVD),Event,RootCause,Mitigation\n";
        if (well.events) {
            well.events.forEach(e => {
                csvContent += `Event,${e.depth_tvd || ''},"${e.event_type || ''}","${e.root_cause || ''}","${e.mitigation_applied || ''}"\n`;
            });
        }
        
        const encodedUri = encodeURI(csvContent);
        const link = document.createElement("a");
        link.setAttribute("href", encodedUri);
        link.setAttribute("download", `${selectedWell}_data_export.csv`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    } catch (err) {
        console.error("Export failed", err);
        alert("Failed to export well data");
    }
  };

  useEffect(() => {
    const fetchHistory = async () => {
        try {
            const res = await axios.get(`http://localhost:8000/api/wells/${selectedWell}/history`);
            if (res.data && res.data.events) {
                // sort by depth descending, take top 5
                const sortedEvents = res.data.events.sort((a, b) => b.depth_tvd - a.depth_tvd).slice(0, 5);
                setRecentEvents(sortedEvents);
            }
        } catch (err) {
            console.error("Failed to fetch well history", err);
            setRecentEvents([]);
        }
    };
    fetchHistory();
  }, [selectedWell]);

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
      <header className="h-14 border-b border-slate-800 bg-slate-900 flex items-center justify-between px-6 z-50 shrink-0 shadow-md relative">
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

          {/* Role Toggle */}
          <div className="flex items-center space-x-3 border-l border-slate-800 pl-6">
            <span className="text-sm text-slate-400">View As:</span>
            <select 
                value={role} 
                onChange={handleRoleChange}
                className="bg-slate-800 border border-slate-700 text-slate-200 text-sm rounded px-2 py-1 outline-none focus:border-status-fluid"
            >
                <option value="Field Engineer">Field Engineer</option>
                <option value="Office Reviewer">Office Reviewer</option>
            </select>
          </div>

          {/* Active Well Selector */}
          <div className="flex items-center space-x-3 border-l border-slate-800 pl-6">
            <span className="text-sm text-slate-400">Active Target:</span>
            <div className="flex items-center space-x-2 bg-slate-800 hover:bg-slate-700 px-3 py-1 rounded transition-colors border border-slate-700">
              <Database size={14} className="text-status-fluid" />
              <select 
                  value={selectedWell} 
                  onChange={(e) => setSelectedWell(e.target.value)}
                  className="bg-transparent text-slate-200 text-sm font-medium outline-none cursor-pointer"
              >
                  <option value="OIL-BAGHJAN-1">OIL-BAGHJAN-1</option>
                  <option value="OIL-NAHARKATIYA-1">OIL-NAHARKATIYA-1</option>
                  <option value="OIL-MORAN-1">OIL-MORAN-1</option>
                  <option value="OIL-DIKOM-1">OIL-DIKOM-1</option>
                  <option value="OIL-TENGAKHAT-1">OIL-TENGAKHAT-1</option>
                  <option value="OIL-KOTHALONI-1">OIL-KOTHALONI-1</option>
                  <option value="OIL-HAPJAN-1">OIL-HAPJAN-1</option>
                  <option value="OIL-SHALMARI-1">OIL-SHALMARI-1</option>
              </select>
            </div>
          </div>

          {/* Tools */}
          <div className="flex items-center space-x-3 text-slate-400 border-l border-slate-800 pl-6 relative">
            <button 
                onClick={() => setIsUploadModalOpen(true)}
                className="hover:text-white transition-colors flex items-center space-x-2 text-sm bg-slate-800 px-3 py-1 rounded"
                title="Upload Document"
            >
                <FileUp size={16} />
                <span>Upload</span>
            </button>
            <div className="w-px h-4 bg-slate-700 mx-2"></div>
            <button 
                onClick={() => setIsKnowledgeSearchOpen(!isKnowledgeSearchOpen)}
                className={`transition-colors ${isKnowledgeSearchOpen ? 'text-white' : 'hover:text-white'}`}
                title="Search Knowledge Base"
            >
                <Search size={18} />
            </button>
            <button className="hover:text-white transition-colors"><Bell size={18} /></button>
            <button 
                onClick={() => setIsSettingsOpen(!isSettingsOpen)} 
                className={`transition-colors ${isSettingsOpen ? 'text-white' : 'hover:text-white'}`}
            >
                <Settings size={18} />
            </button>
            
            {/* Settings Dropdown */}
            {isSettingsOpen && (
                <div className="absolute top-10 right-0 w-64 bg-slate-900 border border-slate-700 shadow-2xl rounded-lg p-4 z-50 animate-in fade-in zoom-in-95">
                    <div className="flex items-center justify-between mb-4 border-b border-slate-800 pb-2">
                        <h3 className="font-semibold text-slate-200">System Settings</h3>
                        <button onClick={() => setIsSettingsOpen(false)} className="text-slate-500 hover:text-slate-300">
                            <XCircle size={16} />
                        </button>
                    </div>
                    <div className="space-y-4">
                        <div className="flex items-center justify-between">
                            <span className="text-sm text-slate-400">Dark Mode</span>
                            <div className="w-8 h-4 bg-status-active rounded-full relative cursor-pointer">
                                <div className="absolute right-1 top-0.5 w-3 h-3 bg-white rounded-full"></div>
                            </div>
                        </div>
                        <div className="flex items-center justify-between">
                            <span className="text-sm text-slate-400">Audio Alerts</span>
                            <div className="w-8 h-4 bg-slate-700 rounded-full relative cursor-pointer">
                                <div className="absolute left-1 top-0.5 w-3 h-3 bg-slate-400 rounded-full"></div>
                            </div>
                        </div>
                        <div className="flex items-center justify-between">
                            <span className="text-sm text-slate-400">Telemetry Rate</span>
                            <select className="bg-slate-800 text-xs border border-slate-700 rounded p-1 text-slate-300">
                                <option>1.0 Hz</option>
                                <option>0.5 Hz</option>
                                <option>2.0 Hz</option>
                            </select>
                        </div>
                    </div>
                </div>
            )}
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

            <div className={`bg-slate-900/90 backdrop-blur border ${showAlerts && alertState.active ? 'border-status-danger bg-status-danger/10' : 'border-slate-700'} p-4 rounded-lg shadow-xl min-w-[150px] transition-colors duration-500`}>
              <h3 className="text-xs uppercase text-slate-400 font-bold mb-2">Torque</h3>
              <div className={`text-2xl font-light ${showAlerts && alertState.active ? 'text-status-danger animate-pulse' : 'text-status-warning'}`}>
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
          {showAlerts && alertState.active && (
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
                      line: { color: showAlerts && alertState.active ? '#ef4444' : '#3b82f6', width: 2 },
                      marker: { size: 4, color: showAlerts && alertState.active ? '#ef4444' : '#60a5fa' }
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
                {recentEvents.length > 0 ? recentEvents.map((event, i) => (
                  <div key={event.id} className="flex items-start space-x-3 p-3 bg-slate-950/50 rounded border border-slate-800/50 hover:border-slate-600 transition-colors cursor-pointer">
                    <div className={`w-1.5 h-1.5 rounded-full mt-1.5 shrink-0 ${i === 0 ? 'bg-status-danger' : 'bg-status-warning'}`}></div>
                    <div>
                      <p className="text-sm font-medium text-slate-300">{event.event_type}</p>
                      <p className="text-xs text-slate-500 mt-1">Depth: {event.depth_tvd}m TVD</p>
                    </div>
                  </div>
                )) : (
                  <div className="text-sm text-slate-500 p-3">No recent events found.</div>
                )}
              </div>
              <button 
                onClick={() => setIsCorrelationOpen(true)}
                className="w-full mt-4 bg-status-active/20 hover:bg-status-active/30 text-status-active text-sm font-medium py-2 rounded transition-colors border border-status-active/30 flex items-center justify-center"
              >
                Correlate with Offset Well
              </button>
              <button 
                onClick={exportWellData}
                className="w-full mt-2 bg-slate-800 hover:bg-slate-700 text-slate-300 text-sm font-medium py-2 rounded transition-colors border border-slate-700 flex items-center justify-center"
              >
                <Download size={16} className="mr-2" />
                Export Well Data (CSV)
              </button>
            </div>
          </div>
        </aside>
      </main>

      {/* Document Upload Modal */}
      <DocumentUploadModal 
          isOpen={isUploadModalOpen} 
          onClose={() => setIsUploadModalOpen(false)} 
          activeWellId={selectedWell} 
      />

      {/* Manual Knowledge Search Drawer */}
      <KnowledgeSearch 
          isOpen={isKnowledgeSearchOpen}
          onClose={() => setIsKnowledgeSearchOpen(false)}
      />

      {/* Cross-Well Correlation Panel */}
      <CorrelationPanel 
          isOpen={isCorrelationOpen}
          onClose={() => setIsCorrelationOpen(false)}
          activeWell={selectedWell}
          offsetWell={selectedWell === 'OIL-BAGHJAN-1' ? 'OIL-NAHARKATIYA-1' : 'OIL-BAGHJAN-1'}
      />
    </div>
  );
}

export default App;
