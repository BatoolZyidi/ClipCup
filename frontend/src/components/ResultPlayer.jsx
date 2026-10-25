import React, { useState } from 'react';
import { Download, ExternalLink, Copy, Check, RotateCcw, ArrowLeft } from 'lucide-react';
import StatsCard from './StatsCard';

export default function ResultPlayer({ job, onReset, onBack }) {
  const [copied, setCopied] = useState(false);
  const resultUrl = job?.result_url || '';

  // Format local file URI, Windows file path, or web URL for video playback
  let videoSrc = resultUrl;
  let downloadUrl = resultUrl;
  if (resultUrl && !resultUrl.startsWith('http://') && !resultUrl.startsWith('https://')) {
    // If local file path, extract filename and serve via proxy /media/shorts/
    const normalized = resultUrl.replace(/\\/g, '/');
    const filename = normalized.split('/').pop();
    if (filename) {
      videoSrc = `/media/shorts/${filename}`;
      downloadUrl = `/media/shorts/${filename}`;
    }
  }

  const handleCopyUrl = () => {
    if (resultUrl) {
      navigator.clipboard.writeText(resultUrl);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="w-full max-w-4xl mx-auto glass-panel rounded-3xl p-6 sm:p-8 space-y-8 animate-fadeIn">
      {/* Header with Back and New Video buttons */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-white/5 pb-6">
        <div>
          <button
            onClick={onBack || onReset}
            className="inline-flex items-center gap-2 text-xs font-semibold text-slate-300 hover:text-white bg-slate-800/80 hover:bg-slate-700/80 border border-white/10 px-3 py-1.5 rounded-lg transition-all mb-3 shadow-sm hover:scale-[1.02]"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>← Back to Home</span>
          </button>
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse" />
            <h2 className="text-xl font-extrabold text-white">Your Vertical Short is Ready!</h2>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Transcribed with AssemblyAI • Highlight selected by AI • Reframed with OpenCV 5 (Face, Moment &amp; Object Tracking)
          </p>
        </div>
        <div className="flex items-center gap-2.5">
          <button
            onClick={onReset}
            className="flex items-center gap-2 text-xs font-semibold px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 transition-colors border border-white/10"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Process Another Video</span>
          </button>
        </div>
      </div>

      {/* Main Content: Player + Stats */}
      <div className="grid grid-cols-1 md:grid-cols-12 gap-8 items-start">
        {/* Left Column: Vertical Video Frame */}
        <div className="md:col-span-5 flex justify-center">
          <div className="relative w-full max-w-[280px] aspect-[9/16] rounded-3xl overflow-hidden bg-black border-4 border-slate-800 shadow-2xl shadow-brand-500/10 ring-1 ring-white/10">
            <video
              src={videoSrc}
              controls
              autoPlay
              loop
              playsInline
              className="w-full h-full object-cover"
            >
              Your browser does not support the video tag.
            </video>
            <div className="absolute top-3 left-3 px-2 py-0.5 rounded-md bg-black/60 backdrop-blur-md text-[10px] font-mono text-white/90 border border-white/10 pointer-events-none">
              Vertical • 1080x1920
            </div>
          </div>
        </div>

        {/* Right Column: AI Analysis & Metrics */}
        <div className="md:col-span-7 space-y-6">
          <StatsCard
            stats={job?.stats}
            topic={job?.topic}
            reason={job?.reason}
          />

          {/* Action Buttons */}
          <div className="space-y-3 pt-2">
            <a
              href={downloadUrl}
              download={`clipcup_${job?.id || 'short'}.mp4`}
              target="_blank"
              rel="noreferrer"
              className="w-full py-3 px-4 rounded-xl bg-gradient-to-r from-brand-600 to-accent-500 hover:from-brand-500 hover:to-accent-400 text-white font-semibold text-sm shadow-md shadow-brand-500/25 flex items-center justify-center gap-2 transition-all duration-200"
            >
              <Download className="w-4 h-4" />
              <span>Download Vertical Short (H.264 MP4)</span>
            </a>

            <div className="flex items-center gap-2">
              <input
                type="text"
                readOnly
                value={resultUrl}
                className="flex-1 glass-input text-xs text-slate-300 px-3.5 py-2.5 rounded-xl font-mono truncate focus:outline-none"
              />
              <button
                onClick={handleCopyUrl}
                title="Copy Presigned S3 Link"
                className="px-3.5 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold flex items-center gap-1.5 transition-colors border border-white/10 shrink-0"
              >
                {copied ? (
                  <>
                    <Check className="w-4 h-4 text-emerald-400" />
                    <span>Copied!</span>
                  </>
                ) : (
                  <>
                    <Copy className="w-4 h-4" />
                    <span>Copy URL</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
