import React, { useState, useRef } from 'react';
import axios from 'axios';
import { UploadCloud, File, X, CheckCircle, Loader2 } from 'lucide-react';

const DocumentUploadModal = ({ isOpen, onClose, activeWellId }) => {
    const [file, setFile] = useState(null);
    const [isUploading, setIsUploading] = useState(false);
    const [uploadStatus, setUploadStatus] = useState(null);
    const fileInputRef = useRef(null);

    if (!isOpen) return null;

    const handleDragOver = (e) => {
        e.preventDefault();
        e.stopPropagation();
    };

    const handleDrop = (e) => {
        e.preventDefault();
        e.stopPropagation();
        if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
            setFile(e.dataTransfer.files[0]);
        }
    };

    const handleUpload = async () => {
        if (!file) return;
        setIsUploading(true);
        setUploadStatus(null);
        
        const formData = new FormData();
        formData.append('file', file);
        formData.append('well_id', activeWellId || 'OIL-BAGHJAN-1');

        try {
            await axios.post('http://localhost:8000/api/upload-report', formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });
            setUploadStatus('success');
            setTimeout(() => {
                onClose();
                setFile(null);
                setUploadStatus(null);
            }, 2000);
        } catch (error) {
            console.error('Upload failed:', error);
            setUploadStatus('error');
        } finally {
            setIsUploading(false);
        }
    };

    return (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm animate-in fade-in">
            <div className="bg-slate-900 border border-slate-700 w-[500px] rounded-lg shadow-2xl overflow-hidden animate-in zoom-in-95">
                <div className="flex justify-between items-center p-4 border-b border-slate-800 bg-slate-900/50">
                    <h2 className="text-lg font-semibold text-slate-200">Upload Drilling Report (PDF)</h2>
                    <button onClick={onClose} className="text-slate-500 hover:text-slate-300 transition-colors">
                        <X size={20} />
                    </button>
                </div>
                
                <div className="p-6">
                    {!file ? (
                        <div 
                            className="border-2 border-dashed border-slate-700 rounded-lg h-48 flex flex-col items-center justify-center cursor-pointer hover:border-status-fluid/50 hover:bg-slate-800/50 transition-colors"
                            onDragOver={handleDragOver}
                            onDrop={handleDrop}
                            onClick={() => fileInputRef.current?.click()}
                        >
                            <input 
                                type="file" 
                                ref={fileInputRef} 
                                className="hidden" 
                                accept=".pdf"
                                onChange={(e) => {
                                    if (e.target.files && e.target.files.length > 0) {
                                        setFile(e.target.files[0]);
                                    }
                                }} 
                            />
                            <UploadCloud size={40} className="text-slate-500 mb-3" />
                            <p className="text-slate-300 font-medium mb-1">Drag and drop a PDF file here</p>
                            <p className="text-slate-500 text-sm">or click to browse from your computer</p>
                        </div>
                    ) : (
                        <div className="flex flex-col items-center justify-center h-48 bg-slate-800/50 rounded-lg border border-slate-700">
                            <File size={40} className="text-status-fluid mb-3" />
                            <p className="text-slate-200 font-medium mb-2">{file.name}</p>
                            <p className="text-slate-500 text-sm mb-4">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                            <button 
                                onClick={() => setFile(null)}
                                className="text-sm text-red-400 hover:text-red-300 transition-colors"
                            >
                                Remove file
                            </button>
                        </div>
                    )}

                    {uploadStatus === 'success' && (
                        <div className="mt-4 p-3 bg-status-active/10 border border-status-active/30 rounded flex items-center text-status-active">
                            <CheckCircle size={18} className="mr-2" />
                            <span className="text-sm">File parsed and FAISS index updated successfully.</span>
                        </div>
                    )}
                    
                    {uploadStatus === 'error' && (
                        <div className="mt-4 p-3 bg-red-500/10 border border-red-500/30 rounded flex items-center text-red-400">
                            <X size={18} className="mr-2" />
                            <span className="text-sm">Failed to upload and parse the report. Please try again.</span>
                        </div>
                    )}
                </div>

                <div className="p-4 border-t border-slate-800 bg-slate-900/50 flex justify-end space-x-3">
                    <button 
                        onClick={onClose}
                        className="px-4 py-2 rounded text-slate-300 hover:bg-slate-800 transition-colors text-sm font-medium"
                    >
                        Cancel
                    </button>
                    <button 
                        onClick={handleUpload}
                        disabled={!file || isUploading}
                        className={`px-4 py-2 rounded text-white flex items-center text-sm font-medium transition-colors ${
                            !file || isUploading 
                            ? 'bg-slate-700 cursor-not-allowed opacity-70' 
                            : 'bg-status-fluid hover:bg-blue-500'
                        }`}
                    >
                        {isUploading ? (
                            <>
                                <Loader2 size={16} className="animate-spin mr-2" />
                                Parsing PDF & Updating FAISS...
                            </>
                        ) : 'Upload Report'}
                    </button>
                </div>
            </div>
        </div>
    );
};

export default DocumentUploadModal;
