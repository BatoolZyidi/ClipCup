import React, { useState, useRef } from 'react';
import { Link2, Upload, AlertCircle, FileVideo, ArrowRight } from 'lucide-react';

export default function InputTabs({ onSubmit, isSubmitting }) {
  const [activeTab, setActiveTab] = useState('url'); // 'url' | 'upload'
  const [urlInput, setUrlInput] = useState('');
  const [selectedFile, setSelectedFile] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const [error, setError] = useState('');
  const fileInputRef = useRef(null);

  const handleTabChange = (tab) => {
    setActiveTab(tab);
    setError('');
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      validateAndSetFile(file);
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  const validateAndSetFile = (file) => {
    setError('');
    const validExtensions = ['.mp4', '.mov', '.mkv', '.webm', '.avi'];
    const hasValidExt = validExtensions.some(ext => file.name.toLowerCase().endsWith(ext));
    if (!hasValidExt && !file.type.startsWith('video/')) {
      setError('Please select a valid video file (.mp4, .mov, .mkv, .webm).');
      return;
    }
    setSelectedFile(file);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    setError('');

    if (activeTab === 'url') {
      const trimmed = urlInput.trim();
      if (!trimmed) {
        setError('Please enter a direct video URL.');
        return;
      }
      onSubmit({ type: 'url', value: trimmed });
    } else {
      if (!selectedFile) {
        setError('Please select or drop a video file to upload.');
        return;
      }
      onSubmit({ type: 'file', value: selectedFile });
    }
  };

  return (
    <div className="w-full max-w-2xl mx-auto glass-panel rounded-3xl p-6 sm:p-8 relative overflow-hidden transition-all duration-300">
      {/* Background glow accent */}
      <div className="absolute top-0 right-1/4 -mt-12 w-64 h-32 bg-brand-500/10 blur-3xl pointer-events-none rounded-full" />
      <div className="absolute bottom-0 left-1/4 -mb-12 w-64 h-32 bg-accent-500/10 blur-3xl pointer-events-none rounded-full" />

      {/* Tabs Switcher */}
      <div className="flex p-1 bg-slate-900/80 rounded-2xl border border-white/5 mb-6 max-w-sm mx-auto">
        <button
          type="button"
          onClick={() => handleTabChange('url')}
          className={`flex-1 flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl text-xs sm:text-sm font-semibold transition-all duration-200 ${
            activeTab === 'url'
              ? 'bg-gradient-to-r from-brand-600 to-brand-500 text-white shadow-md shadow-brand-500/25'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <Link2 className="w-4 h-4" />
          Direct Video URL
        </button>
        <button
          type="button"
          onClick={() => handleTabChange('upload')}
          className={`flex-1 flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl text-xs sm:text-sm font-semibold transition-all duration-200 ${
            activeTab === 'upload'
              ? 'bg-gradient-to-r from-brand-600 to-brand-500 text-white shadow-md shadow-brand-500/25'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <Upload className="w-4 h-4" />
          File Upload
        </button>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {activeTab === 'url' ? (
          <div className="space-y-3">
            <label htmlFor="url-input" className="block text-xs font-semibold text-slate-300 uppercase tracking-wider">
              Video URL or YouTube Link (max 10 min)
            </label>
            <div className="relative">
              <input
                id="url-input"
                type="url"
                value={urlInput}
                onChange={(e) => {
                  setUrlInput(e.target.value);
                  setError('');
                }}
                placeholder="https://youtu.be/... or https://example.com/video.mp4"
                disabled={isSubmitting}
                className="w-full glass-input text-slate-100 placeholder-slate-500 px-4 py-3.5 rounded-2xl text-sm focus:outline-none pr-10"
              />
              <Link2 className="w-4 h-4 text-slate-500 absolute right-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
            </div>
            <div className="flex items-center justify-between text-[11px] text-slate-400 px-1">
              <span>YouTube, direct video URLs (.mp4, .mov…), max 10 min.</span>
              <button
                type="button"
                onClick={() => setUrlInput('https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4')}
                className="text-brand-400 hover:text-brand-300 hover:underline transition-colors"
              >
                Use sample URL
              </button>
            </div>
          </div>
        ) : (
          <div className="space-y-3">
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider">
              Upload Video File (Max 10 minutes)
            </label>
            <div
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              className={`border-2 border-dashed rounded-2xl p-6 sm:p-8 text-center cursor-pointer transition-all duration-200 ${
                dragActive
                  ? 'border-brand-500 bg-brand-500/10'
                  : selectedFile
                  ? 'border-brand-500/50 bg-slate-900/60'
                  : 'border-white/10 hover:border-white/20 bg-slate-900/30'
              }`}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept="video/mp4,video/quicktime,video/x-matroska,video/webm"
                onChange={handleFileChange}
                className="hidden"
                disabled={isSubmitting}
              />
              <div className="flex flex-col items-center justify-center gap-2">
                <div className="w-12 h-12 rounded-full bg-brand-500/10 text-brand-400 flex items-center justify-center mb-1">
                  {selectedFile ? <FileVideo className="w-6 h-6 text-brand-400" /> : <Upload className="w-6 h-6" />}
                </div>
                {selectedFile ? (
                  <div>
                    <p className="text-sm font-semibold text-slate-200">{selectedFile.name}</p>
                    <p className="text-xs text-slate-400 mt-0.5">
                      {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB • Click or drag to replace
                    </p>
                  </div>
                ) : (
                  <div>
                    <p className="text-sm font-medium text-slate-300">
                      <span className="text-brand-400 font-semibold">Click to upload</span> or drag and drop
                    </p>
                    <p className="text-xs text-slate-500 mt-1">MP4, MOV, MKV up to 10 minutes</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {error && (
          <div className="flex items-start gap-2.5 p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-red-300 text-xs animate-fadeIn">
            <AlertCircle className="w-4 h-4 shrink-0 mt-0.5 text-red-400" />
            <span>{error}</span>
          </div>
        )}

        <div className="flex justify-center">
          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full sm:w-auto min-w-[220px] max-w-sm py-3 px-8 rounded-2xl bg-gradient-to-r from-brand-600 via-brand-500 to-accent-500 hover:from-brand-500 hover:to-accent-400 text-white font-semibold text-sm shadow-lg shadow-brand-500/25 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 transition-all duration-200 active:scale-[0.99]"
          >
            {isSubmitting ? (
              <>
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                <span>Initializing Job...</span>
              </>
            ) : (
              <>
                <span>Generate Vertical Short</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
