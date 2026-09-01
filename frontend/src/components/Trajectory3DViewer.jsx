import React, { useState, useEffect } from 'react';
import axios from 'axios';
import Plot from 'react-plotly.js';
import { X, Loader2 } from 'lucide-react';

const Trajectory3DViewer = ({ isOpen, onClose, activeWellId, offsetWells = [] }) => {
    const [plotData, setPlotData] = useState([]);
    const [isLoading, setIsLoading] = useState(false);

    useEffect(() => {
        if (!isOpen) return;

        const fetchTrajectories = async () => {
            setIsLoading(true);
            try {
                const traces = [];
                
                // Fetch Active Well
                try {
                    const activeRes = await axios.get(`http://localhost:8000/api/wells/${activeWellId}/trajectory`);
                    const activeData = activeRes.data.trajectory;
                    traces.push({
                        type: 'scatter3d',
                        mode: 'lines',
                        name: `Active: ${activeWellId}`,
                        x: activeData.x,
                        y: activeData.y,
                        z: activeData.z,
                        line: { width: 8, color: '#06B6D4' }
                    });
                } catch(e) {
                    console.error("Failed to load active well trajectory", e);
                }

                // Fetch Offset Wells
                for (const w of offsetWells) {
                    if (w.well_id === activeWellId) continue;
                    try {
                        const offsetRes = await axios.get(`http://localhost:8000/api/wells/${w.well_id}/trajectory`);
                        const offsetData = offsetRes.data.trajectory;
                        traces.push({
                            type: 'scatter3d',
                            mode: 'lines',
                            name: `Offset: ${w.well_id}`,
                            x: offsetData.x,
                            y: offsetData.y,
                            z: offsetData.z,
                            line: { width: 3, color: '#64748B' },
                            opacity: 0.7
                        });
                    } catch(e) {}
                }
                
                setPlotData(traces);
            } catch (error) {
                console.error("Failed to load trajectories", error);
            } finally {
                setIsLoading(false);
            }
        };

        fetchTrajectories();
    }, [isOpen, activeWellId, offsetWells]);

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/80 backdrop-blur-sm animate-in fade-in">
            <div className="bg-slate-900 border border-slate-700 w-[90vw] h-[90vh] rounded-xl shadow-2xl flex flex-col overflow-hidden animate-in zoom-in-95">
                <div className="flex justify-between items-center p-4 border-b border-slate-800 bg-slate-900/50">
                    <h2 className="text-lg font-semibold text-slate-200">3D Subsurface Trajectory View</h2>
                    <button onClick={onClose} className="text-slate-500 hover:text-white transition-colors">
                        <X size={24} />
                    </button>
                </div>
                <div className="flex-1 relative bg-slate-950">
                    {isLoading ? (
                        <div className="absolute inset-0 flex flex-col items-center justify-center text-slate-400">
                            <Loader2 size={32} className="animate-spin mb-4 text-status-fluid" />
                            <p>Loading 3D Meshes...</p>
                        </div>
                    ) : (
                        <Plot
                            data={plotData}
                            layout={{
                                autosize: true,
                                margin: { l: 0, r: 0, b: 0, t: 0 },
                                paper_bgcolor: 'transparent',
                                plot_bgcolor: 'transparent',
                                scene: {
                                    xaxis: { title: 'East (m)', gridcolor: '#334155', zerolinecolor: '#475569', color: '#94a3b8' },
                                    yaxis: { title: 'North (m)', gridcolor: '#334155', zerolinecolor: '#475569', color: '#94a3b8' },
                                    zaxis: { title: 'TVD (m)', autorange: 'reversed', gridcolor: '#334155', zerolinecolor: '#475569', color: '#94a3b8' },
                                    camera: {
                                        eye: { x: 1.5, y: 1.5, z: 0.5 }
                                    }
                                },
                                showlegend: true,
                                legend: { font: { color: '#cbd5e1' }, bgcolor: 'rgba(0,0,0,0.5)' }
                            }}
                            useResizeHandler={true}
                            style={{ width: '100%', height: '100%' }}
                        />
                    )}
                </div>
            </div>
        </div>
    );
};

export default Trajectory3DViewer;
