// Configuration for regional geology, stratigraphy, and hazard mappings

export const REGIONS_CONFIG = {
  assam: {
    id: "assam",
    name: "Upper Assam Shelf",
    center: [27.4, 95.2],
    zoom: 9,
    badgeColor: "bg-green-100 text-green-800 border-green-200",
    description: "Mature oilfield with severe thief-bed losses and high-pressure gas kicks.",
    layers: [
      { from: 0, to: 1450, color: "#EAB308", label: "Tipam Sandstone", problemDescription: "Freshwater permeable sand reservoir, severe thief-bed mud loss", hazardType: "lost_circulation", severity: "high" },
      { from: 1450, to: 2000, color: "#8B4513", label: "Girujan Clay", problemDescription: "Sloughing/caving shale", hazardType: "stuck_pipe", severity: "medium" },
      { from: 2000, to: 2400, color: "#F97316", label: "Barail Formation", problemDescription: "Overpressured sand-shale (Known Kick Zone & differential sticking)", hazardType: "gas_kick", severity: "critical" },
      { from: 2400, to: 3500, color: "#A855F7", label: "Kopili Formation", problemDescription: "Deep marine shale transition, swelling reactive shale", hazardType: "stuck_pipe", severity: "high" }
    ],
    defaultWell: "OIL-BAGHJAN-1"
  },
  rajasthan: {
    id: "rajasthan",
    name: "Rajasthan Basin",
    center: [27.6, 71.4],
    zoom: 8,
    badgeColor: "bg-orange-100 text-orange-800 border-orange-200",
    description: "Desert basin with heavy oil, sand abrasion, and massive lost circulation.",
    layers: [
      { from: 0, to: 1200, color: "#FCD34D", label: "Pariwar Formation", problemDescription: "Sand abrasion & filtration loss", hazardType: "wear", severity: "medium" },
      { from: 1200, to: 1800, color: "#9CA3AF", label: "Baisakhi Formation", problemDescription: "Tight hole", hazardType: "stuck_pipe", severity: "high" },
      { from: 1800, to: 2300, color: "#D97706", label: "Jodhpur Sandstone", problemDescription: "Heavy oil viscous drag & differential sticking", hazardType: "stuck_pipe", severity: "high" },
      { from: 2300, to: 3500, color: "#94A3B8", label: "Bilara Carbonates", problemDescription: "Massive cavernous lost circulation & torque vibration", hazardType: "lost_circulation", severity: "critical" }
    ],
    defaultWell: "OIL-RAJ-BAGHEWALA-1"
  },
  kg: {
    id: "kg",
    name: "KG Deepwater",
    center: [16.25, 82.40],
    zoom: 8,
    badgeColor: "bg-blue-100 text-blue-800 border-blue-200",
    description: "Offshore basin with Shallow Water Flow, gumbo shale, and HPHT overpressures.",
    layers: [
      { from: 0, to: 800, color: "#38BDF8", label: "Shallow Marine Sediments", problemDescription: "Shallow Water Flow / gas hydrates", hazardType: "gas_kick", severity: "high" },
      { from: 800, to: 1800, color: "#3F6212", label: "Godavari Gumbo", problemDescription: "Gumbo bit balling & plugging", hazardType: "stuck_pipe", severity: "high" },
      { from: 1800, to: 3200, color: "#DC2626", label: "Ravva Formation", problemDescription: "Narrow PP-FG window & rapid gas influx", hazardType: "gas_kick", severity: "critical" },
      { from: 3200, to: 4500, color: "#7C3AED", label: "Cretaceous", problemDescription: "HPHT overpressures", hazardType: "gas_kick", severity: "critical" }
    ],
    defaultWell: "OIL-KG-DEEPWATER-1"
  },
  mizoram: {
    id: "mizoram",
    name: "Mizoram Fold Belt",
    center: [23.72, 92.70],
    zoom: 8,
    badgeColor: "bg-slate-100 text-slate-800 border-slate-200",
    description: "Tectonically active fold belt with high horizontal stress and stuck pipe risks.",
    layers: [
      { from: 0, to: 1500, color: "#F59E0B", label: "Bokabil Formation", problemDescription: "Tectonic ovalization", hazardType: "stuck_pipe", severity: "medium" },
      { from: 1500, to: 2500, color: "#B45309", label: "Upper Bhuban", problemDescription: "High horizontal stress breakout", hazardType: "stuck_pipe", severity: "high" },
      { from: 2500, to: 3400, color: "#78350F", label: "Middle Bhuban", problemDescription: "Steeply dipping bedding-plane packoff & catastrophic stuck pipe", hazardType: "stuck_pipe", severity: "critical" },
      { from: 3400, to: 4500, color: "#475569", label: "Disang Flysch", problemDescription: "Tectonic crushed rock overpressure", hazardType: "gas_kick", severity: "high" }
    ],
    defaultWell: "OIL-MZ-AIZAWL-1"
  }
};

export const getRegionalGeoLayers = (wellId, selectedRegion) => {
  let regionKey = selectedRegion;
  
  if (!regionKey || regionKey === 'all') {
    if (wellId?.includes("OIL-RAJ")) regionKey = "rajasthan";
    else if (wellId?.includes("OIL-KG")) regionKey = "kg";
    else if (wellId?.includes("OIL-MZ")) regionKey = "mizoram";
    else regionKey = "assam";
  }
  
  const regionConfig = REGIONS_CONFIG[regionKey];
  return regionConfig ? regionConfig.layers : REGIONS_CONFIG.assam.layers;
};

export const getRegionBadge = (wellId, selectedRegion) => {
    let regionKey = selectedRegion;
    if (!regionKey || regionKey === 'all') {
      if (wellId?.includes("OIL-RAJ")) regionKey = "rajasthan";
      else if (wellId?.includes("OIL-KG")) regionKey = "kg";
      else if (wellId?.includes("OIL-MZ")) regionKey = "mizoram";
      else regionKey = "assam";
    }
    return REGIONS_CONFIG[regionKey] || REGIONS_CONFIG.assam;
};
