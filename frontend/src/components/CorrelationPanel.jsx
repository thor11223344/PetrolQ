import React, { useState, useEffect } from 'react';
import axios from 'axios';
import Plot from 'react-plotly.js';
import { X, Loader2, Link2 } from 'lucide-react';

const CorrelationPanel = ({ isOpen, onClose, activeWell, offsetWell }) => {
    const [data, setData] = useState(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState(null);

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

    // Build Plotly Traces
    const traces = [];
    
    if (data) {
        // Shift offset well GR on the X-axis by +200 API for side-by-side visualization
        const offsetShift = 200;
        
        // 1. Active Well Trace
        traces.push({
            x: data.active_gr,
            y: data.active_depths,
            name: activeWell,
            type: 'scatter',
            mode: 'lines',
            line: { color: '#06B6D4', width: 2 }
        });
        
        // 2. Offset Well Trace
        traces.push({
            x: data.offset_gr.map(gr => gr + offsetShift),
            y: data.offset_depths,
            name: offsetWell,
            type: 'scatter',
            mode: 'lines',
            line: { color: '#F59E0B', width: 2 }
        });

        // 3. Correlation Lines (Subsample DTW mapping to avoid cluttered plot, e.g., every 25th point)
        const mappingX = [];
        const mappingY = [];
        
        for (let i = 0; i < data.mapping.length; i += 25) {
            const [activeIdx, offsetIdx] = data.mapping[i];
            const ax = data.active_gr[activeIdx];
            const ay = data.active_depths[activeIdx];
            
            const ox = data.offset_gr[offsetIdx] + offsetShift;
            const oy = data.offset_depths[offsetIdx];
            
            // Draw a line segment
            mappingX.push(ax, ox, null);
            mappingY.push(ay, oy, null);
        }
        
        traces.push({
            x: mappingX,
            y: mappingY,
            name: 'DTW Mapping',
            type: 'scatter',
            mode: 'lines',
            line: { color: 'rgba(148, 163, 184, 0.4)', width: 1, dash: 'dot' },
            hoverinfo: 'none',
            showlegend: true
        });
    }

    return (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/80 backdrop-blur-sm animate-in fade-in">
            <div className="bg-slate-900 border border-slate-700 w-[70vw] h-[85vh] rounded-xl shadow-2xl flex flex-col overflow-hidden animate-in zoom-in-95">
                <div className="flex justify-between items-center p-4 border-b border-slate-800 bg-slate-900/50">
                    <div className="flex items-center space-x-2 text-slate-200">
                        <Link2 size={18} className="text-status-fluid" />
                        <h2 className="text-lg font-semibold tracking-wide">Cross-Well Stratigraphic Correlation</h2>
                    </div>
                    <button onClick={onClose} className="text-slate-500 hover:text-white transition-colors">
                        <X size={24} />
                    </button>
                </div>
                
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
                                layout={{
                                    autosize: true,
                                    margin: { l: 60, r: 40, b: 40, t: 40 },
                                    paper_bgcolor: 'transparent',
                                    plot_bgcolor: 'transparent',
                                    title: {
                                        text: `Gamma Ray (API) Correlation: ${activeWell} vs ${offsetWell}`,
                                        font: { color: '#94a3b8', size: 14 }
                                    },
                                    xaxis: { 
                                        title: 'Gamma Ray (API)', 
                                        gridcolor: '#334155', 
                                        zerolinecolor: '#334155', 
                                        color: '#94a3b8',
                                        showticklabels: false
                                    },
                                    yaxis: { 
                                        title: 'Depth TVD (m)', 
                                        autorange: 'reversed', 
                                        gridcolor: '#334155', 
                                        zerolinecolor: '#334155', 
                                        color: '#94a3b8' 
                                    },
                                    legend: { font: { color: '#cbd5e1' }, bgcolor: 'rgba(0,0,0,0.5)', x: 0.8, y: 1 }
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
