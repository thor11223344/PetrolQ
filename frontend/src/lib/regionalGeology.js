// Configuration for regional geology, stratigraphy, and hazard mappings across India

export const REGIONS_CONFIG = {
  all: {
    id: "all",
    name: "Pan-India Portfolio",
    center: [22.5, 82.5], // Geographic center of India
    zoom: 4.8,
    badgeColor: "bg-cyan-950/60 text-cyan-300 border-cyan-500/30",
    markerColor: "#06B6D4",
    description: "Pan-India operational overview covering Upper Assam Shelf, Rajasthan Basin, KG Deepwater, and Mizoram Fold Belt.",
    defaultWell: "OIL-BAGHJAN-1"
  },
  assam: {
    id: "assam",
    name: "Upper Assam Shelf",
    center: [27.4, 95.2],
    zoom: 9.5,
    badgeColor: "bg-emerald-950/60 text-emerald-300 border-emerald-500/30",
    markerColor: "#10B981",
    description: "Mature oilfield with severe thief-bed losses in Tipam sands and high-pressure gas kicks in Barail formation.",
    layers: [
      { from: 0, to: 1450, color: "#EAB308", label: "Tipam Sandstone", problemDescription: "Freshwater permeable sand reservoir, severe thief-bed mud loss", hazardType: "lost_circulation", severity: "high" },
      { from: 1450, to: 2000, color: "#8B4513", label: "Girujan Clay", problemDescription: "Sloughing/caving shale & tight hole", hazardType: "stuck_pipe", severity: "medium" },
      { from: 2000, to: 2400, color: "#F97316", label: "Barail Formation", problemDescription: "Overpressured sand-shale (Known Kick Zone & differential sticking)", hazardType: "gas_kick", severity: "critical" },
      { from: 2400, to: 3500, color: "#A855F7", label: "Kopili Formation", problemDescription: "Deep marine shale transition, swelling reactive shale & packoff", hazardType: "stuck_pipe", severity: "high" }
    ],
    defaultWell: "OIL-BAGHJAN-1"
  },
  rajasthan: {
    id: "rajasthan",
    name: "Rajasthan Basin",
    center: [27.6, 71.4],
    zoom: 8.0,
    badgeColor: "bg-amber-950/60 text-amber-300 border-amber-500/30",
    markerColor: "#F59E0B",
    description: "Desert basin with heavy oil, severe quartz sand abrasion, and massive lost circulation in Bilara carbonates.",
    layers: [
      { from: 0, to: 1200, color: "#FCD34D", label: "Pariwar Formation", problemDescription: "Sand abrasion & severe filtration loss", hazardType: "wear", severity: "medium" },
      { from: 1200, to: 1800, color: "#9CA3AF", label: "Baisakhi Formation", problemDescription: "Tight hole & overpull risk", hazardType: "stuck_pipe", severity: "high" },
      { from: 1800, to: 2300, color: "#D97706", label: "Jodhpur Sandstone", problemDescription: "Heavy oil viscous drag & differential sticking", hazardType: "stuck_pipe", severity: "high" },
      { from: 2300, to: 3500, color: "#94A3B8", label: "Bilara Carbonates", problemDescription: "Massive cavernous lost circulation & extreme torque vibration", hazardType: "lost_circulation", severity: "critical" }
    ],
    defaultWell: "OIL-RAJ-BAGHEWALA-1"
  },
  kg: {
    id: "kg",
    name: "KG Deepwater",
    center: [16.35, 82.35],
    zoom: 8.5,
    badgeColor: "bg-sky-950/60 text-sky-300 border-sky-500/30",
    markerColor: "#0284C7",
    description: "Offshore deepwater basin with Shallow Water Flow, gumbo shale bit balling, and HPHT narrow pore-pressure margin.",
    layers: [
      { from: 0, to: 800, color: "#38BDF8", label: "Shallow Marine Sediments", problemDescription: "Shallow Water Flow / gas hydrates / seafloor slumping", hazardType: "gas_kick", severity: "high" },
      { from: 800, to: 1800, color: "#3F6212", label: "Godavari Gumbo", problemDescription: "Gumbo bit balling & flowline plugging", hazardType: "stuck_pipe", severity: "high" },
      { from: 1800, to: 3200, color: "#DC2626", label: "Ravva Formation", problemDescription: "Narrow PP-FG safe drilling window & rapid gas influx", hazardType: "gas_kick", severity: "critical" },
      { from: 3200, to: 4500, color: "#7C3AED", label: "Cretaceous Basement", problemDescription: "HPHT overpressures & high temperature thermal degradation", hazardType: "gas_kick", severity: "critical" }
    ],
    defaultWell: "OIL-KG-DEEPWATER-1"
  },
  mizoram: {
    id: "mizoram",
    name: "Mizoram Fold Belt",
    center: [23.72, 92.70],
    zoom: 8.5,
    badgeColor: "bg-purple-950/60 text-purple-300 border-purple-500/30",
    markerColor: "#8B5CF6",
    description: "Tectonically active fold belt with intense horizontal tectonic stress, 45°-60° dipping beds, and catastrophic stuck pipe.",
    layers: [
      { from: 0, to: 1500, color: "#F59E0B", label: "Bokabil Formation", problemDescription: "Tectonic borehole ovalization & spalling", hazardType: "stuck_pipe", severity: "medium" },
      { from: 1500, to: 2500, color: "#B45309", label: "Upper Bhuban", problemDescription: "High horizontal tectonic stress breakout", hazardType: "stuck_pipe", severity: "high" },
      { from: 2500, to: 3400, color: "#78350F", label: "Middle Bhuban", problemDescription: "Steeply dipping bedding-plane packoff & catastrophic stuck pipe", hazardType: "stuck_pipe", severity: "critical" },
      { from: 3400, to: 4500, color: "#475569", label: "Disang Flysch", problemDescription: "Tectonic crushed rock overpressure & sudden wellbore collapse", hazardType: "gas_kick", severity: "high" }
    ],
    defaultWell: "OIL-MZ-AIZAWL-1"
  }
};

export const getRegionIdFromWellId = (wellId) => {
  if (!wellId) return "assam";
  if (wellId.includes("OIL-RAJ")) return "rajasthan";
  if (wellId.includes("OIL-KG")) return "kg";
  if (wellId.includes("OIL-MZ")) return "mizoram";
  return "assam";
};

export const getRegionalGeoLayers = (wellId, selectedRegion) => {
  let regionKey = selectedRegion;
  
  if (!regionKey || regionKey === 'all') {
    regionKey = getRegionIdFromWellId(wellId);
  }
  
  const regionConfig = REGIONS_CONFIG[regionKey];
  return regionConfig?.layers || REGIONS_CONFIG.assam.layers;
};

export const getRegionBadge = (wellId, selectedRegion) => {
  let regionKey = selectedRegion;
  if (!regionKey || regionKey === 'all') {
    regionKey = getRegionIdFromWellId(wellId);
  }
  return REGIONS_CONFIG[regionKey] || REGIONS_CONFIG.assam;
};
