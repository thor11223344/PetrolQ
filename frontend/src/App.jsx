import React, { useState, useEffect, useRef, useCallback } from 'react';
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
  Download,
  Radar,
  Gauge,
  FileText,
  Brain,
  CheckCircle2,
  Sparkles,
  X,
  ChevronRight,
  Layers,
  Play,
  Pause,
  RotateCcw,
  Flame,
  Droplets,
  Anchor,
  BarChart2
} from 'lucide-react';
import axios from 'axios';
import { API_BASE, WS_BASE } from './lib/api';
import Plot from 'react-plotly.js';

import WellMap from './components/WellMap';
import DocumentUploadModal from './components/DocumentUploadModal';
import KnowledgeSearch from './components/KnowledgeSearch';
import CorrelationPanel from './components/CorrelationPanel';
import LookAheadRadar from './components/LookAheadRadar';
import PPFGWindowModal from './components/PPFGWindowModal';
import PreSpudDossierModal from './components/PreSpudDossierModal';
import ContributeLessonModal from './components/ContributeLessonModal';

const WELL_DEFAULT_TELEMETRY = {
  'OIL-BAGHJAN-1': { well_id: 'OIL-BAGHJAN-1', depth_tvd: 2240.0, rop: 16.5, wob: 14.0, rpm: 105.0, torque: 13200.0, mud_weight: 11.2, ecd: 11.6, flow_out_pct: 100.0, pit_gain_bbl: 0.0, spp_psi: 2800.0 },
  'OIL-BAGHJAN-4': { well_id: 'OIL-BAGHJAN-4', depth_tvd: 2380.0, rop: 18.2, wob: 15.0, rpm: 110.0, torque: 14100.0, mud_weight: 11.4, ecd: 11.8, flow_out_pct: 100.0, pit_gain_bbl: 0.0, spp_psi: 2950.0 },
  'OIL-NAHARKATIYA-1': { well_id: 'OIL-NAHARKATIYA-1', depth_tvd: 2020.0, rop: 14.0, wob: 12.5, rpm: 95.0, torque: 11800.0, mud_weight: 10.8, ecd: 11.2, flow_out_pct: 100.0, pit_gain_bbl: 0.0, spp_psi: 2600.0 },
  'OIL-MORAN-1': { well_id: 'OIL-MORAN-1', depth_tvd: 2550.0, rop: 15.0, wob: 13.0, rpm: 100.0, torque: 12500.0, mud_weight: 11.0, ecd: 11.4, flow_out_pct: 100.0, pit_gain_bbl: 0.0, spp_psi: 2750.0 },
  'OIL-DIKOM-1': { well_id: 'OIL-DIKOM-1', depth_tvd: 2200.0, rop: 17.0, wob: 14.5, rpm: 105.0, torque: 13500.0, mud_weight: 11.3, ecd: 11.7, flow_out_pct: 100.0, pit_gain_bbl: 0.0, spp_psi: 2850.0 },
};

