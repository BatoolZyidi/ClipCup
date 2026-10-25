import React, { useState } from 'react';
import { Video, LogOut, History, ChevronDown } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function Header({ onShowHistory, onGoHome }) {
  const { user, logout } = useAuth();
  const [menuOpen, setMenuOpen] = useState(false);

  const initials = user
    ? ((user.first_name?.[0] || '') + (user.last_name?.[0] || '') || user.username?.[0] || '?').toUpperCase()
    : '?';

  return (
    <header className="w-full pt-6 pb-5 px-4 max-w-5xl mx-auto flex items-center justify-between border-b border-white/5">
      {/* Logo */}
      <div
        className="flex items-center gap-3 cursor-pointer group"
        onClick={onGoHome}
        title="Go to Home"
      >
        <div className="relative flex items-center justify-center w-11 h-11 rounded-2xl bg-gradient-to-tr from-brand-600 via-brand-500 to-accent-400 p-[2px] shadow-lg shadow-brand-500/20 group-hover:scale-105 transition-transform">
          <div className="w-full h-full bg-[#0d121c] rounded-[13px] flex items-center justify-center">
            <Video className="w-5 h-5 text-brand-400" />
          </div>
          <span className="absolute -top-1 -right-1 flex h-3.5 w-3.5">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-brand-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-3.5 w-3.5 bg-brand-500"></span>
          </span>
        </div>
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xl font-extrabold tracking-tight bg-gradient-to-r from-white via-slate-100 to-slate-400 bg-clip-text text-transparent group-hover:text-white transition-colors">
              Clip Cup
            </span>
            <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-brand-500/10 text-brand-400 border border-brand-500/20 tracking-wide uppercase">
              POC v1.0
            </span>
          </div>
          <p className="text-xs text-slate-500 font-medium">Horizontal to vertical video reframing · OpenCV &amp; AI</p>
        </div>
      </div>

      {/* Right: user menu */}
      {user && (
        <div className="relative">
          <button
            onClick={() => setMenuOpen((v) => !v)}
            className="flex items-center gap-2.5 px-3 py-2 rounded-2xl bg-slate-900/60 border border-white/5 hover:border-white/10 transition-all duration-200"
          >
            <div className="w-7 h-7 rounded-full bg-gradient-to-br from-brand-500 to-accent-500 flex items-center justify-center text-white text-xs font-bold shrink-0">
              {initials}
            </div>
            <span className="text-xs text-slate-300 font-medium max-w-[100px] truncate hidden sm:block">
              {user.first_name || user.username}
            </span>
            <ChevronDown className={`w-3.5 h-3.5 text-slate-500 transition-transform ${menuOpen ? 'rotate-180' : ''}`} />
          </button>

          {menuOpen && (
            <div className="absolute right-0 mt-2 w-52 rounded-2xl bg-slate-900 border border-white/10 shadow-2xl overflow-hidden z-50 animate-fadeIn">
              <div className="px-4 py-3 border-b border-white/5">
                <p className="text-xs font-semibold text-white truncate">{user.username}</p>
                <p className="text-[11px] text-slate-500 truncate">{user.email}</p>
              </div>
              <button
                onClick={() => { setMenuOpen(false); onShowHistory?.(); }}
                className="w-full flex items-center gap-3 px-4 py-3 text-sm text-slate-300 hover:bg-slate-800 hover:text-white transition-colors"
              >
                <History className="w-4 h-4 text-brand-400" /> My History
              </button>
              <button
                onClick={() => { setMenuOpen(false); logout(); }}
                className="w-full flex items-center gap-3 px-4 py-3 text-sm text-slate-300 hover:bg-red-500/10 hover:text-red-300 transition-colors border-t border-white/5"
              >
                <LogOut className="w-4 h-4" /> Sign Out
              </button>
            </div>
          )}
        </div>
      )}
    </header>
  );
}
