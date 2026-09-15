import React, { useState } from 'react';
import { Clock, MapPin, BrainCircuit, ChevronDown, ChevronUp, Sparkles, TrendingUp } from 'lucide-react';

const ImpactStatCards = ({ className = "" }) => {
  const [isExpanded, setIsExpanded] = useState(true);

  const stats = [
    {
      id: 'pre-spud',
      icon: Clock,
      iconColor: 'text-cyan-400',
      borderColor: 'border-cyan-500/30',
      label: 'Pre-Spud Risk Compilation',
      before: '~2-3 days (manual)',
      after: '<1 minute (automated)',
      gain: '99.8% Faster',
      accentColor: 'text-cyan-300'
    },
    {
      id: 'offset-search',
      icon: MapPin,
      iconColor: 'text-emerald-400',
      borderColor: 'border-emerald-500/30',
      label: 'Offset Well Search Radius',
      before: 'Manual archive lookup',
      after: 'Instant PostGIS spatial query',
      gain: 'Real-Time Spatial',
      accentColor: 'text-emerald-300'
    },
    {
      id: 'knowledge-retrieval',
      icon: BrainCircuit,
      iconColor: 'text-purple-400',
      borderColor: 'border-purple-500/30',
      label: 'Institutional Knowledge Retrieval',
      before: 'Individual engineer memory',
      after: 'Semantic search across all events',
      gain: 'Zero Memory Loss',
      accentColor: 'text-purple-300'
    }
  ];

  return (
    <div className={`w-full bg-[#080e1b]/95 border-b border-slate-800/80 px-3 sm:px-4 lg:px-5 py-1 shrink-0 transition-all ${className}`}>
      <div className="flex items-center justify-between gap-2">
        
        {/* Title Tag */}
        <div className="flex items-center space-x-2 shrink-0">
          <div className="flex items-center space-x-1.5 px-2 py-0.5 rounded-md bg-cyan-950/60 border border-cyan-500/30 text-cyan-300 text-[10px] font-mono font-bold tracking-wider uppercase">
            <Sparkles size={11} className="text-cyan-400" />
            <span>Platform Impact</span>
          </div>
          <span className="text-[10px] font-mono text-slate-500 hidden md:inline">
            Estimated operational efficiency gains
          </span>
        </div>

        {/* Toggle on small screens */}
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="lg:hidden p-1 rounded text-slate-400 hover:text-white transition flex items-center gap-1 text-[11px]"
        >
          <span>{isExpanded ? 'Hide' : 'Show'} Impact</span>
          {isExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
        </button>

        {/* 3 Compact Stat Cards */}
        {isExpanded && (
          <div className="flex flex-1 items-center justify-end gap-2 overflow-x-auto custom-scrollbar py-0.5 max-w-full">
            {stats.map((item) => {
              const Icon = item.icon;
              return (
                <div 
                  key={item.id}
                  className={`glass-panel p-1.5 px-2.5 rounded-lg border ${item.borderColor} bg-slate-900/90 shadow-glass flex items-center space-x-2 min-w-[210px] xl:min-w-[245px] shrink-0 relative overflow-hidden group hover:border-slate-600 transition`}
                >
                  <div className="p-1 rounded-md bg-slate-950/80 border border-slate-800 text-slate-300 shrink-0">
                    <Icon size={13} className={item.iconColor} />
                  </div>
                  
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center justify-between gap-1 leading-none mb-0.5">
                      <span className="text-[10px] font-mono font-bold uppercase text-slate-300 tracking-wider truncate">
                        {item.label}
                      </span>
                      <span className="text-[9px] font-mono px-1 py-0.2 rounded bg-slate-800/80 text-slate-400 border border-slate-700/60 shrink-0">
                        (estimated)
                      </span>
                    </div>

                    <div className="text-[10.5px] font-mono flex items-center gap-1 truncate">
                      <span className={`font-semibold ${item.accentColor} truncate`}>
                        {item.after}
                      </span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}

      </div>
    </div>
  );
};

export default ImpactStatCards;
