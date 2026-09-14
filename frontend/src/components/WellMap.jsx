import React, { useState, useEffect, useMemo } from 'react';
import { Target, AlertTriangle, Box, ChevronDown, ChevronUp, Moon, Globe, Mountain } from 'lucide-react';
import Map, { Marker, NavigationControl, Source, Layer } from 'react-map-gl/maplibre';
import * as maplibregl from 'maplibre-gl';
import axios from 'axios';
import { API_BASE } from '../lib/api';
import 'maplibre-gl/dist/maplibre-gl.css';
import Trajectory3DViewer from './Trajectory3DViewer';
import SourceTag from './SourceTag';
import { REGIONS_CONFIG } from '../lib/regionalGeology';

// Note: Mapbox requires an access token.
const MAPBOX_TOKEN = import.meta.env.VITE_MAPBOX_TOKEN || '';

function createGeoJSONCircle(center, radiusInKm, points = 64) {
    const coords = { latitude: center[1], longitude: center[0] };
    const km = radiusInKm;
    const ret = [];
    const distanceX = km / (111.320 * Math.cos(coords.latitude * Math.PI / 180));
    const distanceY = km / 110.574;

    let theta, x, y;
    for (let i = 0; i < points; i++) {
        theta = (i / points) * (2 * Math.PI);
        x = distanceX * Math.cos(theta);
        y = distanceY * Math.sin(theta);
        ret.push([coords.longitude + x, coords.latitude + y]);
    }
    ret.push(ret[0]); // Close the polygon

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
        [coords.longitude - distanceX, coords.latitude - distanceY], // southwest [minLon, minLat]
        [coords.longitude + distanceX, coords.latitude + distanceY]  // northeast [maxLon, maxLat]
    ];
}

const isOffline = import.meta.env.VITE_OFFLINE_MODE === 'true';

const offlineStyle = {
    version: 8,
    sources: {
        'offline-tiles': {
            type: 'raster',
            tiles: [`${API_BASE}/tiles/{z}/{x}/{y}.png`],
            tileSize: 256
        }
    },
    layers: [{
        id: 'offline-tiles-layer',
        type: 'raster',
        source: 'offline-tiles',
        minzoom: 0,
        maxzoom: 22
    }]
};

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

const BASEMAP_STORAGE_KEY = 'petrolq_basemap_style';

const BASEMAP_OPTIONS = [
    { id: 'dark', label: 'Dark', icon: Moon },
    { id: 'satellite', label: 'Satellite', icon: Globe },
    { id: 'terrain', label: 'Terrain', icon: Mountain }
];

