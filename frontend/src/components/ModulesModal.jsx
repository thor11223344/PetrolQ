import React, { useState, useEffect } from 'react';
import { 
  Layers, 
  Radar, 
  Gauge, 
  FileText, 
  History, 
  Brain, 
  X, 
  ChevronRight, 
  CheckCircle2, 
  ShieldCheck, 
  Activity, 
  AlertTriangle,
  ArrowRight,
  Filter,
  LayoutGrid,
  ListFilter,
  Maximize2,
  ExternalLink
} from 'lucide-react';

export default function ModulesModal({
  isOpen,
  onClose,
  onOpenRadar,
  onOpenCorrelation,
  onOpenPPFG,
  onOpenDossier,
  onOpenBacktest,
  onOpenContribute,
  activeWellId = 'OIL-BAGHJAN-1',
  currentDepth = 2240.0,
  isBackendConnected = false
}) {
  const [selectedFilter, setSelectedFilter] = useState('all');
  const [viewMode, setViewMode] = useState('grid'); // 'grid' | 'list'

  // Helper to launch any module in a new browser tab in fullscreen mode
  const launchModuleInNewTab = (moduleId, fallbackFn) => {
    const url = `${window.location.origin}${window.location.pathname}?module=${moduleId}&well=${encodeURIComponent(activeWellId || 'OIL-BAGHJAN-1')}&fullscreen=true`;
    try {
      const newTab = window.open(url, '_blank');
      if (!newTab || newTab.closed || typeof newTab.closed === 'undefined') {
        if (fallbackFn) fallbackFn();
      }
    } catch (err) {
      console.warn('window.open failed, falling back to local open:', err);
      if (fallbackFn) fallbackFn();
    }
    onClose();
  };

  // Close on Escape key
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const modules = [
    {
      id: 'radar',
      title: 'Ahead-of-the-Bit Hazard Radar',
      subtitle: 'Predictive Formation & Proximity Detection',
      category: 'realtime',
      categoryName: 'Real-Time Drilling',
      icon: Radar,
      accentColor: 'text-amber-400',
      borderColor: 'border-slate-800 hover:border-amber-500/60',
      bgColor: 'bg-slate-950/80 hover:bg-slate-900/90',
      activeGlow: 'hover:shadow-[0_0_25px_rgba(245,158,11,0.2)]',
      iconBg: 'bg-amber-500/15 border-amber-500/30 text-amber-400',
      badgeBg: 'bg-amber-500/15 text-amber-300 border-amber-500/30',
      btnStyle: 'bg-amber-500/20 hover:bg-amber-500/30 text-amber-200 border-amber-500/40 hover:border-amber-400',
      statusText: 'Real-Time Active',
      description: 'Scans 50m and 100m lookahead intervals ahead of the current bit position. Detects impending formation boundary transitions, historical offset hazard clusters, and calculates an automated 0–100% predictive risk index.',
      features: [
        '50m & 100m Lookahead Windows',
        'Formation Boundary Proximity Warnings',
        'Historical Offset Kick & Loss Clusters',
        'Predictive Hazard Risk Score (0-100%)'
      ],
      actionLabel: 'Open in New Tab (Full Screen)',
      onLaunch: () => launchModuleInNewTab('radar', onOpenRadar)
    },
    {
      id: 'correlation',
      title: 'Cross-Well Correlation & Stratigraphic Fence',
      subtitle: 'Dynamic Time Warping & Casing Schedule Programs',
      category: 'planning',
      categoryName: 'Offset & Planning',
      icon: Layers,
      accentColor: 'text-indigo-400',
      borderColor: 'border-slate-800 hover:border-indigo-500/60',
      bgColor: 'bg-slate-950/80 hover:bg-slate-900/90',
      activeGlow: 'hover:shadow-[0_0_25px_rgba(99,102,241,0.2)]',
      iconBg: 'bg-indigo-500/15 border-indigo-500/30 text-indigo-400',
      badgeBg: 'bg-indigo-500/15 text-indigo-300 border-indigo-500/30',
      btnStyle: 'bg-indigo-500/20 hover:bg-indigo-500/30 text-indigo-200 border-indigo-500/40 hover:border-indigo-400',
      statusText: 'Offset Logs Loaded',
      description: 'Executes non-linear Dynamic Time Warping (FastDTW) to correlate active gamma ray logs against nearby offset wells. Generates a 3-well stratigraphic fence diagram with regional lithology horizons and correlates casing/cementing schedules.',
      features: [
        'Dynamic Time Warping (FastDTW) Alignment',
        '3-Well Stratigraphic Fence Diagram',
        'Casing Shoe & Cement Top Schedule Correlator',
        'Leak-off Test (LOT) / EMW Cross-Well Comparison'
      ],
      actionLabel: 'Open in New Tab (Full Screen)',
      onLaunch: () => launchModuleInNewTab('correlation', onOpenCorrelation)
    },
    {
      id: 'ppfg',
      title: 'PPFG Safe Mud Weight Operating Window',
      subtitle: 'Eaton Pore Pressure & Fracture Breakdown Limit',
      category: 'realtime',
      categoryName: 'Real-Time Drilling',
      icon: Gauge,
      accentColor: 'text-emerald-400',
      borderColor: 'border-slate-800 hover:border-emerald-500/60',
      bgColor: 'bg-slate-950/80 hover:bg-slate-900/90',
      activeGlow: 'hover:shadow-[0_0_25px_rgba(16,185,129,0.2)]',
      iconBg: 'bg-emerald-500/15 border-emerald-500/30 text-emerald-400',
      badgeBg: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30',
      btnStyle: 'bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-200 border-emerald-500/40 hover:border-emerald-400',
      statusText: 'Safe Window Computed',
      description: 'Applies the Eaton (1972) acoustic/resistivity pore pressure model and Hubbert-Willis (1957) fracture gradient equations. Displays the safe drilling mud weight operating corridor with ±5% uncertainty margins, casing shoes, and live telemetry tracking.',
      features: [
        'Eaton (1972) Pore Pressure Curve',
        'Hubbert-Willis (1957) Fracture Gradient Limit',
        '±5% to 8% Regional Uncertainty Envelope',
        'Active Depth Mud Weight Telemetry Marker'
      ],
      actionLabel: 'Open in New Tab (Full Screen)',
      onLaunch: () => launchModuleInNewTab('ppfg', onOpenPPFG)
    },
    {
      id: 'dossier',
      title: '1-Click Pre-Spud Offset Hazard Dossier',
      subtitle: 'Automated 8-Section Comprehensive Engineering Packet',
      category: 'planning',
      categoryName: 'Offset & Planning',
      icon: FileText,
      accentColor: 'text-cyan-400',
      borderColor: 'border-slate-800 hover:border-cyan-500/60',
      bgColor: 'bg-slate-950/80 hover:bg-slate-900/90',
      activeGlow: 'hover:shadow-[0_0_25px_rgba(6,182,212,0.2)]',
      iconBg: 'bg-cyan-500/15 border-cyan-500/30 text-cyan-400',
      badgeBg: 'bg-cyan-500/15 text-cyan-300 border-cyan-500/30',
      btnStyle: 'bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-200 border-cyan-500/40 hover:border-cyan-400',
      statusText: 'Full Dossier Ready',
      description: 'Synthesizes complete pre-spud risk assessment across all offset wells within a 5.0 km radius. Includes geological setting, lithology prognosis, historical kick/loss/stuck incidents, 3D anti-collision clearance, and regulatory contingency plans.',
      features: [
        '8 Comprehensive Engineering Dossier Sections',
        'Offset Risk Clustering within 5.0 km Radius',
        '3D Anti-Collision & Proximity Clearance Scan',
        'Export to Production PDF / Print Ready Dossier'
      ],
      actionLabel: 'Open in New Tab (Full Screen)',
      onLaunch: () => launchModuleInNewTab('dossier', onOpenDossier)
    },
    {
      id: 'backtest',
      title: 'Time-Travel Causal Hazard Backtest',
      subtitle: 'Historical Run Replay & Real-Time Alert Lead Time Validation',
      category: 'realtime',
      categoryName: 'Real-Time Drilling',
      icon: History,
      accentColor: 'text-purple-400',
      borderColor: 'border-slate-800 hover:border-purple-500/60',
      bgColor: 'bg-slate-950/80 hover:bg-slate-900/90',
      activeGlow: 'hover:shadow-[0_0_25px_rgba(168,85,247,0.2)]',
      iconBg: 'bg-purple-500/15 border-purple-500/30 text-purple-400',
      badgeBg: 'bg-purple-500/15 text-purple-300 border-purple-500/30',
      btnStyle: 'bg-purple-500/20 hover:bg-purple-500/30 text-purple-200 border-purple-500/40 hover:border-purple-400',
      statusText: '3 Run Replays Ready',
      description: 'Replays historical drilling telemetry second-by-second leading up to known severe well kicks or stuck pipe events. Audits whether the system provided advance warning without hindsight bias and measures the exact warning lead time.',
      features: [
        'Second-by-Second Causal Telemetry Replay',
        'Advance Warning Lead-Time Validation (Minutes Ahead)',
        'False Alarm vs Missed Detection Ratio Audit',
        'Three Documented Regional Incident Runs'
      ],
      actionLabel: 'Open in New Tab (Full Screen)',
      onLaunch: () => launchModuleInNewTab('backtest', onOpenBacktest)
    },
    {
      id: 'contribute',
      title: 'Institutional Memory Feedback (+ Lesson)',
      subtitle: 'Two-Way Field Learning & Vector Knowledge Base Ingestion',
      category: 'memory',
      categoryName: 'Institutional Memory',
      icon: Brain,
      accentColor: 'text-rose-400',
      borderColor: 'border-slate-800 hover:border-rose-500/60',
      bgColor: 'bg-slate-950/80 hover:bg-slate-900/90',
      activeGlow: 'hover:shadow-[0_0_25px_rgba(244,63,94,0.2)]',
      iconBg: 'bg-rose-500/15 border-rose-500/30 text-rose-400',
      badgeBg: 'bg-rose-500/15 text-rose-300 border-rose-500/30',
      btnStyle: 'bg-rose-500/20 hover:bg-rose-500/30 text-rose-200 border-rose-500/40 hover:border-rose-400',
      statusText: 'Live RAG Ingestion',
      description: 'Allows field engineers and office reviewers to log lessons learned, root causes, NPT hours, and successful mitigations during active drilling. Directly embeds and commits lessons to the 384-dimensional vector knowledge base in real time.',
      features: [
        'Real-Time Institutional Memory Feedback Loop',
        '384-Dimensional Dense Vector Embedding',
        'Immediate Semantic Search Indexing in Same Session',
        'Rig Edge Offline Cache with Automatic Cloud Sync'
      ],
      actionLabel: 'Open in New Tab (Full Screen)',
      onLaunch: () => launchModuleInNewTab('contribute', onOpenContribute)
    }
  ];

  const filteredModules = selectedFilter === 'all' 
    ? modules 
    : modules.filter(m => m.category === selectedFilter);

  return (
    <div className="fixed inset-0 z-50 w-screen h-screen flex flex-col bg-slate-950 text-slate-100 overflow-hidden select-none animate-in fade-in duration-200">
      
      {/* Top Mission Control Header (Edge-to-Edge) */}
      <header className="flex items-center justify-between px-6 py-3.5 border-b border-slate-800/90 bg-slate-900/90 backdrop-blur-xl shrink-0 z-20">
        <div className="flex items-center space-x-3.5">
          <div className="p-2.5 rounded-xl bg-cyan-500/15 border border-cyan-500/30 shadow-[0_0_15px_rgba(6,182,212,0.25)]">
            <Layers size={22} className="text-cyan-400" />
          </div>
          <div>
            <div className="flex items-center space-x-2.5">
              <h1 className="text-base lg:text-lg font-bold text-white font-mono tracking-tight flex items-center gap-2">
                Drilling Decision Support & Engineering Modules
              </h1>
              <span className="px-2 py-0.5 rounded-full bg-cyan-500/20 text-cyan-300 text-[10px] font-mono font-semibold border border-cyan-500/30">
                6 Production Modules
              </span>
              <span className="hidden sm:inline-flex items-center space-x-1 px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-300 text-[10px] font-mono border border-emerald-500/30">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                <span>Active Rig Synchronized</span>
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Physics-based predictive hazard radar, cross-well correlation, geomechanics, pre-spud dossiers, and institutional memory
            </p>
          </div>
        </div>

        {/* Right Side: Context Pill + Close Button */}
        <div className="flex items-center space-x-3">
          {/* Active Well Context Pill */}
          <div className="hidden md:flex items-center space-x-2.5 px-3 py-1.5 rounded-xl bg-slate-950/80 border border-slate-800 text-xs font-mono">
            <span className="text-slate-400">Target Well:</span>
            <span className="text-cyan-300 font-bold bg-cyan-950/60 px-2 py-0.5 rounded border border-cyan-700/50">
              {activeWellId}
            </span>
            <span className="text-slate-600">•</span>
            <span className="text-slate-400">Current TVD:</span>
            <span className="text-emerald-400 font-bold">{currentDepth ? `${currentDepth.toFixed(1)}m` : '2,240.0m'}</span>
          </div>

          {/* Close Button with ESC label */}
          <button
            onClick={onClose}
            className="flex items-center space-x-2 px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-750 text-slate-300 hover:text-white border border-slate-700 hover:border-slate-500 text-xs font-semibold transition cursor-pointer shadow-sm group"
            title="Close Fullscreen Modules (Press Escape)"
          >
            <span>Close</span>
            <kbd className="hidden sm:inline-block px-1.5 py-0.5 text-[10px] font-mono bg-slate-900 border border-slate-700 rounded text-slate-400 group-hover:text-slate-200">
              ESC
            </kbd>
            <X size={16} className="text-slate-400 group-hover:text-white" />
          </button>
        </div>
      </header>

      {/* Sub-Header Toolbar: Filter Chips & View Mode */}
      <div className="flex flex-wrap items-center justify-between px-6 py-2.5 bg-slate-900/60 border-b border-slate-800/80 shrink-0 gap-3 z-10">
        {/* Filter Chips */}
        <div className="flex items-center space-x-2 overflow-x-auto py-0.5 scrollbar-none">
          <span className="flex items-center space-x-1 text-xs font-semibold text-slate-400 font-mono mr-1">
            <Filter size={13} />
            <span>Filter:</span>
          </span>
          <button
            onClick={() => setSelectedFilter('all')}
            className={`px-3 py-1 rounded-lg text-xs font-semibold font-mono transition border cursor-pointer whitespace-nowrap ${
              selectedFilter === 'all'
                ? 'bg-cyan-500/20 text-cyan-200 border-cyan-400 shadow-[0_0_12px_rgba(6,182,212,0.3)]'
                : 'bg-slate-900 text-slate-400 border-slate-800 hover:text-slate-200 hover:bg-slate-850'
            }`}
          >
            All Modules (6)
          </button>
          <button
            onClick={() => setSelectedFilter('realtime')}
            className={`px-3 py-1 rounded-lg text-xs font-semibold font-mono transition border cursor-pointer whitespace-nowrap ${
              selectedFilter === 'realtime'
                ? 'bg-amber-500/20 text-amber-200 border-amber-400 shadow-[0_0_12px_rgba(245,158,11,0.3)]'
                : 'bg-slate-900 text-slate-400 border-slate-800 hover:text-slate-200 hover:bg-slate-850'
            }`}
          >
            Real-Time Drilling (3)
          </button>
          <button
            onClick={() => setSelectedFilter('planning')}
            className={`px-3 py-1 rounded-lg text-xs font-semibold font-mono transition border cursor-pointer whitespace-nowrap ${
              selectedFilter === 'planning'
                ? 'bg-indigo-500/20 text-indigo-200 border-indigo-400 shadow-[0_0_12px_rgba(99,102,241,0.3)]'
                : 'bg-slate-900 text-slate-400 border-slate-800 hover:text-slate-200 hover:bg-slate-850'
            }`}
          >
            Offset & Planning (2)
          </button>
          <button
            onClick={() => setSelectedFilter('memory')}
            className={`px-3 py-1 rounded-lg text-xs font-semibold font-mono transition border cursor-pointer whitespace-nowrap ${
              selectedFilter === 'memory'
                ? 'bg-rose-500/20 text-rose-200 border-rose-400 shadow-[0_0_12px_rgba(244,63,94,0.3)]'
                : 'bg-slate-900 text-slate-400 border-slate-800 hover:text-slate-200 hover:bg-slate-850'
            }`}
          >
            Institutional Memory (1)
          </button>
        </div>

        {/* View Toggle (Grid / List) */}
        <div className="flex items-center space-x-1 bg-slate-950/80 p-1 rounded-lg border border-slate-800">
          <button
            onClick={() => setViewMode('grid')}
            className={`p-1.5 rounded-md text-xs transition cursor-pointer flex items-center space-x-1 ${
              viewMode === 'grid' 
                ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40' 
                : 'text-slate-400 hover:text-slate-200'
            }`}
            title="Card Grid View"
          >
            <LayoutGrid size={14} />
            <span className="text-[11px] font-mono hidden sm:inline">Grid</span>
          </button>
          <button
            onClick={() => setViewMode('list')}
            className={`p-1.5 rounded-md text-xs transition cursor-pointer flex items-center space-x-1 ${
              viewMode === 'list' 
                ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40' 
                : 'text-slate-400 hover:text-slate-200'
            }`}
            title="Detailed List View"
          >
            <ListFilter size={14} />
            <span className="text-[11px] font-mono hidden sm:inline">List</span>
          </button>
        </div>
      </div>

      {/* Main Fullscreen Body Container (Expansive & Responsive) */}
      <main className="flex-1 overflow-y-auto p-6 bg-slate-950/95 scrollbar-thin scrollbar-thumb-slate-800">
        
        {viewMode === 'grid' ? (
          /* High-Impact 3-Column / 2-Column Responsive Card Grid that fills full screen */
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5 max-w-[1800px] mx-auto">
            {filteredModules.map((m) => {
              const Icon = m.icon;
              return (
                <div
                  key={m.id}
                  onClick={m.onLaunch}
                  className={`flex flex-col justify-between p-5 rounded-2xl border transition-all duration-300 cursor-pointer group shadow-lg ${m.bgColor} ${m.borderColor} ${m.activeGlow}`}
                >
                  {/* Top: Icon + Badge + Title */}
                  <div>
                    <div className="flex items-center justify-between mb-3.5">
                      <div className={`p-3 rounded-xl border group-hover:scale-110 transition-transform shadow-inner ${m.iconBg}`}>
                        <Icon size={24} />
                      </div>
                      <div className="flex items-center space-x-1.5">
                        <span className="text-[10px] font-mono text-slate-500 uppercase tracking-wider">
                          {m.categoryName}
                        </span>
                        <span className={`px-2 py-0.5 rounded-full text-[10px] font-mono font-bold border ${m.badgeBg}`}>
                          {m.statusText}
                        </span>
                        <span className="hidden sm:inline-flex items-center space-x-1 px-2 py-0.5 rounded-full text-[10px] font-mono bg-cyan-950/60 border border-cyan-800/60 text-cyan-300">
                          <ExternalLink size={10} />
                          <span>New Tab</span>
                        </span>
                      </div>
                    </div>

                    <h2 className="text-base font-bold text-white group-hover:text-cyan-200 transition font-mono tracking-tight mb-1">
                      {m.title}
                    </h2>

                    <div className="text-xs font-semibold text-slate-400 font-mono mb-3">
                      {m.subtitle}
                    </div>

                    <p className="text-xs text-slate-300 leading-relaxed line-clamp-3 group-hover:text-slate-200 mb-4">
                      {m.description}
                    </p>

                    {/* Features list */}
                    <div className="space-y-1.5 mb-5 border-t border-slate-800/80 pt-3">
                      {m.features.map((feat, idx) => (
                        <div key={idx} className="flex items-center space-x-2 text-xs text-slate-300">
                          <CheckCircle2 size={13} className="text-emerald-400 shrink-0" />
                          <span className="truncate">{feat}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Bottom Launch Button */}
                  <div className="pt-2 border-t border-slate-800/80">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        m.onLaunch();
                      }}
                      className={`w-full py-2.5 px-4 rounded-xl text-xs font-bold transition flex items-center justify-center space-x-2 border shadow-sm cursor-pointer ${m.btnStyle}`}
                    >
                      <ExternalLink size={14} className="shrink-0" />
                      <span>{m.actionLabel}</span>
                      <ChevronRight size={15} className="group-hover:translate-x-1.5 transition-transform" />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          /* Expanded Full-Width Rows List View */
          <div className="space-y-4 max-w-[1800px] mx-auto">
            {filteredModules.map((m) => {
              const Icon = m.icon;
              return (
                <div
                  key={m.id}
                  onClick={m.onLaunch}
                  className={`p-5 rounded-2xl border transition-all duration-200 cursor-pointer group shadow-md hover:shadow-2xl flex flex-col lg:flex-row items-start lg:items-center justify-between gap-5 ${m.bgColor} ${m.borderColor} ${m.activeGlow}`}
                >
                  <div className="flex items-start space-x-4 flex-1 min-w-0">
                    <div className={`p-3.5 rounded-xl border shrink-0 group-hover:scale-105 transition-transform ${m.iconBg}`}>
                      <Icon size={26} />
                    </div>

                    <div className="flex-1 min-w-0">
                      <div className="flex flex-wrap items-center gap-2.5 mb-1.5">
                        <h2 className="text-base font-bold text-white group-hover:text-cyan-200 transition font-mono tracking-tight">
                          {m.title}
                        </h2>
                        <span className={`px-2 py-0.5 rounded-full text-[10px] font-mono font-bold border ${m.badgeBg}`}>
                          {m.statusText}
                        </span>
                        <span className="hidden sm:inline-flex items-center space-x-1 px-2 py-0.5 rounded-full text-[10px] font-mono bg-cyan-950/60 border border-cyan-800/60 text-cyan-300">
                          <ExternalLink size={10} />
                          <span>New Tab</span>
                        </span>
                        <span className="text-[10px] font-mono text-slate-500 uppercase">
                          • {m.categoryName}
                        </span>
                      </div>

                      <div className="text-xs font-semibold text-slate-400 font-mono mb-2">
                        {m.subtitle}
                      </div>

                      <p className="text-xs text-slate-300 leading-relaxed mb-3 max-w-4xl">
                        {m.description}
                      </p>

                      <div className="flex flex-wrap gap-2">
                        {m.features.map((feat, idx) => (
                          <span
                            key={idx}
                            className="px-2.5 py-0.5 rounded-md bg-slate-900 border border-slate-800 text-[11px] text-slate-300 font-mono flex items-center space-x-1"
                          >
                            <span className="text-emerald-400">✓</span>
                            <span>{feat}</span>
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>

                  <div className="shrink-0 w-full lg:w-auto flex justify-end pt-3 lg:pt-0 border-t lg:border-t-0 border-slate-800">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        m.onLaunch();
                      }}
                      className={`w-full lg:w-auto px-5 py-2.5 rounded-xl text-xs font-bold transition flex items-center justify-center space-x-2 border shadow-sm cursor-pointer whitespace-nowrap ${m.btnStyle}`}
                    >
                      <ExternalLink size={14} className="shrink-0" />
                      <span>{m.actionLabel}</span>
                      <ChevronRight size={15} className="group-hover:translate-x-1.5 transition-transform" />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}

      </main>

      {/* Bottom Fullscreen Status Bar */}
      <footer className="px-6 py-2.5 border-t border-slate-800/90 bg-slate-950 shrink-0 flex flex-wrap items-center justify-between text-xs text-slate-400 z-20">
        <div className="flex items-center space-x-3">
          <span className={`w-2 h-2 rounded-full ${isBackendConnected ? 'bg-emerald-400' : 'bg-cyan-400'} animate-pulse`} />
          <span className="font-mono">
            Platform Engine: <span className="text-white font-semibold">{isBackendConnected ? 'FastAPI Cloud Synchronized' : 'Rig Edge Autonomous Engine (100% Offline Ready)'}</span>
          </span>
          <span className="text-slate-600 hidden sm:inline">•</span>
          <span className="font-mono hidden sm:inline">
            Active Formation: <span className="text-cyan-300">Barail Arenaceous / Tipam Sandstone</span>
          </span>
        </div>

        <div className="flex items-center space-x-3">
          <span className="text-slate-500 font-mono text-[11px] hidden md:inline">
            Click any module card to launch immediately
          </span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-750 text-slate-300 hover:text-white border border-slate-700 text-xs font-semibold transition cursor-pointer"
          >
            Return to Telemetry Cockpit
          </button>
        </div>
      </footer>

    </div>
  );
}
