import React from 'react';
import { Video, Zap, Brain, Eye, Layers, ArrowRight, Sparkles } from 'lucide-react';

const FEATURES = [
  {
    icon: Brain,
    color: 'from-violet-500 to-purple-600',
    glow: 'shadow-violet-500/20',
    title: 'AI Highlight Selection',
    desc: 'AWS Bedrock analyzes your transcript and picks the most engaging, viral moments automatically.',
    badge: 'Intelligent Cuts',
  },
  {
    icon: Eye,
    color: 'from-cyan-500 to-blue-600',
    glow: 'shadow-cyan-500/20',
    title: 'OpenCV 5 Smart Tracking',
    desc: 'Powered by OpenCV 5 — tracks human faces, screen presentations, active objects, and motion dynamics with smooth cinematic panning.',
    badge: 'OpenCV 5 Vision',
  },
  {
    icon: Zap,
    color: 'from-amber-500 to-orange-500',
    glow: 'shadow-amber-500/20',
    title: 'Speech to Text Sync',
    desc: 'Word-level timestamps power precise clip boundaries, so cuts always land on natural sentence and speech breaks.',
    badge: 'Audio Intelligence',
  },
  {
    icon: Layers,
    color: 'from-emerald-500 to-teal-600',
    glow: 'shadow-emerald-500/20',
    title: 'Device Upload & Video URLs',
    desc: 'Upload video files directly from your computer or phone, or paste YouTube and direct video links for instant conversion up to 120s.',
    badge: 'Upload or Paste Link',
  },
];

const TECH = [
  { label: 'OpenCV 5', sub: 'Face & Motion Saliency' },
  { label: 'AWS Bedrock', sub: 'Claude 3.5 Sonnet' },
  { label: 'AssemblyAI', sub: 'Word-level STT' },
  { label: 'AWS S3', sub: 'Cloud Video Storage' },
  { label: 'PostgreSQL', sub: 'Cloud Database' },
  { label: 'Django REST', sub: 'Python Backend' },
];

export default function LandingPage({ onGetStarted }) {
  return (
    <div className="min-h-screen flex flex-col bg-[#080d18] text-white overflow-x-hidden">
      {/* ── Nav ── */}
      <nav className="w-full max-w-6xl mx-auto flex items-center justify-between px-6 py-5">
        <div className="flex items-center gap-3">
          <div className="relative flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-tr from-brand-600 to-accent-400 p-[2px] shadow-lg shadow-brand-500/20">
            <div className="w-full h-full bg-[#080d18] rounded-[10px] flex items-center justify-center">
              <Video className="w-5 h-5 text-brand-400" />
            </div>
            <span className="absolute -top-1 -right-1 flex h-3 w-3">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-brand-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-3 w-3 bg-brand-500"></span>
            </span>
          </div>
          <span className="text-xl font-extrabold tracking-tight bg-gradient-to-r from-white to-slate-400 bg-clip-text text-transparent">
            Clip Cup
          </span>
        </div>
        <button
          onClick={onGetStarted}
          className="flex items-center gap-2 px-5 py-2 rounded-xl bg-gradient-to-r from-brand-600 to-brand-500 text-white text-sm font-semibold shadow-lg shadow-brand-500/30 hover:shadow-brand-500/50 hover:scale-105 transition-all duration-200"
        >
          Sign In <ArrowRight className="w-4 h-4" />
        </button>
      </nav>

      {/* ── Hero ── */}
      <section className="flex-1 flex flex-col items-center justify-center text-center px-6 py-20 relative">
        {/* background glow orbs */}
        <div className="absolute top-20 left-1/4 w-96 h-96 bg-brand-600/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute bottom-20 right-1/4 w-80 h-80 bg-accent-500/10 rounded-full blur-3xl pointer-events-none" />

        {/* Feature Pill */}
        <div className="flex justify-center mb-8">
          <span className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full text-xs font-semibold bg-brand-500/10 border border-brand-500/20 text-brand-300">
            <Sparkles className="w-3.5 h-3.5 text-accent-400" /> Convert Horizontal Videos to Vertical Shorts
          </span>
        </div>

        <h1 className="text-5xl sm:text-6xl md:text-7xl font-black tracking-tight leading-[1.05] max-w-4xl">
          Convert Horizontal Videos into{' '}
          <span className="bg-gradient-to-r from-brand-400 via-brand-500 to-accent-400 bg-clip-text text-transparent">
            Engaging Vertical Shorts
          </span>
        </h1>

        <p className="mt-6 text-lg text-slate-400 max-w-2xl leading-relaxed">
          Upload any video directly from your device or paste a link. AI pinpoints the best highlight, tracks the speaker frame-by-frame, and renders a ready-to-share vertical video in minutes.
        </p>

        <div className="mt-10 flex flex-col sm:flex-row items-center gap-4">
          <button
            onClick={onGetStarted}
            className="group flex items-center gap-2 px-8 py-4 rounded-2xl bg-gradient-to-r from-brand-600 to-brand-500 text-white font-bold text-base shadow-2xl shadow-brand-500/30 hover:shadow-brand-500/60 hover:scale-105 transition-all duration-200"
          >
            Get Started Free
            <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
          </button>
        </div>
      </section>

      {/* ── Features ── */}
      <section className="max-w-6xl mx-auto w-full px-6 py-16">
        <p className="text-center text-xs font-semibold text-slate-500 uppercase tracking-widest mb-10">
          How It Works
        </p>
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-5">
          {FEATURES.map(({ icon: Icon, color, glow, title, desc, badge }) => (
            <div
              key={title}
              className={`relative p-6 rounded-3xl bg-slate-900/60 border border-white/5 hover:border-white/10 transition-all duration-300 hover:-translate-y-1 hover:shadow-2xl ${glow}`}
            >
              <div className={`inline-flex p-3 rounded-2xl bg-gradient-to-br ${color} shadow-lg ${glow} mb-4`}>
                <Icon className="w-5 h-5 text-white" />
              </div>
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-2 block">{badge}</span>
              <h3 className="text-sm font-bold text-white mb-2">{title}</h3>
              <p className="text-xs text-slate-400 leading-relaxed">{desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── Tech Stack ── */}
      <section className="max-w-6xl mx-auto w-full px-6 pb-16">
        <p className="text-center text-xs font-semibold text-slate-500 uppercase tracking-widest mb-6">
          Powered By
        </p>
        <div className="flex flex-wrap justify-center gap-3">
          {TECH.map(({ label, sub }) => (
            <div key={label} className="px-5 py-3 rounded-2xl bg-slate-900/60 border border-white/5 text-center">
              <p className="text-sm font-bold text-white">{label}</p>
              <p className="text-[10px] text-slate-500 mt-0.5">{sub}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── Footer ── */}
      <footer className="border-t border-white/5 py-6 px-6 text-center text-xs text-slate-600">
        <p>© {new Date().getFullYear()} Clip Cup. All rights reserved.</p>
      </footer>
    </div>
  );
}
