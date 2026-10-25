import React, { useState, useEffect, useRef } from 'react';
import { AlertCircle, RotateCcw } from 'lucide-react';
import { useAuth } from './context/AuthContext';
import { apiUrl } from './api';
import LandingPage from './components/LandingPage';
import AuthPage from './components/AuthPage';
import Header from './components/Header';
import InputTabs from './components/InputTabs';
import ProgressBar from './components/ProgressBar';
import ResultPlayer from './components/ResultPlayer';
import HistoryPanel from './components/HistoryPanel';

// Views: 'landing' | 'auth' | 'app'
// App sub-views: 'input' | 'processing' | 'result' | 'history'

export default function App() {
  const { user, authFetch } = useAuth();

  // Top-level routing
  const [page, setPage] = useState('landing'); // 'landing' | 'auth' | 'app'

  // App inner state
  const [view, setView] = useState('input');
  const [currentJob, setCurrentJob] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [elapsedSeconds, setElapsedSeconds] = useState(0);

  const pollIntervalRef = useRef(null);
  const timerIntervalRef = useRef(null);

  // If user is already logged in, skip to app
  useEffect(() => {
    if (user && page === 'landing') setPage('app');
    if (!user && page === 'app') setPage('landing');
  }, [user]);

  // Poll job status every 3s
  useEffect(() => {
    if (view === 'processing' && currentJob?.id) {
      timerIntervalRef.current = setInterval(() => {
        setElapsedSeconds((prev) => prev + 1);
      }, 1000);

      pollIntervalRef.current = setInterval(async () => {
        try {
          const res = await authFetch(apiUrl(`/api/jobs/${currentJob.id}`));
          if (!res.ok) throw new Error(`Server returned ${res.status}`);
          const data = await res.json();
          setCurrentJob(data);

          if (data.status === 'DONE') {
            clearInterval(pollIntervalRef.current);
            clearInterval(timerIntervalRef.current);
            setView('result');
          } else if (data.status === 'FAILED') {
            clearInterval(pollIntervalRef.current);
            clearInterval(timerIntervalRef.current);
            setErrorMessage(data.error || 'Video processing failed. Please check the source format.');
          }
        } catch (err) {
          console.error('Error polling job:', err);
        }
      }, 3000);
    }

    return () => {
      if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
      if (timerIntervalRef.current) clearInterval(timerIntervalRef.current);
    };
  }, [view, currentJob?.id, authFetch]);

  const handleSubmit = async ({ type, value }) => {
    setIsSubmitting(true);
    setErrorMessage('');

    try {
      let response;
      if (type === 'url') {
        response = await authFetch(apiUrl('/api/jobs'), {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ url: value }),
        });
      } else {
        const formData = new FormData();
        formData.append('file', value);
        response = await authFetch(apiUrl('/api/jobs'), { method: 'POST', body: formData });
      }

      const text = await response.text();
      const data = text ? JSON.parse(text) : {};

      if (!response.ok) {
        throw new Error(data.error || `Server error ${response.status}`);
      }

      setCurrentJob(data);
      setElapsedSeconds(0);
      setView('processing');
    } catch (err) {
      setErrorMessage(err.message || 'Submission failed.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleReset = () => {
    if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
    if (timerIntervalRef.current) clearInterval(timerIntervalRef.current);
    setView('input');
    setCurrentJob(null);
    setErrorMessage('');
    setElapsedSeconds(0);
  };

  const handleResumeJob = async (job) => {
    setCurrentJob(job);
    setView('result');

    // Always fetch latest full detail from backend to ensure topic, reason, and stats are populated
    try {
      const res = await authFetch(apiUrl(`/api/jobs/${job.id}`));
      if (res.ok) {
        const detail = await res.json();
        setCurrentJob((prev) => ({ ...prev, ...job, ...detail }));
      }
    } catch (err) {
      // Retain current job object
    }
  };

  // ── Routing ──────────────────────────────────────────────────────────────

  if (page === 'landing') {
    return <LandingPage onGetStarted={() => setPage('auth')} />;
  }

  if (page === 'auth') {
    return (
      <AuthPage
        onBack={() => setPage('landing')}
        onSuccess={() => setPage('app')}
      />
    );
  }

  // ── Authenticated App ─────────────────────────────────────────────────────
  return (
    <div className="min-h-screen flex flex-col justify-between selection:bg-brand-500/30 selection:text-brand-100">
      <div>
        <Header
          onShowHistory={() => setView('history')}
          onGoHome={handleReset}
        />

        <main className="max-w-5xl mx-auto px-4 py-8 sm:py-12">
          {errorMessage && (
            <div className="max-w-2xl mx-auto mb-6 p-4 rounded-2xl bg-red-500/10 border border-red-500/20 text-red-200 text-sm flex items-start justify-between gap-3 animate-fadeIn">
              <div className="flex items-start gap-2.5">
                <AlertCircle className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
                <div>
                  <h4 className="font-semibold text-red-300">Processing Error</h4>
                  <p className="text-xs text-red-300/80 mt-0.5">{errorMessage}</p>
                </div>
              </div>
              <button
                onClick={handleReset}
                className="shrink-0 flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-red-500/20 hover:bg-red-500/30 text-xs font-semibold text-red-200 transition-colors"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                <span>Try Again</span>
              </button>
            </div>
          )}

          {view === 'input' && (
            <div className="space-y-8 animate-fadeIn">
              <div className="text-center max-w-xl mx-auto space-y-3">
                <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-white">
                  Turn Horizontal Videos into{' '}
                  <span className="bg-gradient-to-r from-brand-400 via-brand-500 to-accent-400 bg-clip-text text-transparent">
                    Viral Vertical Shorts
                  </span>
                </h2>
                <p className="text-sm text-slate-400 leading-relaxed">
                  Automatic AI highlight selection, intelligent speaker &amp; visual attention tracking with OpenCV 5, and smooth panning with synced audio.
                </p>
              </div>
              <InputTabs onSubmit={handleSubmit} isSubmitting={isSubmitting} />
              <HistoryPanel onResumeJob={handleResumeJob} />
            </div>
          )}

          {view === 'history' && (
            <div className="animate-fadeIn">
              <button
                onClick={() => setView('input')}
                className="mb-6 flex items-center gap-1.5 text-sm text-slate-400 hover:text-white transition-colors"
              >
                ← Back
              </button>
              <HistoryPanel onResumeJob={(job) => { handleResumeJob(job); setView('result'); }} />
            </div>
          )}

          {view === 'processing' && (
            <ProgressBar job={currentJob} elapsedSeconds={elapsedSeconds} />
          )}

          {view === 'result' && (
            <ResultPlayer
              job={currentJob}
              onReset={handleReset}
              onBack={() => setView('input')}
            />
          )}
        </main>
      </div>

      <footer className="w-full border-t border-white/5 py-6 px-4 text-center text-xs text-slate-500">
        <div className="max-w-5xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>Clip Cup · Automated AI Video Reframer</span>
          <div className="flex items-center gap-4 text-slate-400">
            <span>OpenCV YuNet</span>
            <span>•</span>
            <span>AssemblyAI</span>
            <span>•</span>
            <span>AWS Bedrock</span>
            <span>•</span>
            <span>PostgreSQL</span>
            <span>•</span>
            <span>AWS S3</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
