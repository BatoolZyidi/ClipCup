import React from 'react';
import { Activity, Scissors, Target, ShieldAlert, Cpu } from 'lucide-react';

export default function StatsCard({ stats, topic, reason }) {
  const safeStats = stats || {};
  const hitRate = safeStats.face_hit_rate != null ? (safeStats.face_hit_rate * 100).toFixed(1) : '100.0';
  const jitter = safeStats.avg_jitter_px != null ? safeStats.avg_jitter_px : 0;
  const fallbacks = safeStats.fallback_frames != null ? safeStats.fallback_frames : 0;
  const totalFrames = safeStats.total_frames || 0;
  const sceneCuts = safeStats.scene_cuts || 0;

  return (
    <div className="space-y-4">
      {/* Highlight Topic Card */}
      <div className="p-4 rounded-2xl bg-gradient-to-r from-brand-950/40 to-slate-900/60 border border-brand-500/20">
        <div className="flex items-center gap-2 text-brand-400 text-xs font-semibold uppercase tracking-wider mb-1">
          <Target className="w-3.5 h-3.5" />
          <span>AI Selected Moment</span>
        </div>
        <h4 className="text-base font-bold text-white mb-1">{topic || 'Featured Highlight'}</h4>
        <p className="text-xs text-slate-300 leading-relaxed">
          {reason || 'Contextual dialogue and visual motion analysis identified this segment as the primary highlight.'}
        </p>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="p-3.5 rounded-2xl bg-slate-900/60 border border-white/5">
          <div className="flex items-center gap-1.5 text-slate-400 text-xs mb-1">
            <Target className="w-3.5 h-3.5 text-emerald-400" />
            <span>Face &amp; Focus Hit</span>
          </div>
          <div className="text-lg font-bold text-slate-100 font-mono">{hitRate}%</div>
          <div className="text-[10px] text-slate-500 mt-0.5">OpenCV 5 Tracking</div>
        </div>

        <div className="p-3.5 rounded-2xl bg-slate-900/60 border border-white/5">
          <div className="flex items-center gap-1.5 text-slate-400 text-xs mb-1">
            <Activity className="w-3.5 h-3.5 text-accent-400" />
            <span>Pan Stability</span>
          </div>
          <div className="text-lg font-bold text-slate-100 font-mono">{jitter} px</div>
          <div className="text-[10px] text-slate-500 mt-0.5">Gaussian smoothed pan</div>
        </div>

        <div className="p-3.5 rounded-2xl bg-slate-900/60 border border-white/5">
          <div className="flex items-center gap-1.5 text-slate-400 text-xs mb-1">
            <Scissors className="w-3.5 h-3.5 text-amber-400" />
            <span>Scene Cuts</span>
          </div>
          <div className="text-lg font-bold text-slate-100 font-mono">{sceneCuts}</div>
          <div className="text-[10px] text-slate-500 mt-0.5">Shot boundary cuts</div>
        </div>

        <div className="p-3.5 rounded-2xl bg-slate-900/60 border border-white/5">
          <div className="flex items-center gap-1.5 text-slate-400 text-xs mb-1">
            <ShieldAlert className="w-3.5 h-3.5 text-purple-400" />
            <span>Moment &amp; Object Focus</span>
          </div>
          <div className="text-lg font-bold text-slate-100 font-mono">
            {fallbacks} <span className="text-xs text-slate-500">/ {totalFrames}</span>
          </div>
          <div className="text-[10px] text-slate-500 mt-0.5">Visual saliency tracking</div>
        </div>
      </div>
    </div>
  );
}
