import React, { useState, useEffect, useMemo, useRef, useCallback } from 'react';
import { Target, Box, ChevronDown, ChevronUp, Moon, Globe, Mountain, Compass, MapPin, AlertCircle, ShieldCheck } from 'lucide-react';
import Map, { Marker, NavigationControl, Source, Layer } from 'react-map-gl/maplibre';
import * as maplibregl from 'maplibre-gl';
import axios from 'axios';
import { API_BASE } from '../lib/api';
import 'maplibre-gl/dist/maplibre-gl.css';
import Trajectory3DViewer from './Trajectory3DViewer';
import SourceTag from './SourceTag';
import { REGIONS_CONFIG, getRegionIdFromWellId } from '../lib/regionalGeology';

function createGeoJSONCircle(center, radiusInKm, points = 64) {
    const coords = { latitude: center[1], longitude: center[0] };
    const km = radiusInKm;
    const ret = [];
    const distanceX = km / (111.320 * Math.cos(coords.latitude * Math.PI / 180));
    const distanceY = km / 110.574;

    for (let i = 0; i < points; i++) {
        const theta = (i / points) * (2 * Math.PI);
        const x = distanceX * Math.cos(theta);
        const y = distanceY * Math.sin(theta);
        ret.push([coords.longitude + x, coords.latitude + y]);
    }
    ret.push(ret[0]); // Close polygon

    return {
        type: "FeatureCollection",
        features: [{
            type: "Feature",
            geometry: {
                type: "Polygon",
                coordinates: [ret]
            }
        }]
    };
}

function getCircleBoundingBox(center, radiusInKm) {
    const coords = { latitude: center[1], longitude: center[0] };
    const km = radiusInKm;
    const distanceX = km / (111.320 * Math.cos(coords.latitude * Math.PI / 180));
    const distanceY = km / 110.574;
    return [
        [coords.longitude - distanceX, coords.latitude - distanceY],
        [coords.longitude + distanceX, coords.latitude + distanceY]
    ];
}

const isOffline = import.meta.env.VITE_OFFLINE_MODE === 'true';

const osmStyle = "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json";

const satelliteStyle = {
    version: 8,
    sources: {
        'esri-satellite': {
            type: 'raster',
            tiles: ['https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'],
            tileSize: 256,
            attribution: 'Esri, Maxar, Earthstar Geographics'
        }
    },
    layers: [{ id: 'esri-satellite-layer', type: 'raster', source: 'esri-satellite', minzoom: 0, maxzoom: 19 }]
};

const terrainStyle = {
    version: 8,
    sources: {
        'opentopo': {
            type: 'raster',
            tiles: [
                'https://a.tile.opentopomap.org/{z}/{x}/{y}.png',
                'https://b.tile.opentopomap.org/{z}/{x}/{y}.png',
                'https://c.tile.opentopomap.org/{z}/{x}/{y}.png'
            ],
            tileSize: 256,
            attribution: 'OpenTopoMap (CC-BY-SA)'
        }
    },
    layers: [{ id: 'opentopo-layer', type: 'raster', source: 'opentopo', minzoom: 0, maxzoom: 17 }]
};

export const BASEMAP_STORAGE_KEY = 'petrolq_basemap_style';

export const BASEMAP_OPTIONS = [
    { id: 'dark', label: 'Dark', icon: Moon },
    { id: 'satellite', label: 'Satellite', icon: Globe },
    { id: 'terrain', label: 'Terrain', icon: Mountain }
];

const REGION_THEME = {
    assam: {
        color: '#10B981',
        border: 'border-emerald-400',
        bg: 'bg-emerald-500',
        glow: 'shadow-[0_0_12px_rgba(16,185,129,0.7)]',
        label: 'Assam'
    },
    rajasthan: {
        color: '#F59E0B',
        border: 'border-amber-400',
        bg: 'bg-amber-500',
        glow: 'shadow-[0_0_12px_rgba(245,158,11,0.7)]',
        label: 'Rajasthan'
    },
    kg: {
        color: '#0284C7',
        border: 'border-sky-400',
        bg: 'bg-sky-500',
        glow: 'shadow-[0_0_12px_rgba(2,132,199,0.7)]',
        label: 'KG Deepwater'
    },
    mizoram: {
        color: '#8B5CF6',
        border: 'border-purple-400',
        bg: 'bg-purple-500',
        glow: 'shadow-[0_0_12px_rgba(139,92,246,0.7)]',
        label: 'Mizoram'
    }
};