export default function WellMap({ 
    activeWellId, 
    onSelectWell, 
    selectedRegion,
    onSelectRegion,
    currentDepth, 
    activeScenario,
    is3DViewerOpen: external3DOpen,
    setIs3DViewerOpen: setExternal3DOpen
}) {
    const [viewState, setViewState] = useState({
        longitude: 95.185,
        latitude: 27.415,
        zoom: 11,
        pitch: 30
    });

    const [basemapStyle, setBasemapStyle] = useState(() => {
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

    const handleBasemapChange = (styleKey) => {
        setBasemapStyle(styleKey);
        try {
            localStorage.setItem(BASEMAP_STORAGE_KEY, styleKey);
        } catch (e) {
            console.warn("Could not save basemapStyle to localStorage", e);
        }
    };

    const currentMapStyle = useMemo(() => {
        if (isOffline) return offlineStyle;
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

    const [radius, setRadius] = useState(50.0);
    const [wells, setWells] = useState([]);
    const [isCollapsed, setIsCollapsed] = useState(false);
    
    // Draggable state for the search box
    const [position, setPosition] = useState({ x: 24, y: 150 }); // Start a bit lower to avoid App.jsx status cards
    const [isDragging, setIsDragging] = useState(false);
    const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
    const [internal3DOpen, setInternal3DOpen] = useState(false);
    const is3DViewerOpen = external3DOpen !== undefined ? external3DOpen : internal3DOpen;
    const setIs3DViewerOpen = setExternal3DOpen || setInternal3DOpen;

    // The coordinates the radius search is centered around
    const [searchCoords, setSearchCoords] = useState({ lat: 27.415, lon: 95.185 });

    useEffect(() => {
        // Fetch nearby wells based on searchCoords and radius
        const fetchNearby = async () => {
            try {
                const params = {
                    lat: searchCoords.lat,
                    lon: searchCoords.lon,
                    radius_km: radius
                };
                if (selectedRegion && selectedRegion !== 'all') {
                    params.region = selectedRegion;
                }
                const response = await axios.get(`${API_BASE}/api/wells/nearby`, { params });
                setWells(response.data);
            } catch (err) {
                console.error("Failed to fetch nearby wells:", err);
            }
        };
        fetchNearby();
    }, [searchCoords, radius, selectedRegion]);

    // Recenter map when region changes
    useEffect(() => {
        if (selectedRegion && selectedRegion !== 'all') {
            const config = REGIONS_CONFIG[selectedRegion];
            if (config) {
                setSearchCoords({ lat: config.center[0], lon: config.center[1] });
                setRadius(config.zoom === 8 ? 500 : 50);
            }
        }
    }, [selectedRegion]);

    const circleGeoJSON = useMemo(() => {
        return createGeoJSONCircle([searchCoords.lon, searchCoords.lat], radius);
    }, [searchCoords, radius]);

    const fitCircleBounds = React.useCallback((coords = searchCoords, r = radius, duration = 400) => {
        const map = mapRef.current?.getMap ? mapRef.current.getMap() : mapRef.current;
        if (!map) return;
        const bounds = getCircleBoundingBox([coords.lon, coords.lat], r);
        try {
            map.fitBounds(bounds, {
                padding: 60,
                duration,
                maxZoom: 15
            });
        } catch (err) {
            console.warn("fitBounds failed:", err);
        }
    }, [searchCoords, radius]);

    // Automatically fit map view to the circle bounds whenever searchCoords or radius changes
    useEffect(() => {
        const map = mapRef.current?.getMap ? mapRef.current.getMap() : mapRef.current;
        if (!map) return;

        const bounds = getCircleBoundingBox([searchCoords.lon, searchCoords.lat], radius);
        try {
            map.fitBounds(bounds, {
                padding: 60,
                duration: 400,
                maxZoom: 15
            });
        } catch (err) {
            console.warn("fitBounds failed:", err);
        }
    }, [searchCoords.lat, searchCoords.lon, radius]);

    const setAsActiveRig = () => {
        const active = wells.find(w => w.well_id === activeWellId);
        if (active && active.surface_location) {
            const newCoords = {
                lat: active.surface_location.lat,
                lon: active.surface_location.lon
            };
            setSearchCoords(newCoords);
            fitCircleBounds(newCoords, radius, 600);
        }
    };

    const handlePointerDown = (e) => {
        // Prevent dragging if interacting with inputs or buttons
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

    const mapRef = React.useRef(null);
    useEffect(() => {
        if (mapRef.current) {
            window.debugMap = mapRef.current.getMap ? mapRef.current.getMap() : mapRef.current;
        }
    }, [mapRef.current]);

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
            map.on('style.load', () => {
                hideBorders(map);
            });
        }
        // Initial fit to ensure default 50km radius circle is fully visible with padding
        const bounds = getCircleBoundingBox([searchCoords.lon, searchCoords.lat], radius);
        try {
            map.fitBounds(bounds, { padding: 60, duration: 400, maxZoom: 15 });
        } catch (err) {
            console.warn("fitBounds on load failed:", err);
        }
    };

    return (
        <div className="relative w-full h-full flex-1">
            {/* Basemap Style Switcher Control */}
            <div 
                id="basemap-style-switcher"
                className="absolute top-3.5 left-3.5 z-20 flex items-center bg-[#0c1322]/85 backdrop-blur-md border border-slate-700/80 rounded-xl p-1 shadow-glass space-x-1 select-none"
                role="group"
                aria-label="Basemap style selection"
            >
                {BASEMAP_OPTIONS.map(opt => {
                    const isSelected = basemapStyle === opt.id;
                    const Icon = opt.icon;
                    return (
                        <button
                            key={opt.id}
                            type="button"
                            id={`basemap-btn-${opt.id}`}
                            onClick={() => handleBasemapChange(opt.id)}
                            title={isOffline ? `${opt.label} (Offline mode active - serving local tiles)` : `Switch to ${opt.label} basemap`}
                            className={`
                                flex items-center space-x-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium transition-all
                                ${isSelected 
                                    ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-sm font-semibold' 
                                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 border border-transparent'}
                                ${isOffline ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
                            `}
                            disabled={isOffline}
                        >
                            <Icon size={13} className={isSelected ? 'text-cyan-400' : 'text-slate-400'} />
                            <span>{opt.label}</span>
                        </button>
                    );
                })}
                {isOffline && (
                    <span className="text-[10px] text-amber-400/90 font-mono px-1.5 py-0.5 bg-amber-500/10 border border-amber-500/20 rounded">
                        Offline
                    </span>
                )}
            </div>

            <Map
                mapLib={maplibregl}
                ref={mapRef}
                onLoad={handleMapLoad}
                {...viewState}
                onMove={evt => setViewState(evt.viewState)}
                onMoveEnd={evt => setViewState(evt.viewState)}
                mapStyle={currentMapStyle}
                style={{ width: '100%', height: '100%' }}
            >
                <NavigationControl position="bottom-right" />

                {/* Radius Polygon - Fill */}
                <Source id="radius-source-fill" type="geojson" data={circleGeoJSON}>
                    <Layer 
                        id="radius-fill" 
                        type="fill" 
                        paint={{
                            'fill-color': '#0284C7',
                            'fill-opacity': 0.35
                        }} 
                    />
                </Source>

                {/* Radius Polygon - Line */}
                <Source id="radius-source-line" type="geojson" data={circleGeoJSON}>
                    <Layer 
                        id="radius-line" 
                        type="line" 
                        paint={{
                            'line-color': '#1E3A8A',
                            'line-width': 3
                        }} 
                    />
                </Source>

                {/* Markers */}
                {wells.map(well => {
                    const loc = well.surface_location;
                    if (!loc || typeof loc === 'string') return null;
                    
                    const isActive = well.well_id === activeWellId;
                    
                    return (
                        <Marker 
                            key={well.id} 
                            longitude={loc.lon} 
                            latitude={loc.lat}
                            anchor="center"
                            onClick={e => {
                                e.originalEvent.stopPropagation();
                                onSelectWell(well.well_id);
                            }}
                        >
                            <div className="relative flex items-center justify-center cursor-pointer group">
                                {isActive && (
                                    <>
                                        <span className="animate-ping absolute inline-flex h-9 w-9 rounded-full bg-status-active opacity-60"></span>
                                        <span className="absolute inline-flex h-6 w-6 rounded-full bg-status-active/30 border border-status-active/50"></span>
                                    </>
                                )}
                                <div className={`
                                    relative z-10 rounded-full border-2 shadow-lg transition-transform group-hover:scale-125 flex items-center justify-center
                                    ${isActive 
                                        ? 'bg-status-active border-white w-5 h-5 shadow-glow-emerald' 
                                        : 'bg-slate-400 hover:bg-cyan-400 border-slate-900 w-3.5 h-3.5'}
                                `}>
                                    {isActive && <div className="w-1.5 h-1.5 rounded-full bg-slate-950"></div>}
                                </div>
                                
                                {/* Tooltip */}
                                <div className="absolute top-7 opacity-0 group-hover:opacity-100 transition-all duration-200 bg-[#0c1322]/95 border border-slate-700 text-slate-100 text-[11px] font-mono px-2.5 py-1.5 rounded-lg shadow-xl pointer-events-none whitespace-nowrap z-50 flex items-center space-x-2 backdrop-blur-md">
                                    <span className={`w-1.5 h-1.5 rounded-full ${isActive ? 'bg-status-active' : 'bg-cyan-400'}`}></span>
                                    <span className="font-semibold">{well.well_id}</span>
                                    {isActive && <span className="text-[10px] text-emerald-400 font-sans font-bold">(ACTIVE)</span>}
                                    <SourceTag source={well.data_source} compact={true} />
                                </div>
                            </div>
                        </Marker>
                    );
                })}
            </Map>

            {/* Floating Control Card (Draggable / Mobile Responsive) */}
            <div 
                className={`absolute w-80 max-w-[calc(100vw-32px)] glass-panel border border-slate-750 shadow-glass rounded-2xl p-3.5 sm:p-4 z-10 transition-all ${isDragging ? 'cursor-grabbing' : 'cursor-grab'}`}
                style={{ top: Math.max(60, position.y), left: Math.max(12, position.x), touchAction: 'none' }}
                onPointerDown={handlePointerDown}
                onPointerMove={handlePointerMove}
                onPointerUp={handlePointerUp}
                onPointerCancel={handlePointerUp}
            >
                <div className="flex items-center justify-between mb-2">
                    <h3 className="font-display font-bold text-slate-100 flex items-center text-xs sm:text-sm">
                        <Target size={16} className="mr-2 text-cyan-400" />
                        Offset Search Horizon
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
                        <div>
                            <div className="flex justify-between text-xs font-mono text-slate-400 mb-1.5">
                                <span>Radial Buffer:</span>
                                <span className="text-cyan-400 font-bold">{radius.toFixed(1)} km</span>
                            </div>
                            <input 
                                type="range" 
                                min="5.0" 
                                max="200.0" 
                                step="5.0" 
                                value={radius}
                                onChange={(e) => setRadius(parseFloat(e.target.value))}
                                className="w-full accent-cyan-500 bg-slate-800 rounded-lg appearance-none cursor-pointer h-1.5"
                            />
                        </div>

                        <button 
                            onClick={setAsActiveRig}
                            className="w-full bg-slate-850 hover:bg-slate-800 active:bg-slate-750 text-slate-200 text-xs font-medium py-2.5 rounded-xl transition-colors border border-slate-700/80 flex items-center justify-center min-h-[40px] shadow-sm"
                        >
                            Set Selected as Active Rig
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
