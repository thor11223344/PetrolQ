import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import Plot from 'react-plotly.js';
import { 
    X, 
    Loader2, 
    RefreshCw, 
    Layers, 
    Compass, 
    AlertTriangle, 
    CheckCircle2, 
    ShieldAlert, 
    Eye, 
    EyeOff,
    Maximize2
} from 'lucide-react';

const Trajectory3DViewer = ({ isOpen, onClose, activeWellId, offsetWells = [] }) => {
    const [plotData, setPlotData] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    const [antiCollisionData, setAntiCollisionData] = useState(null);
    const [showOffsets, setShowOffsets] = useState(true);
    const [showFormations, setShowFormations] = useState(true);
    const [showClosestApproach, setShowClosestApproach] = useState(true);
    const [cameraRevision, setCameraRevision] = useState(0);
    const [currentCamera, setCurrentCamera] = useState({
        eye: { x: 1.5, y: 1.5, z: 0.5 },
        center: { x: 0, y: 0, z: -0.15 },
        up: { x: 0, y: 0, z: 1 }
    });

    // Cached raw data
    const rawDataRef = useRef({
        activeWell: null,
        offsets: [],
        antiCollision: null
    });

    useEffect(() => {
        if (!isOpen || !activeWellId) return;

        const fetchTrajectories = async () => {
            setIsLoading(true);
            try {
                // 1. Fetch Active Well Trajectory
                let activeTrajectory = null;
                try {
                    const activeRes = await axios.get(`http://localhost:8000/api/wells/${activeWellId}/trajectory?is_active=true`);
                    activeTrajectory = activeRes.data;
                } catch (e) {
                    console.error("Failed to load active well trajectory", e);
                }

                // 2. Fetch Offset Wells Trajectories
                const loadedOffsets = [];
                const offsetList = offsetWells.filter(w => w.well_id !== activeWellId);
                for (const w of offsetList) {
                    try {
                        const offsetRes = await axios.get(`http://localhost:8000/api/wells/${w.well_id}/trajectory?is_active=false`);
                        loadedOffsets.push(offsetRes.data);
                    } catch (e) {
                        console.warn(`Could not load offset ${w.well_id}`, e);
                    }
                }

                // 3. Fetch Anti-Collision Analysis
                let antiCollision = null;
                try {
                    const offsetIdsParam = offsetList.map(w => w.well_id).join(',');
                    const acRes = await axios.get(`http://localhost:8000/api/wells/${activeWellId}/anti-collision?offset_ids=${offsetIdsParam}`);
                    antiCollision = acRes.data;
                    setAntiCollisionData(antiCollision);
                } catch (e) {
                    console.warn("Anti-collision endpoint error, calculating fallback", e);
                }

                rawDataRef.current = {
                    activeWell: activeTrajectory,
                    offsets: loadedOffsets,
                    antiCollision: antiCollision
                };

                buildPlotTraces();
            } catch (error) {
                console.error("Failed to assemble 3D subsurface scene", error);
            } finally {
                setIsLoading(false);
            }
        };

        fetchTrajectories();
    }, [isOpen, activeWellId, offsetWells]);

    // Rebuild plot traces whenever toggles change
    useEffect(() => {
        if (rawDataRef.current.activeWell) {
            buildPlotTraces();
        }
    }, [showOffsets, showFormations, showClosestApproach]);

    const buildPlotTraces = () => {
        const { activeWell, offsets, antiCollision } = rawDataRef.current;
        if (!activeWell) return;

        const traces = [];

        // ----------------------------------------------------
        // 1. GROUND SURFACE REFERENCE PLANE at Z = 0 (Issue 4)
        // ----------------------------------------------------
        const planeExtent = 750;
        traces.push({
            type: 'mesh3d',
            name: 'Ground Surface (0m TVD)',
            x: [-planeExtent, planeExtent, planeExtent, -planeExtent],
            y: [-planeExtent, -planeExtent, planeExtent, planeExtent],
            z: [0, 0, 0, 0],
            i: [0, 0],
            j: [1, 2],
            k: [2, 3],
            opacity: 0.12,
            color: '#38BDF8',
            showlegend: true,
            hoverinfo: 'name'
        });

        // Surface Grid Boundary line
        traces.push({
            type: 'scatter3d',
            mode: 'lines',
            name: 'Ground Perimeter',
            x: [-planeExtent, planeExtent, planeExtent, -planeExtent, -planeExtent],
            y: [-planeExtent, -planeExtent, planeExtent, planeExtent, -planeExtent],
            z: [0, 0, 0, 0, 0],
            line: { color: '#0284C7', width: 2, dash: 'dot' },
            showlegend: false,
            hoverinfo: 'none'
        });

        // ----------------------------------------------------
        // 2. SURFACE WELLHEAD MARKERS & LABELS (Issue 5)
        // ----------------------------------------------------
        const wellheadXs = [activeWell.surface?.x || 0];
        const wellheadYs = [activeWell.surface?.y || 0];
        const wellheadZs = [0];
        const wellheadTexts = [`★ Active: ${activeWell.well_id}`];
        const wellheadColors = ['#06B6D4'];
        const wellheadSizes = [9];

        if (showOffsets) {
            offsets.forEach(off => {
                wellheadXs.push(off.surface?.x || 0);
                wellheadYs.push(off.surface?.y || 0);
                wellheadZs.push(0);
                wellheadTexts.push(off.well_id);
                wellheadColors.push('#94A3B8');
                wellheadSizes.push(6);
            });
        }

        traces.push({
            type: 'scatter3d',
            mode: 'markers+text',
            name: 'Surface Wellheads',
            x: wellheadXs,
            y: wellheadYs,
            z: wellheadZs,
            text: wellheadTexts,
            textposition: 'top center',
            textfont: { color: '#E2E8F0', size: 11, family: 'Inter, sans-serif' },
            marker: {
                size: wellheadSizes,
                color: wellheadColors,
                symbol: 'diamond',
                line: { color: '#0F172A', width: 1.5 }
            },
            showlegend: true,
            hoverinfo: 'text'
        });

        // ----------------------------------------------------
        // 3. ACTIVE WELL TRAJECTORY WITH RISK GRADIENT (Issue 6 & 7)
        // ----------------------------------------------------
        const actTraj = activeWell.trajectory;
        const activeCustomData = actTraj.md.map((md, i) => [
            md,
            actTraj.z[i],
            actTraj.inclination[i],
            actTraj.azimuth[i],
            actTraj.risk_scores ? actTraj.risk_scores[i] : 0.2
        ]);

        traces.push({
            type: 'scatter3d',
            mode: 'lines+markers',
            name: `Active: ${activeWell.well_id}`,
            x: actTraj.x,
            y: actTraj.y,
            z: actTraj.z,
            text: actTraj.z.map(() => `Active: ${activeWell.well_id}`),
            customdata: activeCustomData,
            hovertemplate: 
                '<b>%{text}</b><br>' +
                'Measured Depth (MD): <b>%{customdata[0]:.1f} m</b><br>' +
                'True Vertical Depth (TVD): <b>%{customdata[1]:.1f} m</b><br>' +
                'Inclination: <b>%{customdata[2]:.1f}°</b> | Azimuth: <b>%{customdata[3]:.1f}°</b><br>' +
                'ML Hazard Risk: <b>%{customdata[4]:.2f}</b><extra></extra>',
            line: {
                width: 7,
                color: '#38BDF8'
            },
            marker: {
                size: 3.5,
                color: actTraj.risk_scores || actTraj.z.map(() => 0.2),
                cmin: 0.0,
                cmax: 1.0,
                colorscale: [
                    [0.0, '#22C55E'], // Green (Safe)
                    [0.35, '#38BDF8'], // Cyan
                    [0.65, '#F59E0B'], // Amber
                    [1.0, '#EF4444']  // Red (Kick/Overpressure)
                ],
                showscale: true,
                colorbar: {
                    title: {
                        text: 'ML Hazard<br>Risk Score',
                        font: { color: '#CBD5E1', size: 11, family: 'Inter' }
                    },
                    tickvals: [0.1, 0.5, 0.9],
                    ticktext: ['Low (Safe)', 'Moderate', 'Critical Hazard'],
                    tickfont: { color: '#94A3B8', size: 10 },
                    len: 0.45,
                    y: 0.5,
                    thickness: 14,
                    outlinecolor: '#334155'
                }
            }
        });

        // ----------------------------------------------------
        // 4. FORMATION TOPS ALONG TRAJECTORY (Issue 2)
        // ----------------------------------------------------
        if (showFormations && activeWell.formation_tops && activeWell.formation_tops.length > 0) {
            const formXs = [];
            const formYs = [];
            const formZs = [];
            const formTexts = [];
            const formColors = [];
            const formCustomData = [];

            activeWell.formation_tops.forEach(f => {
                formXs.push(f.x);
                formYs.push(f.y);
                formZs.push(f.z);
                formTexts.push(f.name);
                formColors.push(f.color);
                formCustomData.push([f.name, f.tvd, f.md, f.description]);

                // Small geological horizon ring around active trajectory at formation boundary
                const ringRadius = 110;
                const ringPts = 24;
                const rX = [];
                const rY = [];
                const rZ = [];
                for (let step = 0; step <= ringPts; step++) {
                    const theta = (step / ringPts) * 2 * Math.PI;
                    rX.push(f.x + ringRadius * Math.cos(theta));
                    rY.push(f.y + ringRadius * Math.sin(theta));
                    rZ.push(f.z);
                }
                traces.push({
                    type: 'scatter3d',
                    mode: 'lines',
                    name: `${f.name} Horizon`,
                    x: rX,
                    y: rY,
                    z: rZ,
                    line: { color: f.color, width: 3, dash: 'dash' },
                    opacity: 0.65,
                    showlegend: false,
                    hoverinfo: 'none'
                });
            });

            traces.push({
                type: 'scatter3d',
                mode: 'markers+text',
                name: 'Formation Tops',
                x: formXs,
                y: formYs,
                z: formZs,
                text: formTexts.map(name => `▲ Top ${name}`),
                textposition: 'middle right',
                textfont: { color: '#F8FAFC', size: 11, family: 'Inter, sans-serif' },
                customdata: formCustomData,
                hovertemplate: 
                    '<b>Stratigraphic Formation Top</b><br>' +
                    'Formation: <b>%{customdata[0]}</b><br>' +
                    'Depth TVD: <b>%{customdata[1]:.1f} m</b> (MD: %{customdata[2]:.1f} m)<br>' +
                    'Geology Note: <i>%{customdata[3]}</i><extra></extra>',
                marker: {
                    size: 8,
                    color: formColors,
                    symbol: 'circle',
                    line: { color: '#FFFFFF', width: 2 }
                },
                showlegend: true
            });
        }

        // ----------------------------------------------------
        // 5. OFFSET WELL TRAJECTORIES (FANNING OUT) (Issue 1 & 10)
        // ----------------------------------------------------
        if (showOffsets) {
            offsets.forEach(off => {
                const oTraj = off.trajectory;
                const offsetCustom = oTraj.md.map((md, i) => [
                    md,
                    oTraj.z[i],
                    oTraj.inclination[i],
                    oTraj.azimuth[i]
                ]);

                traces.push({
                    type: 'scatter3d',
                    mode: 'lines',
                    name: `Offset: ${off.well_id}`,
                    x: oTraj.x,
                    y: oTraj.y,
                    z: oTraj.z,
                    text: oTraj.z.map(() => `Offset: ${off.well_id}`),
                    customdata: offsetCustom,
                    hovertemplate: 
                        '<b>%{text}</b><br>' +
                        'MD: <b>%{customdata[0]:.1f} m</b> | TVD: <b>%{customdata[1]:.1f} m</b><br>' +
                        'Inc: <b>%{customdata[2]:.1f}°</b> | Az: <b>%{customdata[3]:.1f}°</b><extra></extra>',
                    line: { width: 3.5, color: '#64748B' },
                    opacity: 0.75,
                    showlegend: true
                });
            });
        }

        // ----------------------------------------------------
        // 6. ANTI-COLLISION CLOSEST APPROACH CONNECTOR (Issue 3 & 8)
        // ----------------------------------------------------
        if (showClosestApproach && antiCollision && antiCollision.closest_approach) {
            const ca = antiCollision.closest_approach;
            const actPt = ca.active_point;
            const offPt = ca.offset_point;
            const isAlert = ca.min_distance_m < 60;
            const isCaution = ca.min_distance_m < 120;
            const highlightColor = isAlert ? '#EF4444' : (isCaution ? '#F59E0B' : '#10B981');

            // 3D Connector Segment
            traces.push({
                type: 'scatter3d',
                mode: 'lines+markers+text',
                name: `Min Separation (${ca.min_distance_m}m)`,
                x: [actPt.x, offPt.x],
                y: [actPt.y, offPt.y],
                z: [actPt.z, offPt.z],
                line: {
                    color: highlightColor,
                    width: 6,
                    dash: 'solid'
                },
                marker: {
                    size: 7,
                    color: highlightColor,
                    symbol: 'diamond',
                    line: { color: '#FFFFFF', width: 1.5 }
                },
                text: ['', `⚠ ${ca.min_distance_m}m to ${ca.offset_well_id}`],
                textposition: 'top right',
                textfont: {
                    color: highlightColor,
                    size: 12,
                    family: 'Inter, sans-serif'
                },
                hovertemplate: 
                    '<b>Subsurface Closest Approach</b><br>' +
                    'Active MD: <b>' + actPt.md.toFixed(1) + ' m</b> (TVD: ' + actPt.tvd.toFixed(1) + ' m)<br>' +
                    'Offset MD: <b>' + offPt.md.toFixed(1) + ' m</b> (' + ca.offset_well_id + ')<br>' +
                    '3D Minimum Distance: <b>' + ca.min_distance_m + ' m</b><br>' +
                    'Collision Hazard Status: <b>' + ca.status + '</b><extra></extra>',
                showlegend: true
            });
        }

        setPlotData(traces);
    };

    // Camera control presets (Issue 9)
    const setCameraView = (type) => {
        let newCam = {
            eye: { x: 1.5, y: 1.5, z: 0.5 },
            center: { x: 0, y: 0, z: -0.15 },
            up: { x: 0, y: 0, z: 1 }
        };

        if (type === 'plan') {
            // Top-down looking straight down
            newCam = {
                eye: { x: 0, y: 0.001, z: 2.4 },
                center: { x: 0, y: 0, z: 0 },
                up: { x: 0, y: 1, z: 0 }
            };
        } else if (type === 'section-ew') {
            // Looking North (viewing East-West drift)
            newCam = {
                eye: { x: 0, y: 2.4, z: 0.05 },
                center: { x: 0, y: 0, z: -0.2 },
                up: { x: 0, y: 0, z: 1 }
            };
        } else if (type === 'section-ns') {
            // Looking East (viewing North-South drift)
            newCam = {
                eye: { x: 2.4, y: 0, z: 0.05 },
                center: { x: 0, y: 0, z: -0.2 },
                up: { x: 0, y: 0, z: 1 }
            };
        }

        setCurrentCamera(newCam);
        setCameraRevision(prev => prev + 1);
    };

    if (!isOpen) return null;

    const ca = antiCollisionData?.closest_approach;

    return (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/85 backdrop-blur-md animate-in fade-in">
            <div className="bg-slate-900 border border-slate-700/80 w-[95vw] max-w-7xl h-[92vh] rounded-2xl shadow-2xl flex flex-col overflow-hidden animate-in zoom-in-95">
                
                {/* Header Bar with Controls */}
                <div className="flex flex-wrap justify-between items-center px-6 py-3.5 border-b border-slate-800 bg-slate-900/90 gap-3">
                    <div className="flex items-center space-x-3">
                        <div className="p-2 bg-cyan-500/10 border border-cyan-500/30 rounded-lg text-cyan-400">
                            <Compass size={20} />
                        </div>
                        <div>
                            <h2 className="text-base font-bold text-slate-100 flex items-center gap-2">
                                3D Directional Wellbore & Subsurface Geology
                                <span className="text-xs px-2.5 py-0.5 rounded-full bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 font-mono font-medium">
                                    Active: {activeWellId}
                                </span>
                            </h2>
                            <p className="text-xs text-slate-400">
                                Directional anti-collision monitoring with ML hazard score & stratigraphic tops
                            </p>
                        </div>
                    </div>

                    {/* Anti-collision Quick Badge */}
                    {ca && (
                        <div className={`flex items-center space-x-2 px-3 py-1.5 rounded-lg border text-xs font-semibold ${
                            ca.status === 'CRITICAL' 
                                ? 'bg-red-500/15 border-red-500/40 text-red-300 animate-pulse'
                                : ca.status === 'CAUTION'
                                ? 'bg-amber-500/15 border-amber-500/40 text-amber-300'
                                : 'bg-emerald-500/15 border-emerald-500/40 text-emerald-300'
                        }`}>
                            {ca.status === 'CRITICAL' ? <ShieldAlert size={16} /> : <AlertTriangle size={16} />}
                            <span>Closest Approach: <b>{ca.min_distance_m}m</b> to {ca.offset_well_id}</span>
                            <span className="opacity-75">({ca.status})</span>
                        </div>
                    )}

                    {/* Action & Close Controls */}
                    <div className="flex items-center space-x-2">
                        <button 
                            onClick={onClose} 
                            className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors"
                            title="Close 3D View"
                        >
                            <X size={22} />
                        </button>
                    </div>
                </div>

                {/* Secondary Toolbar: Camera & Layer Toggles */}
                <div className="flex flex-wrap items-center justify-between px-6 py-2 bg-slate-950 border-b border-slate-800/80 text-xs text-slate-300 gap-2">
                    {/* View Presets */}
                    <div className="flex items-center space-x-1.5">
                        <span className="text-slate-400 font-medium mr-1 flex items-center gap-1">
                            <Maximize2 size={13} /> Camera:
                        </span>
                        <button 
                            onClick={() => setCameraView('default')}
                            className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 flex items-center gap-1 transition-colors"
                        >
                            <RefreshCw size={12} /> Reset 3D
                        </button>
                        <button 
                            onClick={() => setCameraView('plan')}
                            className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-colors"
                        >
                            Plan (Top-Down)
                        </button>
                        <button 
                            onClick={() => setCameraView('section-ew')}
                            className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-colors"
                        >
                            Section (E-W)
                        </button>
                        <button 
                            onClick={() => setCameraView('section-ns')}
                            className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-colors"
                        >
                            Section (N-S)
                        </button>
                    </div>

                    {/* Feature Toggles */}
                    <div className="flex items-center space-x-3">
                        <label className="flex items-center space-x-1.5 cursor-pointer select-none hover:text-white">
                            <input 
                                type="checkbox" 
                                checked={showOffsets} 
                                onChange={(e) => setShowOffsets(e.target.checked)}
                                className="rounded bg-slate-800 border-slate-700 text-cyan-500 focus:ring-0 w-3.5 h-3.5"
                            />
                            <span>Offset Wells ({offsetWells.filter(w => w.well_id !== activeWellId).length})</span>
                        </label>

                        <label className="flex items-center space-x-1.5 cursor-pointer select-none hover:text-white">
                            <input 
                                type="checkbox" 
                                checked={showFormations} 
                                onChange={(e) => setShowFormations(e.target.checked)}
                                className="rounded bg-slate-800 border-slate-700 text-cyan-500 focus:ring-0 w-3.5 h-3.5"
                            />
                            <span>Formation Tops</span>
                        </label>

                        <label className="flex items-center space-x-1.5 cursor-pointer select-none hover:text-white">
                            <input 
                                type="checkbox" 
                                checked={showClosestApproach} 
                                onChange={(e) => setShowClosestApproach(e.target.checked)}
                                className="rounded bg-slate-800 border-slate-700 text-cyan-500 focus:ring-0 w-3.5 h-3.5"
                            />
                            <span>Closest Approach Line</span>
                        </label>
                    </div>
                </div>

                {/* 3D Canvas Area */}
                <div className="flex-1 relative bg-slate-950 overflow-hidden">
                    {isLoading ? (
                        <div className="absolute inset-0 flex flex-col items-center justify-center text-slate-400 bg-slate-950/90 z-10">
                            <Loader2 size={36} className="animate-spin mb-3 text-cyan-400" />
                            <p className="text-sm font-medium">Computing 3D Directional Trajectories & Anti-Collision Vectors...</p>
                            <p className="text-xs text-slate-400 mt-1">Calculating minimum 3D Euclidean distances across subsurface depths</p>
                        </div>
                    ) : (
                        <Plot
                            data={plotData}
                            layout={{
                                autosize: true,
                                margin: { l: 0, r: 0, b: 0, t: 0 },
                                paper_bgcolor: '#020617',
                                plot_bgcolor: '#020617',
                                uirevision: cameraRevision,
                                scene: {
                                    xaxis: { 
                                        title: 'East (m)', 
                                        gridcolor: '#1E293B', 
                                        zerolinecolor: '#334155', 
                                        color: '#94A3B8',
                                        backgroundcolor: '#020617',
                                        showbackground: true
                                    },
                                    yaxis: { 
                                        title: 'North (m)', 
                                        gridcolor: '#1E293B', 
                                        zerolinecolor: '#334155', 
                                        color: '#94A3B8',
                                        backgroundcolor: '#020617',
                                        showbackground: true
                                    },
                                    zaxis: { 
                                        title: 'TVD Depth (m)', 
                                        autorange: 'reversed', 
                                        gridcolor: '#1E293B', 
                                        zerolinecolor: '#334155', 
                                        color: '#94A3B8',
                                        backgroundcolor: '#020617',
                                        showbackground: true
                                    },
                                    camera: currentCamera,
                                    aspectratio: { x: 1, y: 1, z: 1.6 }
                                },
                                showlegend: true,
                                legend: { 
                                    font: { color: '#CBD5E1', size: 10, family: 'Inter' }, 
                                    bgcolor: 'rgba(15, 23, 42, 0.75)',
                                    bordercolor: '#334155',
                                    borderwidth: 1,
                                    x: 0.01,
                                    y: 0.98,
                                    itemclick: 'toggle',
                                    itemdoubleclick: 'toggleothers'
                                }
                            }}
                            useResizeHandler={true}
                            style={{ width: '100%', height: '100%' }}
                            config={{
                                responsive: true,
                                displayModeBar: true,
                                displaylogo: false,
                                modeBarButtonsToRemove: ['toImage', 'sendDataToCloud']
                            }}
                        />
                    )}
                </div>

                {/* Footer Legend Bar */}
                <div className="px-6 py-2 bg-slate-900 border-t border-slate-800 flex flex-wrap items-center justify-between text-xs text-slate-400">
                    <div className="flex items-center space-x-4">
                        <div className="flex items-center gap-1.5">
                            <span className="w-2.5 h-2.5 rounded-full bg-cyan-400"></span>
                            <span>Active Well Tube</span>
                        </div>
                        <div className="flex items-center gap-1.5">
                            <span className="w-2.5 h-2.5 rounded-full bg-slate-500"></span>
                            <span>Offset Trajectories</span>
                        </div>
                        <div className="flex items-center gap-1.5">
                            <span className="w-2.5 h-2.5 rounded-full bg-amber-500"></span>
                            <span>Tipam (1450m)</span>
                        </div>
                        <div className="flex items-center gap-1.5">
                            <span className="w-2.5 h-2.5 rounded-full bg-orange-500"></span>
                            <span>Barail Kick Zone (2400m)</span>
                        </div>
                        <div className="flex items-center gap-1.5">
                            <span className="w-2.5 h-2.5 rounded-full bg-purple-500"></span>
                            <span>Kopili (2950m)</span>
                        </div>
                    </div>
                    <div className="text-slate-400">
                        Rotate: <span className="text-slate-300">Left-Click + Drag</span> | Pan: <span className="text-slate-300">Right-Click + Drag</span> | Zoom: <span className="text-slate-300">Scroll</span>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Trajectory3DViewer;
