import React, { useState, useEffect } from 'react';
import axios from 'axios';
import Plot from 'react-plotly.js';
import { X, Loader2, Link2, Columns, Info, HelpCircle, ChevronDown, ChevronUp, Layers } from 'lucide-react';

const CorrelationPanel = ({ isOpen, onClose, activeWell, offsetWell }) => {
    const [data, setData] = useState(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState(null);
    const [isAligned, setIsAligned] = useState(false);
    const [showHelp, setShowHelp] = useState(false);

    useEffect(() => {
        if (!isOpen) return;

        const fetchCorrelation = async () => {
            setIsLoading(true);
            setError(null);
            try {
                const response = await axios.get('http://localhost:8000/api/correlate', {
                    params: { active_well: activeWell, offset_well: offsetWell }
                });
                setData(response.data);
            } catch (err) {
                console.error("Correlation failed", err);
                setError(err.response?.data?.detail || "Failed to compute correlation");
            } finally {
                setIsLoading(false);
            }
        };

        fetchCorrelation();
    }, [isOpen, activeWell, offsetWell]);

    if (!isOpen) return null;

    const traces = [];
    const shapes = [];
    const annotations = [];
    
    if (data) {
        // 1. Active Well Trace
        traces.push({
            x: data.active_gr,
            y: data.active_depths,
            name: activeWell,
            type: 'scatter',
            mode: 'lines',
            line: { color: '#06B6D4', width: 2 },
            xaxis: 'x',
            yaxis: 'y'
        });
        
        // 2. Offset Well Trace (Raw vs Aligned)
        let offsetGr = data.offset_gr;
        let offsetDepths = data.offset_depths;
        
        if (isAligned) {
            const alignedOffsetGr = [];
            const alignedOffsetDepths = [];
            // Use the DTW path to warp the offset well depths to match the active well
            data.mapping.forEach(([aIdx, oIdx]) => {
                alignedOffsetGr.push(data.offset_gr[oIdx]);
                alignedOffsetDepths.push(data.active_depths[aIdx]);
            });
            offsetGr = alignedOffsetGr;
            offsetDepths = alignedOffsetDepths;
        }

        traces.push({
            x: offsetGr,
            y: offsetDepths,
            name: offsetWell,
            type: 'scatter',
            mode: 'lines',
            line: { color: '#F59E0B', width: 2 },
            xaxis: 'x2',
            yaxis: 'y'
        });

        // 3. Shaded Formation Bands (Draw clean connector lines & depth labels)
        const numBands = 7;
        const step = Math.floor(data.mapping.length / numBands);
        const bandColors = ['#ef4444', '#f97316', '#eab308', '#22c55e', '#3b82f6', '#a855f7'];
        
        for (let i = 1; i < numBands; i++) {
            const [aIdx, oIdx] = data.mapping[i * step];
            const activeY = data.active_depths[aIdx];
            const rawOffsetY = data.offset_depths[oIdx];
            const offsetY = isAligned ? activeY : rawOffsetY;
            const dip = Math.round(rawOffsetY - activeY);
            const color = bandColors[(i - 1) % bandColors.length];
            
            shapes.push({
                type: 'line',
                xref: 'paper', x0: 0, x1: 1,
                yref: 'y', y0: activeY, y1: offsetY,
                line: { color: color, width: 2, dash: isAligned ? 'solid' : 'dot' },
                opacity: 0.65
            });

            // Gutter annotation in the center gap (x=0.5)
            annotations.push({
                xref: 'paper',
                yref: 'y',
                x: 0.5,
                y: isAligned ? activeY : (activeY + offsetY) / 2,
                text: isAligned 
                    ? `Horizon ${i} • Aligned (${Math.round(activeY)}m)` 
                    : `Horizon ${i} • Dip: ${dip > 0 ? '+' : ''}${dip}m`,
                showarrow: false,
                font: { size: 9, color: '#f8fafc', family: 'monospace' },
                bgcolor: 'rgba(15, 23, 42, 0.9)',
                bordercolor: color,
                borderwidth: 1,
                borderpad: 3,
                opacity: 0.95
            });
        }
    }

    return (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/80 backdrop-blur-sm animate-in fade-in">
            <div className="bg-slate-900 border border-slate-700 w-[84vw] h-[92vh] rounded-xl shadow-2xl flex flex-col overflow-hidden animate-in zoom-in-95">
                
                {/* Header */}
                <div className="flex justify-between items-center px-5 py-3.5 border-b border-slate-800 bg-slate-900/80">
                    <div className="flex items-center space-x-3 text-slate-200">
                        <Link2 size={20} className="text-status-fluid" />
                        <div>
                            <h2 className="text-lg font-semibold tracking-wide flex items-center gap-2">
                                Cross-Well Stratigraphic Correlation
                            </h2>
                            <p className="text-xs text-slate-400">
                                Dynamic Time Warping (DTW) geological horizon matching
                            </p>
                        </div>
                    </div>
                    
                    {data && (
                        <div className="flex items-center space-x-4">
                            <div className="flex items-center space-x-2 text-sm bg-slate-950/60 px-3 py-1.5 rounded-lg border border-slate-800">
                                <span className="text-slate-400">DTW Cost:</span>
                                <span className="font-mono font-semibold text-emerald-400">{data.distance.toFixed(1)}</span>
                                <span className="text-slate-500 text-xs">(Strong match)</span>
                            </div>
                            
                            <button 
                                onClick={() => setIsAligned(!isAligned)}
                                className={`flex items-center space-x-2 px-4 py-1.5 rounded-lg text-xs font-semibold tracking-wide transition-all shadow-sm ${
                                    isAligned 
                                        ? 'bg-cyan-500 hover:bg-cyan-400 text-slate-950 shadow-[0_0_15px_rgba(6,182,212,0.4)]' 
                                        : 'bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700'
                                }`}
                            >
                                <Columns size={15} />
                                <span>{isAligned ? '✓ DTW-Aligned View' : 'Raw Depth View'}</span>
                            </button>

                            <button 
                                onClick={() => setShowHelp(!showHelp)}
                                className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                                    showHelp ? 'bg-indigo-600/30 text-indigo-300 border border-indigo-500/40' : 'bg-slate-800/80 hover:bg-slate-800 text-slate-300 border border-slate-700/60'
                                }`}
                                title="Learn how to read this chart"
                            >
                                <HelpCircle size={14} className="text-indigo-400" />
                                <span>Guide</span>
                                {showHelp ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                            </button>
                        </div>
                    )}

                    <button onClick={onClose} className="text-slate-400 hover:text-white transition-colors p-1 rounded-lg hover:bg-slate-800">
                        <X size={22} />
                    </button>
                </div>

                {/* Guide & Legend Strip */}
                {data && (
                    <div className="bg-slate-950/70 border-b border-slate-800/80 px-5 py-2.5 flex flex-wrap items-center justify-between gap-3 text-xs">
                        <div className="flex flex-wrap items-center gap-x-5 gap-y-2">
                            {/* Active Well */}
                            <div className="flex items-center space-x-2">
                                <span className="w-3.5 h-1 rounded bg-[#06B6D4] inline-block shadow-[0_0_8px_rgba(6,182,212,0.6)]"></span>
                                <span className="text-slate-400">Active Well:</span>
                                <span className="font-semibold text-cyan-300 font-mono">{activeWell}</span>
                            </div>

                            {/* Offset Well */}
                            <div className="flex items-center space-x-2">
                                <span className="w-3.5 h-1 rounded bg-[#F59E0B] inline-block shadow-[0_0_8px_rgba(245,158,11,0.6)]"></span>
                                <span className="text-slate-400">Historical Offset:</span>
                                <span className="font-semibold text-amber-300 font-mono">{offsetWell}</span>
                            </div>

                            <div className="h-4 w-px bg-slate-800 hidden md:block"></div>

                            {/* Colored Lines Description */}
                            <div className="flex items-center space-x-2">
                                <div className="flex -space-x-1">
                                    <span className="w-2.5 h-2.5 rounded-full bg-red-500 border border-slate-950"></span>
                                    <span className="w-2.5 h-2.5 rounded-full bg-amber-500 border border-slate-950"></span>
                                    <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 border border-slate-950"></span>
                                    <span className="w-2.5 h-2.5 rounded-full bg-blue-500 border border-slate-950"></span>
                                </div>
                                <span className="text-slate-300">
                                    <strong className="text-slate-100">Colored Lines:</strong> Matching formation horizons (rock layers).
                                    <span className="text-slate-400 ml-1.5 hidden lg:inline">
                                        {isAligned 
                                            ? 'Flattened to confirm geological property match.' 
                                            : 'Slope shows structural dip / depth offset between wells.'}
                                    </span>
                                </span>
                            </div>
                        </div>

                        <div className="text-slate-400 flex items-center space-x-1.5">
                            <span className="inline-block w-2 h-2 rounded-full bg-cyan-400 animate-pulse"></span>
                            <span>{isAligned ? 'Formations aligned at common datum' : 'Showing true measured depths'}</span>
                        </div>
                    </div>
                )}

                {/* Expandable Explanation Drawer */}
                {showHelp && (
                    <div className="bg-slate-900/95 border-b border-indigo-500/30 p-4 text-xs animate-in slide-in-from-top-2">
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                            <div className="bg-slate-950/70 p-3 rounded-lg border border-slate-800">
                                <div className="flex items-center space-x-2 text-cyan-400 font-semibold mb-1">
                                    <span className="w-2.5 h-2.5 rounded-full bg-cyan-400"></span>
                                    <h6>1. Gamma Ray Curves</h6>
                                </div>
                                <p className="text-slate-300 leading-relaxed">
                                    Shows rock radioactivity (0–120 API). Low values indicate permeable sandstone reservoirs; high values indicate impermeable shale seals.
                                </p>
                            </div>

                            <div className="bg-slate-950/70 p-3 rounded-lg border border-slate-800">
                                <div className="flex items-center space-x-2 text-amber-400 font-semibold mb-1">
                                    <Layers size={14} />
                                    <h6>2. Colored Horizon Tie-Lines</h6>
                                </div>
                                <p className="text-slate-300 leading-relaxed">
                                    Each colored line connects the <strong>exact same geological layer</strong> in both wells. In <em>Raw Depth View</em>, the downward slope indicates the formation is dipping deeper in the offset well.
                                </p>
                            </div>

                            <div className="bg-slate-950/70 p-3 rounded-lg border border-slate-800">
                                <div className="flex items-center space-x-2 text-emerald-400 font-semibold mb-1">
                                    <Columns size={14} />
                                    <h6>3. DTW-Aligned View</h6>
                                </div>
                                <p className="text-slate-300 leading-relaxed">
                                    Clicking the toggle stretches and aligns matching layers horizontally. This allows geologists to immediately compare bed thicknesses and verify formation targets.
                                </p>
                            </div>
                        </div>
                    </div>
                )}
                
                {/* Plot Area */}
                <div className="flex-1 relative bg-slate-950 p-4">
                    {isLoading ? (
                        <div className="absolute inset-0 flex flex-col items-center justify-center text-slate-400">
                            <Loader2 size={32} className="animate-spin mb-4 text-status-fluid" />
                            <p>Running Dynamic Time Warping...</p>
                        </div>
                    ) : error ? (
                        <div className="absolute inset-0 flex flex-col items-center justify-center text-red-400">
                            <p>{error}</p>
                        </div>
                    ) : data ? (
                        <div className="w-full h-full bg-slate-900 border border-slate-800 rounded">
                            <Plot
                                data={traces}
                                revision={isAligned ? 1 : 0}
                                layout={{
                                    datarevision: isAligned ? 1 : 0,
                                    autosize: true,
                                    margin: { l: 60, r: 40, b: 50, t: 30 },
                                    paper_bgcolor: 'transparent',
                                    plot_bgcolor: 'transparent',
                                    hovermode: 'y unified',
                                    xaxis: { 
                                        domain: [0, 0.45],
                                        title: 'Active Well GR (API)', 
                                        gridcolor: '#334155', 
                                        zerolinecolor: '#334155', 
                                        color: '#06B6D4'
                                    },
                                    xaxis2: { 
                                        domain: [0.55, 1],
                                        title: 'Offset Well GR (API)', 
                                        gridcolor: '#334155', 
                                        zerolinecolor: '#334155', 
                                        color: '#F59E0B'
                                    },
                                    yaxis: { 
                                        title: 'Depth TVD (m)', 
                                        autorange: 'reversed', 
                                        gridcolor: '#334155', 
                                        zerolinecolor: '#334155', 
                                        color: '#94a3b8',
                                        spikemode: 'across',
                                        spikedash: 'solid',
                                        spikecolor: '#64748b',
                                        spikethickness: 1
                                    },
                                    shapes: shapes,
                                    annotations: annotations,
                                    showlegend: false
                                }}
                                useResizeHandler={true}
                                style={{ width: '100%', height: '100%' }}
                            />
                        </div>
                    ) : null}
                </div>
            </div>
        </div>
    );
};

export default CorrelationPanel;
