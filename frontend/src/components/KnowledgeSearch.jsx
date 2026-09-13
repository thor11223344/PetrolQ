import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { API_BASE } from '../lib/api';
import { Search, X, BookOpen, ChevronRight, Loader2, ShieldCheck } from 'lucide-react';

const KnowledgeSearch = ({ isOpen, onClose, suggestedQuery = '' }) => {
    const [query, setQuery] = useState(suggestedQuery || '');
    const [results, setResults] = useState([]);
    const [isSearching, setIsSearching] = useState(false);
    const [hasSearched, setHasSearched] = useState(false);

    useEffect(() => {
        if (suggestedQuery) {
            setQuery(suggestedQuery);
        }
    }, [suggestedQuery]);

    if (!isOpen) return null;

    const handleSearch = async (e) => {
        if (e.key === 'Enter' && query.trim() !== '') {
            setIsSearching(true);
            setHasSearched(true);
            try {
                const response = await axios.get(`${API_BASE}/api/events/search`, {
                    params: { query: query.trim(), limit: 5 }
                });
                setResults(response.data || []);
            } catch (error) {
                console.error("Search failed:", error);
                setResults([]);
            } finally {
                setIsSearching(false);
            }
        }
    };

    return (
        <div className="fixed top-14 right-0 w-full sm:w-[450px] max-w-full h-[calc(100vh-3.5rem)] bg-slate-900 border-l border-slate-700 shadow-2xl z-40 flex flex-col animate-in slide-in-from-right">
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b border-slate-800 bg-slate-900/80 backdrop-blur">
                <div className="flex items-center space-x-2 text-slate-200">
                    <BookOpen size={18} className="text-status-fluid" />
                    <h2 className="font-semibold tracking-wide">Knowledge Base</h2>
                </div>
                <button onClick={onClose} className="text-slate-500 hover:text-slate-300 transition-colors">
                    <X size={20} />
                </button>
            </div>

            {/* Search Input */}
            <div className="p-4 border-b border-slate-800 bg-slate-950/50">
                <div className="relative">
                    <Search size={16} className="absolute left-3 top-3 text-slate-500" />
                    <input 
                        type="text"
                        placeholder="Search historical incidents... (Press Enter)"
                        className="w-full bg-slate-900 border border-slate-700 rounded-md py-2 pl-9 pr-4 text-sm text-slate-200 placeholder:text-slate-500 focus:outline-none focus:border-status-fluid focus:ring-1 focus:ring-status-fluid transition-all"
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        onKeyDown={handleSearch}
                    />
                </div>
            </div>

            {/* Results Area */}
            <div className="flex-1 overflow-y-auto custom-scrollbar p-4 bg-slate-950">
                {isSearching ? (
                    <div className="flex flex-col items-center justify-center h-32 text-slate-500 space-y-3">
                        <Loader2 size={24} className="animate-spin text-status-fluid" />
                        <span className="text-sm">Searching historical records...</span>
                    </div>
                ) : hasSearched && results.length === 0 ? (
                    <div className="flex flex-col items-center justify-center h-32 text-slate-500">
                        <p className="text-sm">No historical incidents found matching your query.</p>
                    </div>
                ) : (
                    <div className="space-y-4">
                        {results.map((result, idx) => (
                            <div key={idx} className="bg-slate-900 border border-slate-800 rounded-lg p-4 hover:border-slate-700 transition-colors">
                                <div className="flex items-start justify-between mb-2">
                                    <div>
                                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-slate-800 text-slate-300 mb-2">
                                            {result.well_id} • {result.depth_tvd}m TVD
                                        </span>
                                        <h3 className="text-sm font-semibold text-slate-200">{result.event_type}</h3>
                                    </div>
                                    <div className="flex flex-col items-end gap-1.5">
                                        <div className="text-xs font-mono text-cyan-400 bg-cyan-950/60 border border-cyan-500/30 px-2 py-0.5 rounded font-bold shadow-inner">
                                            {((result.hybrid_score ?? result.similarity_score) * 100).toFixed(0)}% Match
                                        </div>
                                        {result.guardrail_verified && (
                                            <span className="inline-flex items-center space-x-1 px-1.5 py-0.5 rounded text-[10px] font-mono font-medium bg-emerald-950/80 border border-emerald-500/40 text-emerald-300">
                                                <ShieldCheck size={11} className="text-emerald-400" />
                                                <span>✓ Guardrail Verified</span>
                                            </span>
                                        )}
                                    </div>
                                </div>
                                
                                {result.root_cause && (
                                    <div className="mb-2">
                                        <span className="text-xs font-bold text-slate-500 uppercase tracking-wider block mb-1">Root Cause</span>
                                        <p className="text-sm text-slate-400">{result.root_cause}</p>
                                    </div>
                                )}
                                
                                <div>
                                    <span className="text-xs font-bold text-slate-500 uppercase tracking-wider block mb-1">Mitigation Applied</span>
                                    <div className="flex items-start space-x-2 bg-status-active/10 p-2 rounded border border-status-active/20">
                                        <ChevronRight size={14} className="text-status-active mt-0.5 shrink-0" />
                                        <p className="text-sm text-emerald-400 font-medium">{result.mitigation_applied}</p>
                                    </div>
                                </div>

                                {/* Multi-Signal Hybrid Retrieval Score Breakdown (Feature 2) */}
                                {result.score_breakdown && (
                                    <div className="mt-3 pt-2.5 border-t border-slate-800/80">
                                        <div className="flex items-center justify-between text-[10px] font-mono text-slate-400 mb-1.5">
                                            <span className="font-semibold uppercase tracking-wider text-slate-400">Multi-Signal Relevance Breakdown</span>
                                            <span className="text-cyan-400 font-bold">{((result.hybrid_score ?? result.similarity_score) * 100).toFixed(1)}% Total</span>
                                        </div>
                                        <div className="grid grid-cols-2 sm:grid-cols-3 gap-1.5 text-[10px] font-mono">
                                            <div className="bg-slate-950/80 px-2 py-1 rounded border border-slate-800 flex justify-between">
                                                <span className="text-slate-400">Formation (25%):</span>
                                                <strong className="text-cyan-300">{(result.score_breakdown.formation_match * 100).toFixed(0)}%</strong>
                                            </div>
                                            <div className="bg-slate-950/80 px-2 py-1 rounded border border-slate-800 flex justify-between">
                                                <span className="text-slate-400">Depth (25%):</span>
                                                <strong className="text-emerald-300">{(result.score_breakdown.depth_proximity * 100).toFixed(0)}%</strong>
                                            </div>
                                            <div className="bg-slate-950/80 px-2 py-1 rounded border border-slate-800 flex justify-between">
                                                <span className="text-slate-400">Type (20%):</span>
                                                <strong className="text-amber-300">{(result.score_breakdown.event_type_match * 100).toFixed(0)}%</strong>
                                            </div>
                                            <div className="bg-slate-950/80 px-2 py-1 rounded border border-slate-800 flex justify-between">
                                                <span className="text-slate-400">BM25 (15%):</span>
                                                <strong className="text-purple-300">{(result.score_breakdown.bm25 * 100).toFixed(0)}%</strong>
                                            </div>
                                            <div className="bg-slate-950/80 px-2 py-1 rounded border border-slate-800 flex justify-between">
                                                <span className="text-slate-400">Vector (15%):</span>
                                                <strong className="text-blue-300">{(result.score_breakdown.vector * 100).toFixed(0)}%</strong>
                                            </div>
                                        </div>
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                )}
                
                {!hasSearched && (
                    <div className="flex flex-col items-center justify-center h-full text-center mt-10">
                        <BookOpen size={48} className="text-slate-800 mb-4" />
                        <p className="text-slate-500 text-sm max-w-xs">
                            Type a query and press enter to search the vector database for similar historical incidents.
                        </p>
                    </div>
                )}
            </div>
        </div>
    );
};

export default KnowledgeSearch;
