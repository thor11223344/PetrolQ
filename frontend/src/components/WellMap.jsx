import React, { useState, useEffect, useMemo } from 'react';
import { Target, AlertTriangle, Box } from 'lucide-react';
import Map, { Marker, NavigationControl, Source, Layer } from 'react-map-gl/maplibre';
import axios from 'axios';
import { API_BASE } from '../lib/api';
import 'maplibre-gl/dist/maplibre-gl.css';
import Trajectory3DViewer from './Trajectory3DViewer';

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

const osmStyle = {
    version: 8,
    sources: {
        'osm-tiles': {
            type: 'raster',
            tiles: [
                'https://a.tile.openstreetmap.org/{z}/{x}/{y}.png',
                'https://b.tile.openstreetmap.org/{z}/{x}/{y}.png',
                'https://c.tile.openstreetmap.org/{z}/{x}/{y}.png'
            ],
            tileSize: 256,
            attribution: '&copy; OpenStreetMap contributors'
        }
    },
    layers: [{
        id: 'osm-tiles-layer',
        type: 'raster',
        source: 'osm-tiles',
        minzoom: 0,
        maxzoom: 19
    }]
};

export default function WellMap({ activeWellId, onSelectWell, currentDepth, activeScenario }) {
    const [viewState, setViewState] = useState({
        longitude: 95.185,
        latitude: 27.415,
        zoom: 11,
        pitch: 30
    });

    const [radius, setRadius] = useState(50.0);
    const [wells, setWells] = useState([]);
    
    // Draggable state for the search box
    const [position, setPosition] = useState({ x: 24, y: 150 }); // Start a bit lower to avoid App.jsx status cards
    const [isDragging, setIsDragging] = useState(false);
    const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
    const [is3DViewerOpen, setIs3DViewerOpen] = useState(false);

    // The coordinates the radius search is centered around
    const [searchCoords, setSearchCoords] = useState({ lat: 27.415, lon: 95.185 });

    useEffect(() => {
        // Fetch nearby wells based on searchCoords and radius
        const fetchNearby = async () => {
            try {
                const response = await axios.get(`${API_BASE}/api/wells/nearby`, {
                    params: {
                        lat: searchCoords.lat,
                        lon: searchCoords.lon,
                        radius_km: radius
                    }
                });
                setWells(response.data);
            } catch (err) {
                console.error("Failed to fetch nearby wells:", err);
            }
        };
        fetchNearby();
    }, [searchCoords, radius]);

    const circleGeoJSON = useMemo(() => {
        return createGeoJSONCircle([searchCoords.lon, searchCoords.lat], radius);
    }, [searchCoords, radius]);

    const setAsActiveRig = () => {
        const active = wells.find(w => w.well_id === activeWellId);
        if (active && active.surface_location) {
            setSearchCoords({
                lat: active.surface_location.lat,
                lon: active.surface_location.lon
            });
            setViewState(prev => ({
                ...prev,
                longitude: active.surface_location.lon,
                latitude: active.surface_location.lat
            }));
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

    return (
        <div className="relative w-full h-full flex-1">
            <Map
                {...viewState}
                onMove={evt => setViewState(evt.viewState)}
                mapStyle={isOffline ? offlineStyle : osmStyle}
                style={{ width: '100%', height: '100%' }}
            >
                <NavigationControl position="bottom-right" />

                {/* Radius Polygon */}
                <Source id="radius-source" type="geojson" data={circleGeoJSON} />
                
                <Layer 
                    id="radius-fill" 
                    type="fill" 
                    source="radius-source"
                    paint={{
                        'fill-color': '#0284C7',
                        'fill-opacity': 0.35
                    }} 
                />
                
                <Layer 
                    id="radius-line" 
                    type="line" 
                    source="radius-source"
                    paint={{
                        'line-color': '#1E3A8A',
                        'line-width': 3
                    }} 
                />

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
                            <div className={`relative flex items-center justify-center cursor-pointer group`}>
                                {isActive && (
                                    <span className="animate-ping absolute inline-flex h-8 w-8 rounded-full bg-status-active opacity-50"></span>
                                )}
                                <div className={`
                                    relative z-10 w-4 h-4 rounded-full border-2 shadow-lg transition-transform hover:scale-125
                                    ${isActive 
                                        ? 'bg-status-active border-slate-900 w-5 h-5' 
                                        : 'bg-slate-400 border-slate-900'}
                                `}></div>
                                
                                {/* Tooltip */}
                                <div className="absolute top-6 opacity-0 group-hover:opacity-100 transition-opacity bg-slate-900 text-slate-200 text-xs px-2 py-1 rounded shadow pointer-events-none whitespace-nowrap z-50">
                                    {well.well_id}
                                </div>
                            </div>
                        </Marker>
                    );
                })}
            </Map>

            {/* Floating Control Card (Draggable) */}
            <div 
                className={`absolute w-80 bg-slate-900/90 backdrop-blur-md border border-slate-700 shadow-2xl rounded-lg p-4 z-10 ${isDragging ? 'cursor-grabbing' : 'cursor-grab'}`}
                style={{ top: position.y, left: position.x, touchAction: 'none' }}
                onPointerDown={handlePointerDown}
                onPointerMove={handlePointerMove}
                onPointerUp={handlePointerUp}
                onPointerCancel={handlePointerUp}
            >
                <div className="flex items-center justify-between mb-4 pointer-events-none">
                    <h3 className="font-semibold text-slate-200 flex items-center">
                        <Target size={16} className="mr-2 text-status-fluid" />
                        Offset Search
                    </h3>
                    <div className="bg-slate-800 px-2 py-1 rounded text-xs font-medium text-slate-300 border border-slate-700">
                        Found {wells.length} Wells
                    </div>
                </div>

                <div className="space-y-4">
                    <div>
                        <div className="flex justify-between text-xs text-slate-400 mb-1">
                            <span>Search Radius</span>
                            <span>{radius.toFixed(1)} km</span>
                        </div>
                        <input 
                            type="range" 
                            min="5.0" 
                            max="200.0" 
                            step="5.0" 
                            value={radius}
                            onChange={(e) => setRadius(parseFloat(e.target.value))}
                            className="w-full accent-status-fluid bg-slate-800 rounded-lg appearance-none cursor-pointer h-1.5"
                        />
                    </div>

                    <button 
                        onClick={setAsActiveRig}
                        className="w-full bg-slate-800 hover:bg-slate-700 text-slate-200 text-sm font-medium py-2 rounded transition-colors border border-slate-700 flex items-center justify-center"
                    >
                        Set Selected as Active Rig Location
                    </button>
                    
                    <button 
                        onClick={() => setIs3DViewerOpen(true)}
                        className="w-full bg-status-fluid/20 hover:bg-status-fluid/30 text-status-fluid text-sm font-medium py-2 rounded transition-colors border border-status-fluid/30 flex items-center justify-center mt-2"
                    >
                        <Box size={16} className="mr-2" />
                        View 3D Subsurface
                    </button>
                </div>
            </div>

            <Trajectory3DViewer 
                isOpen={is3DViewerOpen} 
                onClose={() => setIs3DViewerOpen(false)} 
                activeWellId={activeWellId} 
                offsetWells={wells} 
                currentDepth={currentDepth}
                activeScenario={activeScenario}
            />
        </div>
    );
}
