import React from 'react';
import {
  DownloadCloud,
  FileAudio,
  Sparkles,
  Smile,
  Video,
  CheckCircle2,
  Clock,
  Loader2,
} from 'lucide-react';

const STEPS = [
  { key: 'ingesting', label: 'Ingest Video', icon: DownloadCloud, desc: 'Fetch & extract audio' },
  { key: 'transcribing', label: 'Transcribe', icon: FileAudio, desc: 'AssemblyAI timestamps' },
  { key: 'selecting', label: 'Select Segment', icon: Sparkles, desc: 'AI highlight selection' },
  { key: 'reframing', label: 'Smart Tracking', icon: Video, desc: 'OpenCV 5 Face & Objects' },
  { key: 'rendering', label: 'Render Video', icon: Video, desc: 'FFmpeg H.264 mux' },
  { key: 'storing', label: 'S3 Presign', icon: CheckCircle2, desc: 'Upload & URL ready' },
];

export default function ProgressBar({ job, elapsedSeconds }) {
  const currentStepKey = (job?.step || '').toLowerCase();
  const currentStatus = (job?.status || '').toUpperCase();

  // Find step index
  const stepIndexMap = {
    pending: 0,
    ingesting: 0,
    transcribing: 1,
    selecting: 2,
    reframing: 3,
    rendering: 4,
    storing: 5,
    done: 6,
    failed: -1,
  };

  const activeIndex = stepIndexMap[currentStepKey] ?? 0;
  const isDone = currentStatus === 'DONE';

  return (
    <div className="w-full max-w-2xl mx-auto glass-panel rounded-3xl p-6 sm:p-8 space-y-6">
      {/* Top status bar */}
      <div className="flex items-center justify-between border-b border-white/5 pb-4">
        <div>
          <span className="text-xs font-semibold text-brand-400 uppercase tracking-wider">
            Job Processing
          </span>
          <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2 mt-0.5">
            <span className="font-mono text-xs px-2 py-0.5 rounded bg-slate-800 text-slate-300">
              {job?.id}
            </span>
          </h2>
        </div>
        <div className="flex items-center gap-2 text-xs text-slate-400 bg-slate-900/60 px-3 py-1.5 rounded-full border border-white/5">
          <Clock className="w-3.5 h-3.5 text-brand-400 animate-spin-slow" />
          <span>{elapsedSeconds}s elapsed</span>
        </div>
      </div>

      {/* Steps visualization */}
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
        {STEPS.map((step, idx) => {
          const Icon = step.icon;
          const isComplete = isDone || idx < activeIndex;
          const isCurrent = !isDone && idx === activeIndex;

          return (
            <div
              key={step.key}
              className={`relative rounded-2xl p-3.5 border transition-all duration-300 ${
                isCurrent
                  ? 'bg-brand-500/10 border-brand-500/40 shadow-lg shadow-brand-500/10'
                  : isComplete
                  ? 'bg-slate-900/50 border-white/10 text-slate-300'
                  : 'bg-slate-950/30 border-white/5 text-slate-600'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <div
                  className={`w-7 h-7 rounded-xl flex items-center justify-center ${
                    isCurrent
                      ? 'bg-brand-500 text-white shadow-md shadow-brand-500/30'
                      : isComplete
                      ? 'bg-emerald-500/20 text-emerald-400'
                      : 'bg-slate-800/60 text-slate-600'
                  }`}
                >
                  {isCurrent ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : isComplete ? (
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  ) : (
                    <Icon className="w-3.5 h-3.5" />
                  )}
                </div>
                <span className="text-[10px] font-mono font-semibold opacity-60">
                  0{idx + 1}
                </span>
              </div>
              <h3 className={`text-xs font-semibold ${isCurrent ? 'text-white' : ''}`}>
                {step.label}
              </h3>
              <p className="text-[10px] text-slate-400 truncate mt-0.5">
                {step.desc}
              </p>
            </div>
          );
        })}
      </div>

      {/* Live status banner */}
      <div className="flex items-center justify-between text-xs px-1 text-slate-400">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-brand-400 animate-pulse" />
          <span>Pipeline is active. Polling status every 3s...</span>
        </div>
        <span className="text-[11px] font-mono text-slate-500">Max timeout: 15m</span>
      </div>
    </div>
  );
}
