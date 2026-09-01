import React, { useState } from 'react';
import { 
  Activity, 
  Map as MapIcon, 
  Settings, 
  Bell, 
  ChevronDown, 
  Layers,
  Database
} from 'lucide-react';

import WellMap from './components/WellMap';

function App() {
  const [selectedWell, setSelectedWell] = useState('OIL-BAGHJAN-1');

  return (
    <div className="h-screen w-screen flex flex-col bg-slate-950 text-slate-200 overflow-hidden">
      
      {/* Top Navigation Bar */}
      <header className="h-14 border-b border-slate-800 bg-slate-900 flex items-center justify-between px-6 z-10 shrink-0 shadow-md">
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
        <div className="flex-1 bg-slate-900 relative overflow-hidden">
          <WellMap 
             activeWellId={selectedWell} 
             onSelectWell={setSelectedWell} 
          />
        </div>

        {/* Right-Hand Drawer */}
        <aside className="w-96 border-l border-slate-800 bg-slate-950 flex flex-col shadow-2xl z-10 shrink-0 relative">
          <div className="p-4 border-b border-slate-800 flex items-center justify-between">
            <h2 className="font-medium text-slate-200">Well Intelligence</h2>
            <div className="flex space-x-1">
              <div className="w-2 h-2 rounded-full bg-status-danger mt-1"></div>
              <div className="w-2 h-2 rounded-full bg-status-warning mt-1"></div>
            </div>
          </div>
          
          <div className="flex-1 p-4 overflow-y-auto custom-scrollbar">
            {/* Context Widget Placeholder */}
            <div className="bg-slate-900 border border-slate-800 rounded p-4 mb-4">
              <h3 className="text-xs uppercase font-bold text-slate-500 mb-3">Target Trajectory</h3>
              <div className="h-32 flex items-center justify-center border border-slate-800 border-dashed rounded text-slate-600 text-sm">
                Plotly.js Canvas
              </div>
            </div>

            {/* Event Log Placeholder */}
            <div className="bg-slate-900 border border-slate-800 rounded p-4">
              <h3 className="text-xs uppercase font-bold text-slate-500 mb-3">Recent Offset Events</h3>
              <div className="space-y-3">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="flex items-start space-x-3 p-3 bg-slate-950/50 rounded border border-slate-800/50">
                    <div className={`w-1.5 h-1.5 rounded-full mt-1.5 shrink-0 ${i === 1 ? 'bg-status-danger' : 'bg-status-warning'}`}></div>
                    <div>
                      <p className="text-sm font-medium text-slate-300">Severe Lost Circulation</p>
                      <p className="text-xs text-slate-500 mt-1">Depth: 2,450m TVD</p>
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