export default function WellMap({ 
    activeWellId, 
    onSelectWell, 
    selectedRegion = 'all',
    onSelectRegion,
    currentDepth, 
    activeScenario,
    is3DViewerOpen: external3DOpen,
    setIs3DViewerOpen: setExternal3DOpen,
    basemapStyle: externalBasemapStyle,
    onBasemapChange: externalOnBasemapChange
}) {
    const mapRef = useRef(null);
    const initialConfig = REGIONS_CONFIG[selectedRegion] || REGIONS_CONFIG.assam;

    const [viewState, setViewState] = useState({
        longitude: initialConfig.center[1],
        latitude: initialConfig.center[0],
        zoom: initialConfig.zoom || 8,
        pitch: 25
    });

    const [internalBasemapStyle, setInternalBasemapStyle] = useState(() => {
        try {
            const saved = localStorage.getItem(BASEMAP_STORAGE_KEY);
            if (saved && ['dark', 'satellite', 'terrain'].includes(saved)) {
                return saved;
            }
        } catch (e) {
            console.warn("Could not read basemapStyle from localStorage", e);
        }
        return 'dark';
    });

    const basemapStyle = externalBasemapStyle !== undefined ? externalBasemapStyle : internalBasemapStyle;

    const [wells, setWells] = useState([]);
    const [radius, setRadius] = useState(50);
    const [isCollapsed, setIsCollapsed] = useState(false);
    const [position, setPosition] = useState({ x: 24, y: 150 });
    const [isDragging, setIsDragging] = useState(false);
    const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
    const [internal3DOpen, setInternal3DOpen] = useState(false);
    const is3DViewerOpen = external3DOpen !== undefined ? external3DOpen : internal3DOpen;
    const setIs3DViewerOpen = setExternal3DOpen || setInternal3DOpen;

    const [searchCoords, setSearchCoords] = useState({ 
        lat: initialConfig.center[0], 
        lon: initialConfig.center[1] 
    });

    // 1. Fetch nearby/regional wells whenever region or search parameters change
    useEffect(() => {
        const fetchWells = async () => {
            try {
                const params = {
                    region: selectedRegion || 'all'
                };
                if (selectedRegion && selectedRegion !== 'all') {
                    params.lat = searchCoords.lat;
                    params.lon = searchCoords.lon;
                    params.radius_km = radius;
                } else {
                    params.radius_km = 3000; // Return all across India
                }
                const response = await axios.get(`${API_BASE}/api/wells/nearby`, { params });
                setWells(response.data);
            } catch (err) {
                console.error("Failed to fetch regional wells:", err);
            }
        };
        fetchWells();
    }, [selectedRegion, searchCoords.lat, searchCoords.lon, radius]);

    // Center map helper: smoothly animates and centers camera on a target well
    const centerOnWell = useCallback((wellOrId, customZoom = 11) => {
        if (!wellOrId) return;

        const targetId = typeof wellOrId === 'string' ? wellOrId : wellOrId.well_id;
        const wellObj = typeof wellOrId === 'object' ? wellOrId : wells.find(w => w.well_id === targetId);

        const doFly = (lon, lat) => {
            const targetZoom = Math.max(customZoom, 10.5);
            const map = mapRef.current?.getMap ? mapRef.current.getMap() : mapRef.current;
            if (map && map.flyTo) {
                map.flyTo({
                    center: [lon, lat],
                    zoom: targetZoom,
                    duration: 1000,
                    essential: true
                });
            }
            setViewState(prev => ({
                ...prev,
                latitude: lat,
                longitude: lon,
                zoom: targetZoom
            }));
            setSearchCoords({ lat, lon });
        };

        if (wellObj?.surface_location) {
            const { lat, lon } = wellObj.surface_location;
            if (lat !== undefined && lon !== undefined) {
                doFly(lon, lat);
                return;
            }
        }

        // Fallback: if not yet in local wells array, use regional calibrated center coordinates
        const regKey = getRegionIdFromWellId(targetId);
        const regConfig = REGIONS_CONFIG[regKey];
        if (regConfig?.center) {
            doFly(regConfig.center[1], regConfig.center[0], 9.5);
        }
    }, [wells]);

    // 2. Synchronize search radius & fallback camera when region changes
    useEffect(() => {
        const config = REGIONS_CONFIG[selectedRegion] || REGIONS_CONFIG.all;
        if (config) {
            const targetLat = config.center[0];
            const targetLon = config.center[1];
            const targetZoom = config.zoom || 8;

            setRadius(selectedRegion === 'all' ? 1200 : selectedRegion === 'assam' ? 60 : 250);

            // If active well already belongs to this region, let centerOnWell handle camera
            const activeWellRegion = getRegionIdFromWellId(activeWellId);
            const wellBelongsToRegion = activeWellRegion === selectedRegion;
            
            if (!activeWellId || !wellBelongsToRegion) {
                setSearchCoords({ lat: targetLat, lon: targetLon });
                setViewState(prev => ({
                    ...prev,
                    latitude: targetLat,
                    longitude: targetLon,
                    zoom: targetZoom
                }));

                const map = mapRef.current?.getMap ? mapRef.current.getMap() : mapRef.current;
                if (map && map.flyTo) {
                    map.flyTo({
                        center: [targetLon, targetLat],
                        zoom: targetZoom,
                        duration: 1000,
                        essential: true
                    });
                }
            }
        }
    }, [selectedRegion, activeWellId]);

    // 3. Center automatically on active well whenever activeWellId changes OR when wells load
    useEffect(() => {
        if (!activeWellId || wells.length === 0) return;
        const active = wells.find(w => w.well_id === activeWellId);
        if (active && active.surface_location) {
            centerOnWell(active, 11);
        }
    }, [activeWellId, wells, centerOnWell]);

    const circleGeoJSON = useMemo(() => {
        if (selectedRegion === 'all') return null;
        return createGeoJSONCircle([searchCoords.lon, searchCoords.lat], radius);
    }, [searchCoords, radius, selectedRegion]);

    const setAsActiveRig = () => {
        const active = wells.find(w => w.well_id === activeWellId);
        if (active && active.surface_location) {
            const newCoords = {
                lat: active.surface_location.lat,
                lon: active.surface_location.lon
            };
            setSearchCoords(newCoords);
            const map = mapRef.current?.getMap ? mapRef.current.getMap() : mapRef.current;
            if (map && map.flyTo) {
                map.flyTo({ center: [newCoords.lon, newCoords.lat], zoom: 11, duration: 800 });
            }
            setViewState(prev => ({ ...prev, latitude: newCoords.lat, longitude: newCoords.lon, zoom: 11 }));
        }
    };

    const handlePointerDown = (e) => {
        if (e.target.tagName.toLowerCase() === 'input' || e.target.tagName.toLowerCase() === 'button') {
            return;
        }
        setIsDragging(true);
        setDragStart({ x: e.clientX - position.x, y: e.clientY - position.y });
        e.target.setPointerCapture(e.pointerId);
    };

    const handlePointerMove = (e) => {
        if (!isDragging) return;
        setPosition({ x: e.clientX - dragStart.x, y: e.clientY - dragStart.y });
    };

    const handlePointerUp = (e) => {
        setIsDragging(false);
        if (e.target.hasPointerCapture(e.pointerId)) {
            e.target.releasePointerCapture(e.pointerId);
        }
    };

    const handleBasemapChange = (styleId) => {
        if (externalOnBasemapChange) {
            externalOnBasemapChange(styleId);
        } else {
            setInternalBasemapStyle(styleId);
        }
        try {
            localStorage.setItem(BASEMAP_STORAGE_KEY, styleId);
        } catch (e) {
            console.warn("Could not save basemapStyle to localStorage", e);
        }
    };

    const currentMapStyle = useMemo(() => {
        switch (basemapStyle) {
            case 'satellite':
                return satelliteStyle;
            case 'terrain':
                return terrainStyle;
            case 'dark':
            default:
                return osmStyle;
        }
    }, [basemapStyle]);

    const hideBorders = (map) => {
        if (!map || !map.getLayer) return;
        const borderLayers = ['boundary_county', 'boundary_state', 'boundary_country_outline', 'boundary_country_inner'];
        borderLayers.forEach(layer => {
            if (map.getLayer(layer)) {
                map.setLayoutProperty(layer, 'visibility', 'none');
            }
        });
    };

    const handleMapLoad = (evt) => {
        const map = evt.target;
        hideBorders(map);
        if (map.on) {
            map.on('style.load', () => hideBorders(map));
        }
    };

    return (
        <div className="relative w-full h-full flex-1 overflow-hidden">
            <Map
                mapLib={maplibregl}
                ref={mapRef}
                onLoad={handleMapLoad}
                {...viewState}
                onMove={evt => setViewState(evt.viewState)}
                mapStyle={currentMapStyle}
                style={{ width: '100%', height: '100%' }}
            >
                <NavigationControl position="bottom-right" />

                {/* Radius Polygon - Active only when inspecting a single region */}
                {circleGeoJSON && (
                    <>
                        <Source id="radius-source-fill" type="geojson" data={circleGeoJSON}>
                            <Layer 
                                id="radius-fill" 
                                type="fill" 
                                paint={{
                                    'fill-color': '#0284C7',
                                    'fill-opacity': 0.18
                                }} 
                            />
                        </Source>
                        <Source id="radius-source-line" type="geojson" data={circleGeoJSON}>
                            <Layer 
                                id="radius-line" 
                                type="line" 
                                paint={{
                                    'line-color': '#38BDF8',
                                    'line-width': 2,
                                    'line-dasharray': [2, 2]
                                }} 
                            />
                        </Source>
                    </>
                )}

                {/* Regional Well Markers */}
                {wells.map(well => {
                    const loc = well.surface_location;
                    if (!loc || typeof loc !== 'object' || loc.lat === undefined || loc.lon === undefined) return null;
                    
                    const isActive = well.well_id === activeWellId;
                    const regionKey = getRegionIdFromWellId(well.well_id);
                    const theme = REGION_THEME[regionKey] || REGION_THEME.assam;
                    
                    return (
                        <Marker 
                            key={well.well_id || well.id} 
                            longitude={loc.lon} 
                            latitude={loc.lat}
                            anchor="center"
                            onClick={e => {
                                e.originalEvent.stopPropagation();
                                onSelectWell(well.well_id);
                                centerOnWell(well, 11.5);
                            }}
                        >
                            <div className="relative flex items-center justify-center cursor-pointer group">
                                {isActive && (
                                    <>
                                        <span className="animate-ping absolute inline-flex h-10 w-10 rounded-full bg-emerald-400 opacity-60"></span>
                                        <span className="absolute inline-flex h-7 w-7 rounded-full bg-emerald-500/30 border border-emerald-400"></span>
                                    </>
                                )}
                                
                                <div className={`
                                    relative z-10 rounded-full border-2 transition-all transform group-hover:scale-125 flex items-center justify-center
                                    ${isActive 
                                        ? 'bg-emerald-400 border-white w-5 h-5 shadow-[0_0_15px_rgba(52,211,153,0.9)]' 
                                        : `${theme.bg} ${theme.border} ${theme.glow} w-3.5 h-3.5 hover:scale-110`}
                                `}>
                                    {isActive ? (
                                        <div className="w-1.5 h-1.5 rounded-full bg-slate-950"></div>
                                    ) : (
                                        <div className="w-1 h-1 rounded-full bg-white/70"></div>
                                    )}
                                </div>
                                
                                {/* Rich Interactive Tooltip */}
                                <div className="absolute bottom-8 opacity-0 group-hover:opacity-100 transition-all duration-200 bg-[#0c1322]/95 border border-slate-700 text-slate-100 text-[11px] font-mono px-3 py-2 rounded-xl shadow-2xl pointer-events-none whitespace-nowrap z-50 flex flex-col space-y-1.5 backdrop-blur-md">
                                    <div className="flex items-center space-x-2">
                                        <span className={`w-2 h-2 rounded-full ${isActive ? 'bg-emerald-400' : theme.bg}`}></span>
                                        <span className="font-bold tracking-wide">{well.well_id}</span>
                                        {isActive && <span className="text-[9px] text-emerald-400 font-sans font-extrabold bg-emerald-500/10 px-1.5 py-0.5 rounded border border-emerald-500/30">ACTIVE RIG</span>}
                                        <SourceTag source={well.well_id} compact={true} />
                                    </div>
                                    <div className="flex items-center justify-between text-[10px] text-slate-400 border-t border-slate-800 pt-1">
                                        <span>{well.field_name || theme.label}</span>
                                        <span className="font-semibold text-slate-300 ml-3">{well.total_depth_tvd ? `${well.total_depth_tvd}m TVD` : ''}</span>
                                    </div>
                                </div>
                            </div>
                        </Marker>
                    );
                })}
            </Map>

            {/* Floating Control Card (Draggable / Mobile Responsive) */}
            <div 
                className={`absolute w-84 max-w-[calc(100vw-32px)] glass-panel border border-slate-750 shadow-glass rounded-2xl p-3.5 sm:p-4 z-10 transition-all ${isDragging ? 'cursor-grabbing' : 'cursor-grab'}`}
                style={{ top: Math.max(60, position.y), left: Math.max(12, position.x), touchAction: 'none' }}
                onPointerDown={handlePointerDown}
                onPointerMove={handlePointerMove}
                onPointerUp={handlePointerUp}
                onPointerCancel={handlePointerUp}
            >
                <div className="flex items-center justify-between mb-2">
                    <h3 className="font-display font-bold text-slate-100 flex items-center text-xs sm:text-sm">
                        <Target size={16} className="mr-2 text-cyan-400" />
                        Regional Exploration Map
                    </h3>
                    <div className="flex items-center space-x-1.5">
                        <span className="bg-cyan-950/60 text-cyan-300 border border-cyan-500/30 px-2 py-0.5 rounded-full text-[10px] font-mono font-bold">
                            {wells.length} Wells
                        </span>
                        <button
                            onClick={() => setIsCollapsed(!isCollapsed)}
                            className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
                            title={isCollapsed ? "Expand Search Controls" : "Collapse Search Controls"}
                        >
                            {isCollapsed ? <ChevronDown size={15} /> : <ChevronUp size={15} />}
                        </button>
                    </div>
                </div>

                {!isCollapsed && (
                    <div className="space-y-3 pt-1">
                        {/* Region Indicator Pill */}
                        <div className="flex flex-col space-y-1.5 bg-slate-900/80 px-2.5 py-1.5 rounded-lg border border-slate-800">
                            <div className="flex items-center justify-between text-[11px]">
                                <span className="text-slate-400 flex items-center">
                                    <Compass size={13} className="mr-1.5 text-cyan-400" />
                                    Active Basin:
                                </span>
                                <span className="font-semibold text-slate-200 capitalize">
                                    {REGIONS_CONFIG[selectedRegion]?.name || "Pan-India Portfolio"}
                                </span>
                            </div>
                            {selectedRegion !== 'all' && (
                                <div className="flex items-center space-x-1.5 text-[9.5px] font-sans text-emerald-300 bg-emerald-500/10 border border-emerald-500/30 rounded px-2 py-0.5 leading-snug">
                                    <ShieldCheck size={11} className="text-emerald-400 shrink-0" />
                                    <span>Regionally Calibrated Geomechanics</span>
                                </div>
                            )}
                        </div>

                        {selectedRegion !== 'all' && (
                            <div>
                                <div className="flex justify-between text-xs font-mono text-slate-400 mb-1.5">
                                    <span>Inspection Radius:</span>
                                    <span className="text-cyan-400 font-bold">{radius.toFixed(0)} km</span>
                                </div>
                                <input 
                                    type="range" 
                                    min="20.0" 
                                    max="500.0" 
                                    step="10.0" 
                                    value={radius}
                                    onChange={(e) => setRadius(parseFloat(e.target.value))}
                                    className="w-full accent-cyan-500 bg-slate-800 rounded-lg appearance-none cursor-pointer h-1.5"
                                />
                            </div>
                        )}

                        <button 
                            onClick={setAsActiveRig}
                            className="w-full bg-slate-850 hover:bg-slate-800 active:bg-slate-750 text-slate-200 text-xs font-medium py-2.5 rounded-xl transition-colors border border-slate-700/80 flex items-center justify-center min-h-[40px] shadow-sm"
                        >
                            <MapPin size={14} className="mr-2 text-emerald-400" />
                            Fly to Active Wellhead ({activeWellId ? activeWellId.replace('OIL-', '') : 'None'})
                        </button>
                        
                        <button 
                            onClick={() => setIs3DViewerOpen(true)}
                            className="w-full bg-gradient-to-r from-cyan-500/20 via-blue-500/20 to-cyan-500/20 hover:from-cyan-500/30 hover:to-blue-500/30 active:scale-[0.99] text-cyan-300 text-xs font-semibold py-2.5 rounded-xl transition-all border border-cyan-500/40 shadow-glow-cyan flex items-center justify-center min-h-[40px]"
                        >
                            <Box size={15} className="mr-2 text-cyan-400" />
                            View 3D Subsurface Trajectory
                        </button>
                    </div>
                )}
            </div>

            <Trajectory3DViewer 
                isOpen={is3DViewerOpen} 
                onClose={() => setIs3DViewerOpen(false)} 
                activeWellId={activeWellId} 
                offsetWells={wells} 
                currentDepth={currentDepth}
                activeScenario={activeScenario}
                selectedRegion={selectedRegion}
            />
        </div>
    );
}
