import React, { useEffect, useState } from 'react';
import { History, CheckCircle, XCircle, Loader2, Clock, ExternalLink, ChevronRight } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { apiUrl } from '../api';

const STATUS_META = {
  DONE: { icon: CheckCircle, color: 'text-emerald-400', bg: 'bg-emerald-500/10 border-emerald-500/20' },
  FAILED: { icon: XCircle, color: 'text-red-400', bg: 'bg-red-500/10 border-red-500/20' },
  PENDING: { icon: Clock, color: 'text-slate-400', bg: 'bg-slate-500/10 border-slate-500/20' },
  default: { icon: Loader2, color: 'text-brand-400', bg: 'bg-brand-500/10 border-brand-500/20' },
};

function formatDate(iso) {
  return new Date(iso).toLocaleString(undefined, {
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
  });
}

export default function HistoryPanel({ onResumeJob }) {
  const { authFetch } = useAuth();
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    authFetch(apiUrl('/api/jobs/history'))
      .then((r) => r.json())
      .then((data) => setJobs(data.jobs || []))
      .catch(() => setError('Could not load history.'))
      .finally(() => setLoading(false));
  }, [authFetch]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-16 text-slate-500 gap-2">
        <Loader2 className="w-5 h-5 animate-spin" /> Loading history…
      </div>
    );
  }

  if (error) {
    return <p className="text-center text-red-400 py-8 text-sm">{error}</p>;
  }

  if (jobs.length === 0) {
    return (
      <div className="text-center py-16 space-y-2">
        <History className="w-10 h-10 text-slate-700 mx-auto" />
        <p className="text-slate-500 text-sm">No shorts created yet.</p>
        <p className="text-slate-600 text-xs">Submit a video above to get started.</p>
      </div>
    );
  }

  return (
    <div className="w-full max-w-2xl mx-auto space-y-3">
      <div className="flex items-center gap-2 mb-4">
        <History className="w-4 h-4 text-brand-400" />
        <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">Your History</h2>
        <span className="text-xs text-slate-600 ml-auto">{jobs.length} job{jobs.length !== 1 ? 's' : ''}</span>
      </div>
      {jobs.map((job) => {
        const meta = STATUS_META[job.status] || STATUS_META.default;
        const Icon = meta.icon;
        const isSpinning = !['DONE', 'FAILED'].includes(job.status);
        return (
          <div
            key={job.id}
            className={`flex items-center gap-4 p-4 rounded-2xl border ${meta.bg} transition-all duration-200 hover:border-white/10 cursor-pointer group`}
            onClick={() => job.status === 'DONE' && onResumeJob?.(job)}
          >
            <div className={`shrink-0 ${meta.color}`}>
              <Icon className={`w-5 h-5 ${isSpinning ? 'animate-spin' : ''}`} />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-semibold text-white truncate">
                {job.topic || job.source_input || job.id}
              </p>
              <p className="text-[11px] text-slate-500 mt-0.5">
                {job.status} · {formatDate(job.created_at)}
              </p>
            </div>
            <div className="shrink-0 flex items-center gap-2">
              {job.status === 'DONE' && (
                <button
                  type="button"
                  onClick={() => onResumeJob?.(job)}
                  className="px-2.5 py-1 rounded-lg bg-brand-500/10 hover:bg-brand-500/20 text-brand-400 text-xs font-semibold flex items-center gap-1 transition-colors"
                >
                  <span>View Details</span>
                  <ChevronRight className="w-3.5 h-3.5" />
                </button>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
