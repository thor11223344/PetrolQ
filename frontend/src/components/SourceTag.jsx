import React from 'react';
import { Database, ShieldCheck, Cpu, AlertCircle } from 'lucide-react';

/**
 * Reusable Data Provenance Badge component.
 * Displays verifiable data origin with explanatory tooltips:
 * - "volve_relabeled": Equinor Volve Open Data (North Sea), calibrated to Upper Assam basin
 * - "force2020_relabeled": FORCE 2020 ML Competition Log Benchmark
 * - "synthetic": Regional Geomechanical Synthetic Calibration
 * - "illustrative_uncalibrated": Illustrative / Not Yet Calibrated — architecture demonstration only, no real or Volve-analog data basis
 */
export const SOURCE_CONFIGS = {
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
  },
  regional_calibrated: {
    label: "Regionally Calibrated",
    shortLabel: "Calibrated",
    bgColor: "bg-emerald-500/15",
    textColor: "text-emerald-300",
    borderColor: "border-emerald-500/40",
    dotColor: "bg-emerald-400",
    icon: ShieldCheck,
    tooltip: "Data Provenance: Regionally calibrated geomechanical model using basin offset logs, Eaton pore pressure, and Teale mechanical specific energy (MSE) physics rules."
  },
  illustrative_uncalibrated: {
    label: "Illustrative / Uncalibrated",
    shortLabel: "Illustrative",
    bgColor: "bg-rose-500/15",
    textColor: "text-rose-300",
    borderColor: "border-rose-500/40",
    dotColor: "bg-rose-400",
    icon: AlertCircle,
    tooltip: "Data Provenance: Illustrative / Not Yet Calibrated — architecture demonstration only, no real or Volve-analog data basis."
  }
};

/**
 * Resolves the data provenance classification key for any given well ID or raw data source label.
 */
export const getWellDataSource = (wellIdOrSource) => {
  if (!wellIdOrSource) return "volve_relabeled";
  const str = String(wellIdOrSource).toLowerCase().trim();

  // Regional expansion wells (Rajasthan, KG Deepwater, Mizoram) are illustrative only
  if (
    str.includes("raj") ||
    str.includes("baghewala") ||
    str.includes("tanot") ||
    str.includes("dandewala") ||
    str.includes("rajasthan") ||
    str.includes("jaisalmer") ||
    str.includes("kg") ||
    str.includes("deepwater") ||
    str.includes("yanam") ||
    str.includes("amalapuram") ||
    str.includes("mz") ||
    str.includes("aizawl") ||
    str.includes("mamit") ||
    str.includes("kolasib") ||
    str.includes("lunglei") ||
    str.includes("champhai") ||
    str.includes("mizoram") ||
    str.includes("illustrative") ||
    str.includes("uncalibrated")
  ) {
    return "illustrative_uncalibrated";
  }

  if (str.includes("regional_calibrated")) {
    return "regional_calibrated";
  }

  if (str.includes("nahar") || str.includes("force")) {
    return "force2020_relabeled";
  }

  if (str.includes("dikom") || str.includes("baghjan-4") || str.includes("synth")) {
    return "synthetic";
  }

  return "volve_relabeled";
};

const SourceTag = ({ source, compact = false, showIcon = true, className = "" }) => {
  const normalizedKey = getWellDataSource(source);
  const config = SOURCE_CONFIGS[normalizedKey] || SOURCE_CONFIGS.volve_relabeled;
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