function App() {
  const [selectedWell, setSelectedWell] = useState('OIL-BAGHJAN-1');
  const [telemetryData, setTelemetryData] = useState(WELL_DEFAULT_TELEMETRY['OIL-BAGHJAN-1']);
  const [predictionData, setPredictionData] = useState(null);
  const [simStatus, setSimStatus] = useState({ is_running: false, active_scenario: 'normal' });
  const [simSpeed, setSimSpeed] = useState(1.0);
  const [seekDepth, setSeekDepth] = useState(2240.0);
  const [isDraggingSeek, setIsDraggingSeek] = useState(false);
  const [proximityWarning, setProximityWarning] = useState(null);
  const [trajectoryData, setTrajectoryData] = useState({ depth: [], torque: [], rop: [] });
  const [alertState, setAlertState] = useState({ active: false, prediction: null });
  const alertActiveRef = useRef(false);
  const lastCheckedDepthRef = useRef(null);
  const [ragContext, setRagContext] = useState(null);
  const [recentEvents, setRecentEvents] = useState([]);
  const [newlyIngestedIds, setNewlyIngestedIds] = useState(new Set());
  const [uploadToast, setUploadToast] = useState(null);
  const [expandedEventId, setExpandedEventId] = useState(null);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
  const [isKnowledgeSearchOpen, setIsKnowledgeSearchOpen] = useState(false);
  const [isCorrelationOpen, setIsCorrelationOpen] = useState(false);
  const [isRadarOpen, setIsRadarOpen] = useState(false);
  const [isPPFGOpen, setIsPPFGOpen] = useState(false);
  const [isDossierOpen, setIsDossierOpen] = useState(false);
  const [isContributeOpen, setIsContributeOpen] = useState(false);
  const [role, setRole] = useState('Field Engineer');
  const [isBackendConnected, setIsBackendConnected] = useState(false);
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
        const res = await axios.get(`${API_BASE}/api/wells/${selectedWell}/history`);
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

  const fetchHistory = useCallback(async (wellId = selectedWell) => {
    try {
      const res = await axios.get(`${API_BASE}/api/wells/${wellId}/history`);
      if (res.data && res.data.events) {
        // Sort by ID descending so newly ingested events appear immediately at the top
        const sortedEvents = [...res.data.events].sort((a, b) => (b.id || 0) - (a.id || 0));
        setRecentEvents(sortedEvents.slice(0, 10));
      }
    } catch (err) {
      console.error("Failed to fetch well history", err);
      setRecentEvents([]);
    }
  }, [selectedWell]);

  useEffect(() => {
    fetchHistory(selectedWell);
  }, [selectedWell, fetchHistory]);

  const handleDocumentUploaded = (result, targetWellId) => {
    const wellToUse = targetWellId || selectedWell;
    if (targetWellId && targetWellId !== selectedWell) {
      setSelectedWell(targetWellId);
    }
    fetchHistory(wellToUse);

    const eventCount = result?.extracted_count || result?.events?.length || 0;
    if (result?.events && result.events.length > 0) {
      const newIds = new Set(result.events.map(e => e.id).filter(Boolean));
      setNewlyIngestedIds(newIds);
    }

    const isLas = result?.file_type === 'las' || result?.filename?.toLowerCase().endsWith('.las');
    setUploadToast({
      title: isLas ? `Ingested LAS Log: ${result?.filename || 'Well Log'}` : `Ingested ${eventCount > 0 ? `${eventCount} Incidents` : 'Report'} from ${result?.filename || 'Document'}`,
      description: isLas 
        ? `${result?.points_ingested || 'Log curve'} data points ingested for ${wellToUse}. Ready for cross-well correlation & PPFG analysis.` 
        : `Institutional Memory for ${wellToUse} updated with AI OCR/NLP extraction.`,
      count: eventCount,
      wellId: wellToUse,
      isLas: isLas,
      ocrTriggered: result?.ocr_triggered,
      time: new Date().toLocaleTimeString()
    });
  };

  const handleLessonContributed = (lesson) => {
    fetchHistory(selectedWell);
    setUploadToast({
      title: `Institutional Lesson Contributed!`,
      description: `New mitigations and root causes synchronized for ${selectedWell}.`,
      wellId: selectedWell,
      time: new Date().toLocaleTimeString()
    });
  };

  useEffect(() => {
    let isCleanedUp = false;
    let ws = null;
    let reconnectTimeout = null;

    const connectWebSocket = () => {
      if (isCleanedUp) return;
      try {
        ws = new WebSocket(`${WS_BASE}/api/ws/telemetry`);
        wsRef.current = ws;

        ws.onopen = () => {
          if (isCleanedUp) {
            ws.close();
            return;
          }
          // Connected successfully
          setIsBackendConnected(true);
          fetchHistory(selectedWell);
        };

        ws.onmessage = (event) => {
          if (isCleanedUp) return;
          try {
            const data = JSON.parse(event.data);
            if (data.status === 'success') {
              const currentTelemetry = data.data;
              const prediction = data.prediction;
              
              // Only set telemetry if initially null; client controls its own simulation progression
              setTelemetryData(prev => prev || currentTelemetry);
              if (prediction) {
                setPredictionData(prediction);
              }
              // Do NOT override local client simStatus from foreign broadcasts!
              
              // Update Trajectory Data for plotting (keep last 50 points to prevent lag)
              if (currentTelemetry && currentTelemetry.depth_tvd !== undefined) {
                setTrajectoryData(prev => {
                  const newDepth = [...prev.depth, currentTelemetry.depth_tvd].slice(-50);
                  const newTorque = [...prev.torque, currentTelemetry.torque].slice(-50);
                  const newRop = [...prev.rop, currentTelemetry.rop].slice(-50);
                  return { depth: newDepth, torque: newTorque, rop: newRop };
                });
              }

              // Check for High Risk Alert
              if (prediction?.risk_level === 'HIGH' || prediction?.risk_level === 'CRITICAL') {
                if (!alertActiveRef.current) {
                  alertActiveRef.current = true;
                  setAlertState({ active: true, prediction });
                  fetchRagContext(prediction);
                } else {
                  setAlertState(prev => ({ ...prev, prediction }));
                }
              } else if (data.scenario === 'normal' && prediction?.risk_level === 'LOW') {
                if (alertActiveRef.current) {
                  alertActiveRef.current = false;
                  setAlertState({ active: false, prediction: null });
                }
              }
            }
          } catch (err) {
            console.error("Error parsing websocket message", err);
          }
        };

        ws.onclose = () => {
          if (!isCleanedUp) {
            setIsBackendConnected(false);
            // Auto-reconnect after 3 seconds
            reconnectTimeout = setTimeout(() => {
              connectWebSocket();
            }, 3000);
          }
        };

        ws.onerror = () => {
          if (!isCleanedUp) {
            setIsBackendConnected(false);
          }
        };
      } catch (err) {
        setIsBackendConnected(false);
        if (!isCleanedUp) {
          reconnectTimeout = setTimeout(() => {
            connectWebSocket();
          }, 3000);
        }
      }
    };

    connectWebSocket();

    return () => {
      isCleanedUp = true;
      if (reconnectTimeout) clearTimeout(reconnectTimeout);
      if (ws) {
        if (ws.readyState === WebSocket.OPEN) {
          ws.close();
        } else if (ws.readyState === WebSocket.CONNECTING) {
          // Defer close until handshake finishes to avoid closing before connection established
          ws.onopen = () => {
            ws.close();
          };
        }
      }
    };
  }, [selectedWell, fetchHistory]);

  // Dedicated Client-Side Telemetry Simulation Loop (Strictly isolated to this browser tab/device)
  useEffect(() => {
    if (!simStatus.is_running) return;

    const interval = setInterval(() => {
      setTelemetryData(prev => {
        const current = prev || WELL_DEFAULT_TELEMETRY[selectedWell] || WELL_DEFAULT_TELEMETRY['OIL-BAGHJAN-1'];
        const speed = simSpeed || 1.0;
        const stepM = ((current.rop || 16.5) / 3600.0) * 150.0 * speed;
        let newDepth = (current.depth_tvd || 2240.0) + stepM;
        let newRop = current.rop || 16.5;
        let newTorque = current.torque || 13200.0;
        let newFlowOut = current.flow_out_pct !== undefined ? current.flow_out_pct : 100.0;
        let newPitGain = current.pit_gain_bbl !== undefined ? current.pit_gain_bbl : 0.0;
        let newSpp = current.spp_psi || 2800.0;
        let newMudWeight = current.mud_weight || 11.2;
        let newEcd = current.ecd || 11.6;

        if (simStatus.active_scenario === 'normal') {
          newTorque = Math.max(11000.0, Math.min(15000.0, newTorque + (Math.random() * 300 - 150)));
          newRop = Math.max(10.0, Math.min(22.0, newRop + (Math.random() * 0.8 - 0.4)));
          newFlowOut = Math.max(98.0, Math.min(102.0, newFlowOut + (Math.random() * 0.6 - 0.3)));
          newSpp = Math.max(2700.0, Math.min(2900.0, newSpp + (Math.random() * 30 - 15)));
        } else if (simStatus.active_scenario === 'gas_kick') {
          newPitGain += 0.3 * speed;
          newFlowOut = Math.max(105.0, Math.min(135.0, newFlowOut + (Math.random() * 1.3 - 0.5)));
          newSpp = Math.max(2400.0, newSpp - 10.0 * speed);
        } else if (simStatus.active_scenario === 'lost_circulation') {
          newPitGain -= 0.4 * speed;
          newFlowOut = Math.max(40.0, Math.min(85.0, newFlowOut + (Math.random() * 1.3 - 0.8)));
          newSpp = Math.max(1800.0, newSpp - 25.0 * speed);
        } else if (simStatus.active_scenario === 'stuck_pipe') {
          newTorque = Math.max(26000.0, Math.min(34000.0, newTorque + (Math.random() * 500 - 200)));
          newRop = Math.max(0.5, newRop - 2.0 * speed);
        }

        const updated = {
          ...current,
          well_id: selectedWell,
          depth_tvd: Math.round(newDepth * 100) / 100,
          rop: Math.round(newRop * 100) / 100,
          torque: Math.round(newTorque * 10) / 10,
          flow_out_pct: Math.round(newFlowOut * 10) / 10,
          pit_gain_bbl: Math.round(newPitGain * 10) / 10,
          spp_psi: Math.round(newSpp * 10) / 10,
          mud_weight: newMudWeight,
          ecd: newEcd,
          scenario: simStatus.active_scenario
        };

        // Query real-time ML risk prediction over WebSocket for THIS client only
        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
          wsRef.current.send(JSON.stringify(updated));
        }

        return updated;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [simStatus.is_running, simStatus.active_scenario, simSpeed, selectedWell]);

  // Proactive Depth-Proximity Lookahead Warning Engine (CORRECTION 3: Reuses /api/wells/{id}/lookahead)
  useEffect(() => {
    const checkDepthProximity = async () => {
      const currentDepth = telemetryData?.depth_tvd || 2240.0;
      
      if (lastCheckedDepthRef.current !== null && Math.abs(currentDepth - lastCheckedDepthRef.current) < 5.0) {
        return;
      }
      lastCheckedDepthRef.current = currentDepth;

      try {
        const res = await axios.get(`${API_BASE}/api/wells/${selectedWell}/lookahead`, {
          params: { current_depth: currentDepth, window_meters: 250.0 }
        });
        const lookahead = res.data;
        const dist = lookahead?.distance_to_next_formation_m;
        const nextForm = lookahead?.next_formation;
        
        // Trigger amber proactive warning when within 50m of impending formation or hazard corridor
        if (dist !== null && dist !== undefined && dist <= 50.0 && dist > 0) {
          const upcoming = lookahead?.upcoming_formations?.[0] || {};
          const kickCount = lookahead?.kick_events_count || 0;
          const nearestEvent = lookahead?.events?.[0];
          
          setProximityWarning({
            active: true,
            formation: nextForm || 'Target Formation',
            distance_m: dist,
            tvd_top: upcoming.tvd_top || Math.round(currentDepth + dist),
            primary_risk: upcoming.primary_risk || (kickCount > 0 ? 'Abnormal Gas Kick & Well Control Risk' : 'Stratigraphic Transition'),
            offset_precedent: nearestEvent ? `${nearestEvent.event_type} at ${nearestEvent.depth_tvd}m in ${nearestEvent.well_id}` : null
          });
        } else {
          setProximityWarning(null);
        }
      } catch (err) {
        console.error("Proactive lookahead proximity check failed", err);
      }
    };

    checkDepthProximity();
  }, [selectedWell, telemetryData?.depth_tvd]);

  // Simulator Control Handlers (Strictly isolated to this local browser session)
  const handleSimControl = (action) => {
    if (action === 'play') {
      setSimStatus(prev => ({ ...prev, is_running: true }));
    } else if (action === 'pause') {
      setSimStatus(prev => ({ ...prev, is_running: false }));
    } else if (action === 'reset') {
      const base = WELL_DEFAULT_TELEMETRY[selectedWell] || WELL_DEFAULT_TELEMETRY['OIL-BAGHJAN-1'];
      setSimStatus({ is_running: false, active_scenario: 'normal' });
      setTelemetryData(base);
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify(base));
      }
    }
  };

  const handleSpeedChange = (speed) => {
    setSimSpeed(speed);
  };

  const handleSeek = (depth) => {
    setTelemetryData(prev => {
      const current = prev || WELL_DEFAULT_TELEMETRY[selectedWell] || WELL_DEFAULT_TELEMETRY['OIL-BAGHJAN-1'];
      const updated = { ...current, depth_tvd: depth };
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify(updated));
      }
      return updated;
    });
  };

  const handleScenarioInject = (scenario) => {
    setSimStatus(prev => ({ ...prev, active_scenario: scenario }));
    setTelemetryData(prev => {
      const current = prev || WELL_DEFAULT_TELEMETRY[selectedWell] || WELL_DEFAULT_TELEMETRY['OIL-BAGHJAN-1'];
      let newFlowOut = current.flow_out_pct !== undefined ? current.flow_out_pct : 100.0;
      let newPitGain = current.pit_gain_bbl !== undefined ? current.pit_gain_bbl : 0.0;
      let newTorque = current.torque || 13200.0;
      let newSpp = current.spp_psi || 2800.0;

      if (scenario === 'gas_kick') {
        newFlowOut = 118.0;
        newPitGain = 3.5;
        newSpp = 2650.0;
      } else if (scenario === 'lost_circulation') {
        newFlowOut = 62.0;
        newPitGain = -4.2;
        newSpp = 2100.0;
      } else if (scenario === 'stuck_pipe') {
        newTorque = 28500.0;
      } else if (scenario === 'normal') {
        newFlowOut = 100.0;
        newPitGain = 0.0;
        newTorque = 13200.0;
        newSpp = 2800.0;
      }

      const updated = {
        ...current,
        flow_out_pct: newFlowOut,
        pit_gain_bbl: newPitGain,
        torque: newTorque,
        spp_psi: newSpp,
        scenario
      };

      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify(updated));
      }
      return updated;
    });
  };

  const handleSelectWell = (newWellId) => {
    setSelectedWell(newWellId);
    setProximityWarning(null);
    alertActiveRef.current = false;
    lastCheckedDepthRef.current = null;
    setAlertState({ active: false, prediction: null });
    const base = WELL_DEFAULT_TELEMETRY[newWellId] || WELL_DEFAULT_TELEMETRY['OIL-BAGHJAN-1'];
    setTelemetryData(base);
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(base));
    }
  };


  const fetchRagContext = async (prediction) => {
      try {
          // Construct a dynamic query based on top factors
          let query = "high surface torque and drilling hazard";
          if (prediction?.top_factors?.length > 0) {
              const topFactor = prediction.top_factors[0].feature;
              query = `Elevated ${topFactor} causing potential hazard during drilling`;
          }
          
          const response = await axios.get(`${API_BASE}/api/events/search`, {
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
      alertActiveRef.current = false;
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
            PetrolQ <span className="text-slate-500 font-normal ml-2">| PetrolQ Platform</span>
          </h1>
        </div>

        <div className="flex items-center space-x-6">
          {/* Status Indicator */}
          <div className="flex items-center space-x-2 bg-slate-800/50 px-3 py-1.5 rounded-full border border-slate-700/50">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-status-active opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-status-active"></span>
            </span>
            <span className="text-xs font-medium text-slate-300">Live Feed: Connected</span>
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
                  onChange={(e) => handleSelectWell(e.target.value)}
                  className="bg-transparent text-slate-200 text-sm font-medium outline-none cursor-pointer"
              >
                  <option value="OIL-BAGHJAN-1">OIL-BAGHJAN-1</option>
                  <option value="OIL-BAGHJAN-4">OIL-BAGHJAN-4</option>
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

          {/* Backend API Live Status Indicator */}
          <div className="flex items-center space-x-2 border-l border-slate-800 pl-4">
            {isBackendConnected ? (
              <div 
                className="flex items-center space-x-1.5 px-2.5 py-1 rounded-md bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-mono"
                title="FastAPI Backend is online on port 8000"
              >
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                <span>API Online</span>
              </div>
            ) : (
              <div 
                className="flex items-center space-x-1.5 px-2.5 py-1 rounded-md bg-rose-500/15 border border-rose-500/40 text-rose-300 text-xs font-mono animate-pulse"
                title="FastAPI is offline at port 8000. Start it via 'npm run dev' or '.\start.bat'"
              >
                <span className="w-2 h-2 rounded-full bg-rose-500"></span>
                <span>API Offline (:8000)</span>
              </div>
            )}
          </div>

          {/* Core Decision Support Modules (SIH 2026 Mandate) */}
          <div className="flex items-center space-x-2 border-l border-slate-800 pl-4">
            <button 
                onClick={() => setIsRadarOpen(true)}
                className="flex items-center space-x-1.5 text-xs font-semibold px-2.5 py-1.5 rounded-lg bg-amber-500/10 hover:bg-amber-500/20 text-amber-300 border border-amber-500/30 transition shadow-sm"
                title="Ahead-of-the-Bit Hazard Radar"
            >
                <Radar size={14} className="text-amber-400" />
                <span>Hazard Radar</span>
            </button>

            <button 
                onClick={() => setIsCorrelationOpen(true)}
                className="flex items-center space-x-1.5 text-xs font-semibold px-2.5 py-1.5 rounded-lg bg-indigo-500/10 hover:bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 transition shadow-sm"
                title="Cross-Well Correlation, Casing Programs & Stratigraphic Cross-Section"
            >
                <Layers size={14} className="text-indigo-400" />
                <span>Correlation & Cross-Section</span>
            </button>

            <button 
                onClick={() => setIsPPFGOpen(true)}
                className="flex items-center space-x-1.5 text-xs font-semibold px-2.5 py-1.5 rounded-lg bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 transition shadow-sm"
                title="Pore Pressure & Fracture Gradient Safe Mud Window"
            >
                <Gauge size={14} className="text-emerald-400" />
                <span>Safe Mud Weight Window</span>
            </button>

            <button 
                onClick={() => setIsDossierOpen(true)}
                className="flex items-center space-x-1.5 text-xs font-semibold px-2.5 py-1.5 rounded-lg bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 transition shadow-sm"
                title="1-Click Pre-Spud Offset Hazard Dossier"
            >
                <FileText size={14} className="text-cyan-400" />
                <span>Pre-Spud Report</span>
            </button>

            <button 
                onClick={() => setIsContributeOpen(true)}
                className="flex items-center space-x-1.5 text-xs font-semibold px-2.5 py-1.5 rounded-lg bg-purple-500/10 hover:bg-purple-500/20 text-purple-300 border border-purple-500/30 transition shadow-sm"
                title="Add Field Lesson Learned to Institutional Memory"
            >
                <Brain size={14} className="text-purple-400" />
                <span>Add Lesson Learned</span>
            </button>
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
      <main className="flex-1 relative flex min-h-0 overflow-hidden">
        
        {/* Map Container */}
        <div className="flex-1 bg-slate-900 relative overflow-hidden flex flex-col">
          
          {/* Proactive Depth-Proximity Lookahead Warning Banner (CORRECTION 3: Reuses /api/wells/{id}/lookahead) */}
          {proximityWarning?.active && (
            <div className="absolute top-3 left-4 right-4 z-30 bg-gradient-to-r from-amber-950/95 via-amber-900/90 to-amber-950/95 border-2 border-amber-500/80 p-3.5 rounded-xl shadow-2xl backdrop-blur-md flex items-center justify-between gap-4 animate-in slide-in-from-top-3">
              <div className="flex items-center space-x-3">
                <div className="p-2.5 bg-amber-500/20 rounded-lg border border-amber-500/40 text-amber-300 animate-pulse shrink-0">
                  <AlertTriangle size={22} />
                </div>
                <div>
                  <div className="flex items-center space-x-2">
                    <span className="text-[11px] font-black uppercase tracking-wider bg-amber-500 text-slate-950 px-2 py-0.5 rounded font-mono">
                      Proactive Proximity Alert
                    </span>
                    <span className="text-xs font-bold text-amber-200">
                      {proximityWarning.distance_m}m Ahead: Impending Entry into {proximityWarning.formation} ({proximityWarning.tvd_top}m TVD)
                    </span>
                  </div>
                  <p className="text-xs text-amber-100/90 mt-1">
                    <strong className="text-white">Threat:</strong> {proximityWarning.primary_risk}
                    {proximityWarning.offset_precedent && (
                      <span className="text-amber-300 font-mono ml-2">
                        • Precedent: {proximityWarning.offset_precedent}
                      </span>
                    )}
                  </p>
                </div>
              </div>

              <div className="flex items-center space-x-2 shrink-0">
                <button
                  onClick={() => setIsRadarOpen(true)}
                  className="px-3.5 py-1.5 rounded-lg bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs flex items-center space-x-1.5 shadow-lg shadow-amber-500/30 transition cursor-pointer"
                >
                  <Radar size={14} />
                  <span>Inspect Ahead-of-Bit Radar</span>
                </button>
                <button
                  onClick={() => setProximityWarning(null)}
                  className="p-1 rounded-lg text-amber-300/70 hover:text-white hover:bg-amber-900/50 transition"
                  title="Dismiss alert"
                >
                  <X size={16} />
                </button>
              </div>
            </div>
          )}

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

            {/* Ahead-of-the-Bit Hazard Radar Overlay Card */}
            {(() => {
              const WELL_RADAR_PREVIEWS = {
                'OIL-BAGHJAN-1': { horizon: 'Barail Kick Horizon', top: '2,400m' },
                'OIL-BAGHJAN-4': { horizon: 'Barail Gas Sand', top: '2,420m' },
                'OIL-NAHARKATIYA-1': { horizon: 'Barail Sand-Shale', top: '2,040m' },
                'OIL-MORAN-1': { horizon: 'Deep Barail Interval', top: '2,580m' },
                'OIL-DIKOM-1': { horizon: 'Barail Sandstone Top', top: '2,240m' },
                'OIL-TENGAKHAT-1': { horizon: 'Barail Main Sand', top: '2,120m' },
                'OIL-KOTHALONI-1': { horizon: 'Barail Argillaceous', top: '2,320m' },
                'OIL-HAPJAN-1': { horizon: 'Barail Coal Sequence', top: '2,360m' },
                'OIL-SHALMARI-1': { horizon: 'Barail Laminated Sand', top: '2,210m' },
              };
              const preview = WELL_RADAR_PREVIEWS[selectedWell] || { horizon: 'Barail Horizon', top: '2,400m' };
              return (
                <button 
                  onClick={() => setIsRadarOpen(true)}
                  className="bg-slate-900/90 backdrop-blur border border-amber-500/40 hover:border-amber-500 p-3.5 rounded-lg shadow-xl min-w-[220px] text-left transition group cursor-pointer"
                >
                  <div className="flex items-center justify-between text-xs uppercase text-amber-400 font-bold mb-1.5">
                    <span className="flex items-center space-x-1.5">
                      <Radar size={14} className="animate-spin-slow" />
                      <span>Hazard Radar</span>
                    </span>
                    <span className="text-[10px] bg-amber-500/20 px-1.5 py-0.5 rounded font-mono text-amber-300">+250m Scan</span>
                  </div>
                  <div className="text-sm font-bold text-white group-hover:text-amber-300 transition truncate">
                    {preview.horizon}
                  </div>
                  <div className="text-[11px] text-slate-400 mt-1 flex items-center justify-between">
                    <span>Next Top: ~{preview.top}</span>
                    <span className="text-cyan-400 font-bold">Open Radar →</span>
                  </div>
                </button>
              );
            })()}
          </div>

          {/* In-App Telemetry Feed Controller (CORRECTION 4: Realistic Scenario Injector) */}
          <div className="absolute bottom-6 left-4 z-20 bg-slate-900/95 backdrop-blur-md border border-slate-700/80 p-3 rounded-xl shadow-2xl flex flex-wrap items-center gap-3">
            <div className="flex items-center space-x-2 border-r border-slate-800 pr-3">
              <button
                onClick={() => handleSimControl(simStatus.is_running ? 'pause' : 'play')}
                className={`px-3 py-1.5 rounded-lg font-bold text-xs flex items-center space-x-1.5 transition shadow-md ${
                  simStatus.is_running
                    ? 'bg-amber-500 hover:bg-amber-400 text-slate-950 shadow-amber-500/20'
                    : 'bg-emerald-500 hover:bg-emerald-400 text-slate-950 shadow-emerald-500/20'
                }`}
              >
                {simStatus.is_running ? <Pause size={14} /> : <Play size={14} />}
                <span>{simStatus.is_running ? 'Pause Simulator' : 'Play Simulator'}</span>
              </button>

              <button
                onClick={() => handleSimControl('reset')}
                className="p-1.5 rounded-lg border border-slate-700 hover:bg-slate-800 text-slate-400 hover:text-white transition"
                title="Reset TVD to 2240m"
              >
                <RotateCcw size={14} />
              </button>
            </div>

            {/* Speed Controls */}
            <div className="flex items-center space-x-1 border-r border-slate-800 pr-3">
              {[1, 2, 5].map(speed => (
                <button
                  key={speed}
                  onClick={() => handleSpeedChange(speed)}
                  className={`px-2 py-1 rounded text-xs font-bold transition ${
                    simSpeed === speed
                      ? 'bg-cyan-500 text-slate-900 shadow-md shadow-cyan-500/20'
                      : 'bg-slate-800 text-slate-400 hover:text-white hover:bg-slate-700 border border-slate-700'
                  }`}
                  title={`${speed}x Simulation Speed`}
                >
                  {speed}x
                </button>
              ))}
            </div>

            {/* Seek Control */}
            <div className="flex items-center space-x-3 border-r border-slate-800 pr-3 min-w-[200px]">
              <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider">Seek:</span>
              <input
                type="range"
                min="0"
                max="3500"
                step="10"
                value={isDraggingSeek ? seekDepth : (telemetryData?.depth_tvd || 2240)}
                onPointerDown={() => setIsDraggingSeek(true)}
                onChange={(e) => setSeekDepth(parseFloat(e.target.value))}
                onPointerUp={(e) => {
                  setIsDraggingSeek(false);
                  handleSeek(parseFloat(e.target.value));
                }}
                className="flex-1 accent-cyan-500 cursor-pointer h-1.5 bg-slate-800 rounded-lg appearance-none"
              />
              <span className="text-[10px] font-mono text-slate-300 w-12 text-right">
                {(isDraggingSeek ? seekDepth : (telemetryData?.depth_tvd || 2240)).toFixed(0)}m
              </span>
            </div>

            {/* Scenario Injectors */}
            <div className="flex items-center space-x-1.5">
              <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider mr-1">Inject:</span>
              
              <button
                onClick={() => handleScenarioInject('normal')}
                className={`px-2.5 py-1 rounded text-xs font-semibold transition border ${
                  simStatus.active_scenario === 'normal'
                    ? 'bg-emerald-500/20 border-emerald-500/60 text-emerald-300'
                    : 'bg-slate-800/80 border-slate-700/60 text-slate-400 hover:text-white'
                }`}
                title="Nominal baseline circulating parameters"
              >
                Normal
              </button>

              <button
                onClick={() => handleScenarioInject('gas_kick')}
                className={`px-2.5 py-1 rounded text-xs font-semibold transition border flex items-center space-x-1 ${
                  simStatus.active_scenario === 'gas_kick'
                    ? 'bg-amber-500/30 border-amber-500/80 text-amber-300 shadow-[0_0_10px_rgba(245,158,11,0.3)]'
                    : 'bg-amber-950/20 border-amber-800/40 text-amber-400 hover:bg-amber-900/30'
                }`}
                title="Simulate formation gas influx (flow-out increase, pit gain, SPP drop)"
              >
                <Flame size={12} />
                <span>Inject Gas Kick</span>
              </button>

              <button
                onClick={() => handleScenarioInject('lost_circulation')}
                className={`px-2.5 py-1 rounded text-xs font-semibold transition border flex items-center space-x-1 ${
                  simStatus.active_scenario === 'lost_circulation'
                    ? 'bg-cyan-500/30 border-cyan-500/80 text-cyan-300 shadow-[0_0_10px_rgba(6,182,212,0.3)]'
                    : 'bg-cyan-950/20 border-cyan-800/40 text-cyan-400 hover:bg-cyan-900/30'
                }`}
                title="Simulate mud loss (flow-out deficit, pit volume drop, ECD decrease)"
              >
                <Droplets size={12} />
                <span>Inject Lost Circ</span>
              </button>

              <button
                onClick={() => handleScenarioInject('stuck_pipe')}
                className={`px-2.5 py-1 rounded text-xs font-semibold transition border flex items-center space-x-1 ${
                  simStatus.active_scenario === 'stuck_pipe'
                    ? 'bg-rose-500/30 border-rose-500/80 text-rose-300 shadow-[0_0_10px_rgba(244,63,94,0.3)]'
                    : 'bg-rose-950/20 border-rose-800/40 text-rose-400 hover:bg-rose-900/30'
                }`}
                title="Simulate mechanical packoff (torque spike, zero ROP, motor stall)"
              >
                <Anchor size={12} />
                <span>Inject Stuck Pipe</span>
              </button>
            </div>

            {/* Active Status Badge */}
            <div className="flex items-center space-x-2 border-l border-slate-800 pl-3">
              <span className={`w-2 h-2 rounded-full ${simStatus.is_running ? 'bg-emerald-400 animate-ping' : 'bg-slate-600'}`}></span>
              <span className="text-[11px] font-mono text-slate-300">
                {simStatus.active_scenario !== 'normal' ? (
                  <span className="text-amber-400 font-bold uppercase">{simStatus.active_scenario.replace('_', ' ')} (Active)</span>
                ) : (
                  <span>Baseline Steady</span>
                )}
              </span>
            </div>
          </div>


          <WellMap 
             activeWellId={selectedWell} 
             onSelectWell={handleSelectWell} 
             currentDepth={telemetryData ? telemetryData.depth_tvd : null}
             activeScenario={simStatus.active_scenario}
          />
        </div>

        {/* Right-Hand Drawer */}
        <aside className="w-[450px] border-l border-slate-800 bg-slate-950 flex flex-col shadow-2xl z-20 shrink-0 relative h-full min-h-0 overflow-hidden">
          
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
                    <span className="font-bold uppercase text-xs">PetrolQ</span>
                  </div>
                  <p className="mb-2"><span className="text-slate-400">Historical Match:</span> Offset well <span className="font-mono text-xs text-blue-300">{ragContext.well_id}</span> experienced <strong className="text-white">{ragContext.event_type}</strong> at {ragContext.depth_tvd}m.</p>
                  <p><span className="text-slate-400">Recommended Mitigation:</span> <span className="text-emerald-400 font-medium">{ragContext.mitigation_applied}</span></p>
                </div>
              ) : (
                <div className="text-sm text-red-200 animate-pulse">Fetching PetrolQ...</div>
              )}
            </div>
          )}

          <div className="p-4 border-b border-slate-800 flex items-center justify-between shrink-0">
            <h2 className="font-medium text-slate-200">Real-Time Telemetry</h2>
            <div className="flex space-x-1">
              <div className="w-2 h-2 rounded-full bg-status-danger mt-1"></div>
              <div className="w-2 h-2 rounded-full bg-status-warning mt-1"></div>
            </div>
          </div>
          
          <div className="flex-1 p-4 overflow-y-auto custom-scrollbar pb-10 space-y-4">
            
            {/* Multi-Hazard Risk Engine Gauges (SIH 2026 Mandate) */}
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm space-y-3">
              <div className="flex items-center justify-between border-b border-slate-800/80 pb-2.5">
                <div className="flex items-center space-x-2">
                  <Gauge size={16} className="text-cyan-400" />
                  <h3 className="text-xs uppercase font-bold text-slate-300 tracking-wider">Multi-Hazard Risk Engine</h3>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-xs text-slate-400">Composite:</span>
                  <span className={`text-xs font-bold font-mono px-2 py-0.5 rounded ${
                    (predictionData?.risk_probability || 0.15) >= 0.75 ? 'bg-red-500/20 text-red-400 border border-red-500/40' :
                    (predictionData?.risk_probability || 0.15) >= 0.40 ? 'bg-amber-500/20 text-amber-400 border border-amber-500/40' :
                    'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40'
                  }`}>
                    {Math.round((predictionData?.risk_probability || 0.15) * 100)}% ({predictionData?.risk_level || 'LOW'})
                  </span>
                </div>
              </div>

              {/* 4 Disaggregated Hazard Indicators */}
              <div className="grid grid-cols-2 gap-2.5">
                {/* Gas Kick */}
                {(() => {
                  const kick = predictionData?.hazards?.gas_kick || { probability: 0.08, level: 'LOW', key_indicator: 'Flow: 100%, Pit: +0 bbl' };
                  return (
                    <div className="p-2.5 rounded-lg bg-slate-950/70 border border-slate-800 flex flex-col justify-between">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-[11px] font-semibold text-slate-300 flex items-center space-x-1">
                          <Flame size={12} className="text-amber-400" />
                          <span>Gas Kick</span>
                        </span>
                        <span className={`text-[10px] font-mono font-bold ${kick.probability > 0.6 ? 'text-amber-400' : 'text-slate-400'}`}>
                          {Math.round(kick.probability * 100)}%
                        </span>
                      </div>
                      <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden mb-1.5">
                        <div 
                          className={`h-full transition-all duration-500 ${kick.probability > 0.7 ? 'bg-red-500' : kick.probability > 0.35 ? 'bg-amber-500' : 'bg-emerald-500'}`}
                          style={{ width: `${Math.round(kick.probability * 100)}%` }}
                        />
                      </div>
                      <span className="text-[10px] text-slate-400 font-mono truncate">{kick.key_indicator || 'Nominal'}</span>
                    </div>
                  );
                })()}

                {/* Lost Circulation */}
                {(() => {
                  const loss = predictionData?.hazards?.lost_circulation || { probability: 0.07, level: 'LOW', key_indicator: 'Flow: 100%, Normal FG' };
                  return (
                    <div className="p-2.5 rounded-lg bg-slate-950/70 border border-slate-800 flex flex-col justify-between">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-[11px] font-semibold text-slate-300 flex items-center space-x-1">
                          <Droplets size={12} className="text-cyan-400" />
                          <span>Lost Circ</span>
                        </span>
                        <span className={`text-[10px] font-mono font-bold ${loss.probability > 0.6 ? 'text-cyan-400' : 'text-slate-400'}`}>
                          {Math.round(loss.probability * 100)}%
                        </span>
                      </div>
                      <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden mb-1.5">
                        <div 
                          className={`h-full transition-all duration-500 ${loss.probability > 0.7 ? 'bg-red-500' : loss.probability > 0.35 ? 'bg-cyan-500' : 'bg-emerald-500'}`}
                          style={{ width: `${Math.round(loss.probability * 100)}%` }}
                        />
                      </div>
                      <span className="text-[10px] text-slate-400 font-mono truncate">{loss.key_indicator || 'Nominal'}</span>
                    </div>
                  );
                })()}

                {/* Stuck Pipe */}
                {(() => {
                  const stuck = predictionData?.hazards?.stuck_pipe || { probability: 0.06, level: 'LOW', key_indicator: 'Torque Normal' };
                  return (
                    <div className="p-2.5 rounded-lg bg-slate-950/70 border border-slate-800 flex flex-col justify-between">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-[11px] font-semibold text-slate-300 flex items-center space-x-1">
                          <Anchor size={12} className="text-rose-400" />
                          <span>Stuck Pipe</span>
                        </span>
                        <span className={`text-[10px] font-mono font-bold ${stuck.probability > 0.6 ? 'text-rose-400' : 'text-slate-400'}`}>
                          {Math.round(stuck.probability * 100)}%
                        </span>
                      </div>
                      <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden mb-1.5">
                        <div 
                          className={`h-full transition-all duration-500 ${stuck.probability > 0.7 ? 'bg-red-500' : stuck.probability > 0.35 ? 'bg-rose-500' : 'bg-emerald-500'}`}
                          style={{ width: `${Math.round(stuck.probability * 100)}%` }}
                        />
                      </div>
                      <span className="text-[10px] text-slate-400 font-mono truncate">{stuck.key_indicator || 'Torque normal'}</span>
                    </div>
                  );
                })()}

                {/* Torque & Drag */}
                {(() => {
                  const torqueH = predictionData?.hazards?.torque_drag || { probability: 0.08, level: 'LOW', key_indicator: 'Smooth Rotation' };
                  return (
                    <div className="p-2.5 rounded-lg bg-slate-950/70 border border-slate-800 flex flex-col justify-between">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-[11px] font-semibold text-slate-300 flex items-center space-x-1">
                          <RotateCcw size={12} className="text-purple-400" />
                          <span>Torque & Drag</span>
                        </span>
                        <span className={`text-[10px] font-mono font-bold ${torqueH.probability > 0.6 ? 'text-purple-400' : 'text-slate-400'}`}>
                          {Math.round(torqueH.probability * 100)}%
                        </span>
                      </div>
                      <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden mb-1.5">
                        <div 
                          className={`h-full transition-all duration-500 ${torqueH.probability > 0.7 ? 'bg-red-500' : torqueH.probability > 0.35 ? 'bg-purple-500' : 'bg-emerald-500'}`}
                          style={{ width: `${Math.round(torqueH.probability * 100)}%` }}
                        />
                      </div>
                      <span className="text-[10px] text-slate-400 font-mono truncate">{torqueH.key_indicator || 'Nominal'}</span>
                    </div>
                  );
                })()}
              </div>

              {/* Physics Parameters Footer */}
              <div className="pt-2 border-t border-slate-800/80 grid grid-cols-3 gap-2 text-[11px] font-mono text-slate-400">
                <div>
                  <span className="text-slate-500 block">MSE:</span>
                  <span className="text-white font-semibold">{predictionData?.mse_kpsi || '---'} kpsi</span>
                </div>
                <div>
                  <span className="text-slate-500 block">d_xc:</span>
                  <span className="text-white font-semibold">{predictionData?.d_xc || '---'}</span>
                </div>
                <div>
                  <span className="text-slate-500 block">FG Margin:</span>
                  <span className="text-emerald-400 font-semibold">
                    {predictionData?.fracture_margin_ppg ? `${predictionData.fracture_margin_ppg > 0 ? '+' : ''}${predictionData.fracture_margin_ppg} ppg` : '---'}
                  </span>
                </div>
              </div>
            </div>

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
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center space-x-2">
                  <h3 className="text-xs uppercase font-bold text-slate-400 tracking-wider">Offset Incidents & Memory</h3>
                  <span className="text-[11px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-cyan-400 border border-slate-700">
                    {recentEvents.length}
                  </span>
                </div>
                <button 
                  onClick={() => fetchHistory(selectedWell)}
                  className="text-[11px] text-slate-500 hover:text-cyan-400 transition"
                  title="Reload event log"
                >
                  Refresh
                </button>
              </div>

              <div className="space-y-2">
                {recentEvents.length > 0 ? recentEvents.map((event, i) => {
                  const isNewlyAdded = newlyIngestedIds.has(event.id);
                  const isExpanded = expandedEventId === event.id;
                  const severity = (event.severity || 'HIGH').toUpperCase();
                  const sevColor = severity === 'CRITICAL' ? 'bg-red-500/20 text-red-400 border-red-500/40' :
                                   severity === 'HIGH' ? 'bg-amber-500/20 text-amber-400 border-amber-500/40' :
                                   'bg-blue-500/20 text-blue-400 border-blue-500/40';

                  return (
                    <div 
                      key={event.id || i} 
                      onClick={() => setExpandedEventId(isExpanded ? null : event.id)}
                      className={`p-3 rounded-lg border transition-all cursor-pointer ${
                        isNewlyAdded 
                          ? 'bg-emerald-950/30 border-emerald-500/60 shadow-md shadow-emerald-950/40' 
                          : 'bg-slate-950/60 border-slate-800/80 hover:border-slate-700'
                      }`}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div className="flex items-center space-x-2">
                          <div className={`w-2 h-2 rounded-full shrink-0 ${
                            isNewlyAdded ? 'bg-emerald-400 animate-ping' :
                            severity === 'CRITICAL' ? 'bg-status-danger' : 
                            severity === 'HIGH' ? 'bg-status-warning' : 'bg-status-fluid'
                          }`} />
                          <span className="text-sm font-semibold text-slate-200">{event.event_type}</span>
                        </div>
                        <div className="flex items-center space-x-1.5 shrink-0">
                          {isNewlyAdded && (
                            <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 animate-pulse">
                              INGESTED
                            </span>
                          )}
                          <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold border ${sevColor}`}>
                            {severity}
                          </span>
                        </div>
                      </div>

                      <div className="flex items-center justify-between mt-2 text-xs text-slate-400">
                        <span>Depth: <strong className="text-slate-300 font-mono">{event.depth_tvd}m</strong> TVD</span>
                        {event.formation && (
                          <span className="text-slate-400 truncate max-w-[140px] text-[11px]">{event.formation}</span>
                        )}
                      </div>

                      {/* Expanded Details */}
                      {isExpanded && (
                        <div className="mt-3 pt-3 border-t border-slate-800/80 text-xs space-y-2 animate-in fade-in duration-150">
                          {event.root_cause && (
                            <div>
                              <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block">Root Cause</span>
                              <p className="text-slate-300 mt-0.5 leading-relaxed bg-slate-900/80 p-2 rounded border border-slate-800">
                                {event.root_cause}
                              </p>
                            </div>
                          )}
                          {event.mitigation_applied && (
                            <div>
                              <span className="text-[11px] font-bold text-emerald-400 uppercase tracking-wider block">Mitigation Applied</span>
                              <p className="text-emerald-300/90 mt-0.5 leading-relaxed bg-emerald-950/20 p-2 rounded border border-emerald-900/40">
                                {event.mitigation_applied}
                              </p>
                            </div>
                          )}
                          {event.npt_hours > 0 && (
                            <div className="flex items-center justify-between text-[11px] text-slate-400 pt-1">
                              <span>Non-Productive Time (NPT):</span>
                              <span className="font-bold text-amber-400 font-mono">{event.npt_hours} Hours</span>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  );
                }) : (
                  <div className="text-sm text-slate-500 p-4 text-center bg-slate-950/40 rounded-lg border border-slate-800/50">
                    No offset events recorded for this well yet. Upload a DDR or WCR PDF to ingest incidents.
                  </div>
                )}
              </div>
              <button 
                onClick={() => setIsCorrelationOpen(true)}
                className="w-full mt-4 bg-status-active/20 hover:bg-status-active/30 text-status-active text-sm font-medium py-2 rounded transition-colors border border-status-active/30 flex items-center justify-center"
              >
                Correlate with Offset Well
              </button>
              
              <div className="grid grid-cols-2 gap-2 mt-2">
                <button 
                  onClick={() => setIsPPFGOpen(true)}
                  className="bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium py-2 px-2 rounded border border-slate-700 flex items-center justify-center space-x-1 transition"
                  title="Safe Mud Weight Operating Window"
                >
                  <Gauge size={14} className="text-emerald-400" />
                  <span>Safe Mud Window</span>
                </button>
                <button 
                  onClick={() => setIsDossierOpen(true)}
                  className="bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium py-2 px-2 rounded border border-slate-700 flex items-center justify-center space-x-1 transition"
                  title="1-Click Pre-Spud Risk Dossier"
                >
                  <FileText size={14} className="text-cyan-400" />
                  <span>Pre-Spud Report</span>
                </button>
              </div>

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

      {/* Ahead-of-the-Bit Hazard Radar Modal */}
      <LookAheadRadar 
          isOpen={isRadarOpen}
          onClose={() => setIsRadarOpen(false)}
          activeWellId={selectedWell}
          currentDepth={telemetryData ? telemetryData.depth_tvd : undefined}
      />

      {/* Safe Operating Mud Weight Window (PPFG) Modal */}
      <PPFGWindowModal 
          isOpen={isPPFGOpen}
          onClose={() => setIsPPFGOpen(false)}
          activeWellId={selectedWell}
      />

      {/* 1-Click Pre-Spud Offset Hazard Dossier Modal */}
      <PreSpudDossierModal 
          isOpen={isDossierOpen}
          onClose={() => setIsDossierOpen(false)}
          activeWellId={selectedWell}
      />

      {/* Floating Ingestion / Institutional Memory Toast Notification */}
      {uploadToast && (
        <div className="fixed top-16 right-6 z-50 max-w-md bg-slate-900/95 backdrop-blur-md border border-emerald-500/50 rounded-xl p-4 shadow-2xl shadow-emerald-950/60 animate-in slide-in-from-top-4 flex items-start space-x-3.5">
          <div className="p-2 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 shrink-0 mt-0.5">
            <Sparkles size={20} />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between">
              <h4 className="text-sm font-bold text-white truncate">{uploadToast.title}</h4>
              <button 
                onClick={() => setUploadToast(null)} 
                className="text-slate-400 hover:text-white transition ml-2"
              >
                <X size={16} />
              </button>
            </div>
            <p className="text-xs text-slate-300 mt-1 leading-relaxed">
              {uploadToast.description}
            </p>
            <div className="flex items-center space-x-2 mt-3">
              {uploadToast.isLas ? (
                <button
                  onClick={() => {
                    setIsCorrelationOpen(true);
                    setUploadToast(null);
                  }}
                  className="text-xs font-semibold px-2.5 py-1 rounded bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 hover:bg-cyan-500/30 transition flex items-center space-x-1"
                >
                  <Layers size={12} />
                  <span>View Log Correlation</span>
                </button>
              ) : (
                <button
                  onClick={() => {
                    setIsRadarOpen(true);
                    setUploadToast(null);
                  }}
                  className="text-xs font-semibold px-2.5 py-1 rounded bg-amber-500/20 text-amber-300 border border-amber-500/40 hover:bg-amber-500/30 transition flex items-center space-x-1"
                >
                  <Radar size={12} />
                  <span>Open Hazard Radar</span>
                </button>
              )}
              <button
                onClick={() => {
                  setIsKnowledgeSearchOpen(true);
                  setUploadToast(null);
                }}
                className="text-xs font-semibold px-2.5 py-1 rounded bg-slate-800 text-cyan-300 border border-slate-700 hover:bg-slate-700 transition flex items-center space-x-1"
              >
                <Search size={12} />
                <span>Search Vector DB</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Institutional Memory Contribution Modal (Two-Way Feedback) */}
      <ContributeLessonModal 
          isOpen={isContributeOpen}
          onClose={() => setIsContributeOpen(false)}
          activeWellId={selectedWell}
          onLessonContributed={handleLessonContributed}
      />

      {/* Document Upload Modal */}
      <DocumentUploadModal 
          isOpen={isUploadModalOpen} 
          onClose={() => setIsUploadModalOpen(false)} 
          activeWellId={selectedWell} 
          onUploadSuccess={handleDocumentUploaded}
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
