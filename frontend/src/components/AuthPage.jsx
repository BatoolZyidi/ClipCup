import React, { useState } from 'react';
import { Video, Eye, EyeOff, ArrowLeft, Loader2, User, Mail, Lock, ChevronRight } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function AuthPage({ onBack, onSuccess }) {
  const { login, register, loading } = useAuth();
  const [mode, setMode] = useState('login'); // 'login' | 'register'
  const [error, setError] = useState('');
  const [showPass, setShowPass] = useState(false);

  // Shared field state
  const [fields, setFields] = useState({
    username: '',
    email: '',
    password: '',
    first_name: '',
    last_name: '',
  });

  const set = (key) => (e) => {
    setFields((f) => ({ ...f, [key]: e.target.value }));
    setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    let result;
    if (mode === 'login') {
      result = await login(fields.username || fields.email, fields.password);
    } else {
      result = await register(fields);
    }
    if (result.ok) {
      onSuccess();
    } else {
      setError(result.error);
    }
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-[#080d18] px-4 relative overflow-hidden">
      {/* Glow orbs */}
      <div className="absolute top-0 left-1/3 w-96 h-96 bg-brand-600/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-0 right-1/3 w-80 h-80 bg-accent-500/10 rounded-full blur-3xl pointer-events-none" />

      <div className="relative z-10 w-full max-w-md">
        {/* Back button */}
        <button
          onClick={onBack}
          className="mb-6 flex items-center gap-1.5 text-sm text-slate-400 hover:text-white transition-colors"
        >
          <ArrowLeft className="w-4 h-4" /> Back to landing
        </button>

        {/* Card */}
        <div className="glass-panel rounded-3xl p-8 border border-white/5">
          {/* Logo */}
          <div className="flex items-center gap-3 mb-8">
            <div className="relative flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-tr from-brand-600 to-accent-400 p-[2px] shadow-lg shadow-brand-500/20">
              <div className="w-full h-full bg-[#0d121c] rounded-[10px] flex items-center justify-center">
                <Video className="w-5 h-5 text-brand-400" />
              </div>
            </div>
            <div>
              <h1 className="text-lg font-extrabold text-white">Clip Cup</h1>
              <p className="text-[11px] text-slate-500">AI Short-Form Reframing</p>
            </div>
          </div>

          {/* Mode toggle */}
          <div className="flex p-1 bg-slate-900/80 rounded-2xl border border-white/5 mb-8">
            {['login', 'register'].map((m) => (
              <button
                key={m}
                type="button"
                onClick={() => { setMode(m); setError(''); }}
                className={`flex-1 py-2.5 rounded-xl text-xs font-semibold transition-all duration-200 ${
                  mode === m
                    ? 'bg-gradient-to-r from-brand-600 to-brand-500 text-white shadow-md shadow-brand-500/25'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {m === 'login' ? 'Sign In' : 'Create Account'}
              </button>
            ))}
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {mode === 'register' && (
              <div className="grid grid-cols-2 gap-3">
                <div className="relative">
                  <User className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
                  <input
                    type="text"
                    placeholder="First name"
                    value={fields.first_name}
                    onChange={set('first_name')}
                    className="w-full glass-input text-slate-100 placeholder-slate-500 pl-10 pr-4 py-3 rounded-2xl text-sm focus:outline-none"
                  />
                </div>
                <div className="relative">
                  <User className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
                  <input
                    type="text"
                    placeholder="Last name"
                    value={fields.last_name}
                    onChange={set('last_name')}
                    className="w-full glass-input text-slate-100 placeholder-slate-500 pl-10 pr-4 py-3 rounded-2xl text-sm focus:outline-none"
                  />
                </div>
              </div>
            )}

            {mode === 'register' && (
              <div className="relative">
                <Mail className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
                <input
                  type="email"
                  placeholder="Email address"
                  value={fields.email}
                  onChange={set('email')}
                  required
                  className="w-full glass-input text-slate-100 placeholder-slate-500 pl-10 pr-4 py-3 rounded-2xl text-sm focus:outline-none"
                />
              </div>
            )}

            <div className="relative">
              <User className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
              <input
                type="text"
                placeholder={mode === 'login' ? 'Username or email' : 'Username'}
                value={fields.username}
                onChange={set('username')}
                required
                autoComplete="username"
                className="w-full glass-input text-slate-100 placeholder-slate-500 pl-10 pr-4 py-3 rounded-2xl text-sm focus:outline-none"
              />
            </div>

            <div className="relative">
              <Lock className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
              <input
                type={showPass ? 'text' : 'password'}
                placeholder="Password"
                value={fields.password}
                onChange={set('password')}
                required
                autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
                className="w-full glass-input text-slate-100 placeholder-slate-500 pl-10 pr-10 py-3 rounded-2xl text-sm focus:outline-none"
              />
              <button
                type="button"
                tabIndex={-1}
                onClick={() => setShowPass((v) => !v)}
                className="absolute right-3.5 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300 transition-colors"
              >
                {showPass ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>

            {error && (
              <p className="text-xs text-red-400 bg-red-500/10 border border-red-500/20 rounded-xl px-4 py-2.5">
                {error}
              </p>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full flex items-center justify-center gap-2 py-3.5 rounded-2xl bg-gradient-to-r from-brand-600 to-brand-500 text-white font-bold text-sm shadow-lg shadow-brand-500/30 hover:shadow-brand-500/50 hover:scale-[1.02] transition-all duration-200 disabled:opacity-60 disabled:scale-100"
            >
              {loading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <>
                  {mode === 'login' ? 'Sign In' : 'Create Account'}
                  <ChevronRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>

          <p className="mt-6 text-center text-xs text-slate-500">
            {mode === 'login' ? "Don't have an account? " : 'Already have an account? '}
            <button
              onClick={() => { setMode(mode === 'login' ? 'register' : 'login'); setError(''); }}
              className="text-brand-400 hover:text-brand-300 font-semibold transition-colors"
            >
              {mode === 'login' ? 'Sign up free' : 'Sign in'}
            </button>
          </p>
        </div>
      </div>
    </div>
  );
}
