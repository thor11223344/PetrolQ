import React from 'react';
import { ShieldCheck, Info, X, Cpu, Database, BookOpen, ExternalLink, CheckCircle2, AlertCircle, MapPin } from 'lucide-react';
import SourceTag from './SourceTag';

const DataTransparencyModal = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  return (
    <div 
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-3 sm:p-4 animate-in fade-in duration-200"
      onClick={onClose}
    >
      <div 
        className="bg-slate-900 border border-slate-700/80 w-full max-w-2xl rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[92vh] animate-in zoom-in-95 duration-150"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div className="px-5 py-4 bg-slate-950 border-b border-slate-800 flex justify-between items-center">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-cyan-500/10 rounded-xl border border-cyan-500/20 text-cyan-400">
              <ShieldCheck size={20} />
            </div>
            <div>
              <h3 className="font-display font-bold text-white text-base">
                Data & Methodology Disclosure
              </h3>
              <p className="text-xs text-slate-400">
                Transparent technical basis, physics formulations, and data origin
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
            aria-label="Close"
          >
            <X size={18} />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-5 overflow-y-auto space-y-4 custom-scrollbar">
          
          {/* Section 1: Physics & Engineering */}
          <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800/90 space-y-2 hover:border-cyan-500/30 transition">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <BookOpen size={16} className="text-cyan-400" />
                <h4 className="text-xs font-bold uppercase tracking-wider text-cyan-300 font-mono">
                  Physics & Engineering Foundations
                </h4>
              </div>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-300 border border-cyan-500/30">
                80% Decision Weight
              </span>
            </div>
            <p className="text-xs text-slate-200 leading-relaxed font-sans">
              <strong className="text-white">Genuine published methods:</strong> Eaton's pore pressure/fracture gradient method (1972), Teale's Mechanical Specific Energy (1965), and Jorden & Shirley's d-exponent (1966) with Rehm & McClendon mud-weight normalization (1971).
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 pt-1 text-[11px] font-mono">
              <div className="p-2 rounded bg-slate-900 border border-slate-800 text-slate-300">
                <span className="text-cyan-400 block font-bold">Eaton (1972)</span>
                <span>N = 3.0 acoustic exponent</span>
              </div>
              <div className="p-2 rounded bg-slate-900 border border-slate-800 text-slate-300">
                <span className="text-emerald-400 block font-bold">Teale (1965)</span>
                <span>MSE with η = 0.35 factor</span>
              </div>
              <div className="p-2 rounded bg-slate-900 border border-slate-800 text-slate-300">
                <span className="text-amber-400 block font-bold">d-exponent</span>
                <span>Jorden-Shirley + Rehm</span>
              </div>
            </div>
          </div>

          {/* Section 2: Data Sources & Regional Portfolio Calibration */}
          <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800/90 space-y-3 hover:border-emerald-500/30 transition">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Database size={16} className="text-emerald-400" />
                <h4 className="text-xs font-bold uppercase tracking-wider text-emerald-300 font-mono">
                  Data Provenance & Regional Basin Coverage
                </h4>
              </div>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-300 border border-emerald-500/30">
                Basin Provenance Tagged
              </span>
            </div>

            {/* Basin Subsection A: Upper Assam */}
            <div className="p-3 rounded-lg bg-slate-900/90 border border-slate-800 space-y-1.5">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
                  <span className="text-xs font-bold text-slate-200">Upper Assam Shelf (Calibrated Baseline)</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <SourceTag source="volve_relabeled" compact={true} />
                  <SourceTag source="force2020_relabeled" compact={true} />
                </div>
              </div>
              <p className="text-xs text-slate-300 leading-relaxed font-sans">
                <strong className="text-white">Volve open field dataset</strong> (Equinor, North Sea) and <strong className="text-white">FORCE 2020</strong> ML competition log benchmark, relabeled and adapted to Upper Assam basin lithology. Synthetic sonic-log inputs calibrated with Eaton/Teale formulas for plausible pressure signatures.
              </p>
              <div className="flex items-center space-x-2 text-[11px] text-slate-400 pt-0.5">
                <CheckCircle2 size={13} className="text-emerald-400 shrink-0" />
                <span>Horizons mapped: Tipam Sandstone, Barail Kick Horizon, Kopili Shale.</span>
              </div>
            </div>

            {/* Basin Subsection B: Multi-Region Expansion */}
            <div className="p-3 rounded-lg bg-rose-950/20 border border-rose-500/30 space-y-1.5">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <AlertCircle size={14} className="text-rose-400" />
                  <span className="text-xs font-bold text-rose-200">Rajasthan, KG Deepwater & Mizoram</span>
                </div>
                <SourceTag source="illustrative_uncalibrated" compact={true} />
              </div>
              <p className="text-xs text-rose-100/90 leading-relaxed font-sans">
                <strong className="text-white font-semibold">Illustrative / Not Yet Calibrated:</strong> Formations like Jodhpur Sandstone, Bilara Carbonates, Godavari Gumbo, Ravva, Bokabil, and Bhuban are genuine stratigraphic units in Indian geology. However, all baseline telemetry values, depth horizons, wellhead coordinates, and directional borehole trajectories for these three regions are <strong>purely synthetic, illustrative mock data authored to demonstrate multi-region software architecture and UI scalability</strong>, with NO real sensor log dataset or Volve-analog data basis.
              </p>
              <div className="text-[10px] font-mono text-rose-300/80 bg-rose-500/10 px-2 py-1 rounded border border-rose-500/20">
                Status: Architecture Demonstration Only • No Real or Volve-Analog Telemetry Basis
              </div>
            </div>
          </div>

          {/* Section 3: Machine Learning & Hybrid Architecture */}
          <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800/90 space-y-2 hover:border-purple-500/30 transition">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Cpu size={16} className="text-purple-400" />
                <h4 className="text-xs font-bold uppercase tracking-wider text-purple-300 font-mono">
                  Machine Learning Architecture
                </h4>
              </div>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-purple-500/10 text-purple-300 border border-purple-500/30">
                20% Signal Weight
              </span>
            </div>
            <p className="text-xs text-slate-200 leading-relaxed font-sans">
              <strong className="text-white">LightGBM multi-class classifier</strong>, verified to contribute a genuine 20% weighted signal alongside deterministic physics rules (80% weight) for safety-critical hazard scoring.
            </p>
            {/* 80 / 20 Weight Distribution Visual Bar */}
            <div className="pt-2">
              <div className="flex justify-between text-[11px] font-mono text-slate-400 mb-1.5">
                <span>Deterministic Physics Rules (80%)</span>
                <span>LightGBM ML Classifier (20%)</span>
              </div>
              <div className="w-full h-3 bg-slate-800 rounded-full overflow-hidden flex">
                <div className="h-full bg-cyan-500 shadow-glow-cyan" style={{ width: '80%' }} title="80% Deterministic Physics"></div>
                <div className="h-full bg-purple-500 shadow-glow-purple" style={{ width: '20%' }} title="20% Machine Learning Signal"></div>
              </div>
            </div>
          </div>

        </div>

        {/* Modal Footer */}
        <div className="px-5 py-3 bg-slate-950 border-t border-slate-800 flex justify-between items-center text-xs text-slate-400">
          <span className="font-mono text-[11px]">OIL India SIH 2026 Submission</span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-white font-medium transition"
          >
            Acknowledge & Close
          </button>
        </div>
      </div>
    </div>
  );
};

export default DataTransparencyModal;
