import React from 'react';
import { Database, ShieldCheck, Cpu } from 'lucide-react';

/**
 * Reusable Data Provenance Badge component.
 * Displays verifiable data origin with explanatory tooltips:
 * - "volve_relabeled": Equinor Volve Open Data (North Sea), calibrated to Upper Assam basin
 * - "force2020_relabeled": FORCE 2020 ML Competition Log Benchmark
 * - "synthetic": Regional Geomechanical Synthetic Calibration
 */
const SOURCE_CONFIGS = {
  volve_relabeled: {
    label: "Volve (Relabeled)",
    shortLabel: "Volve",
    bgColor: "bg-amber-500/15",
    textColor: "text-amber-300",
    borderColor: "border-amber-500/40",
    dotColor: "bg-amber-400",
    icon: Database,
    tooltip: "Data Provenance: Derived from Equinor's Volve open field dataset (North Sea, UK/Norwegian sector), relabeled and calibrated to Upper Assam basin lithology & stress regimes."
  },
  force2020_relabeled: {
    label: "FORCE 2020",
    shortLabel: "FORCE20",
    bgColor: "bg-cyan-500/15",
    textColor: "text-cyan-300",
    borderColor: "border-cyan-500/40",
    dotColor: "bg-cyan-400",
    icon: ShieldCheck,
    tooltip: "Data Provenance: Derived from the industry-standard FORCE 2020 Machine Learning Competition well log benchmark, calibrated to regional sandstone/shale sequences."
  },
  synthetic: {
    label: "Synthetic Calibrated",
    shortLabel: "Synthetic",
    bgColor: "bg-purple-500/15",
    textColor: "text-purple-300",
    borderColor: "border-purple-500/40",
    dotColor: "bg-purple-400",
    icon: Cpu,
    tooltip: "Data Provenance: Synthetically calibrated geomechanical model based on published Eaton / Teale physics rules for Upper Assam overpressure zones."
  }
};

const SourceTag = ({ source, compact = false, showIcon = true, className = "" }) => {
  // Normalize source key
  const normalizedKey = (source || "").toLowerCase().trim();
  let config = SOURCE_CONFIGS[normalizedKey];

  if (!config) {
    // Fallback detection
    if (normalizedKey.includes("force")) {
      config = SOURCE_CONFIGS.force2020_relabeled;
    } else if (normalizedKey.includes("synth")) {
      config = SOURCE_CONFIGS.synthetic;
    } else {
      config = SOURCE_CONFIGS.volve_relabeled;
    }
  }

  const Icon = config.icon;

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full border text-[10px] font-mono font-medium tracking-tight transition-all duration-150 cursor-help select-none ${config.bgColor} ${config.textColor} ${config.borderColor} ${className}`}
      title={config.tooltip}
    >
      {showIcon && <Icon size={10} className="shrink-0 opacity-80" />}
      <span className={`w-1.5 h-1.5 rounded-full ${config.dotColor} shrink-0`}></span>
      <span>{compact ? config.shortLabel : config.label}</span>
    </span>
  );
};

export default SourceTag;
