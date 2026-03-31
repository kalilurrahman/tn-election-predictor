import { useState } from 'react';
import { Target, Bell, Activity, RefreshCw, Shield, X, Loader2, CheckCircle, AlertCircle, ChevronDown } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { cn } from '../../lib/utils';

interface UpdateStatus {
  running: boolean;
  last_run: string | null;
  last_run_duration: string | null;
  constituencies_updated: number;
  total_constituencies: number;
  progress: number;
  log: string[];
}

export const Header = () => {
  const [showAdmin, setShowAdmin] = useState(false);
  const [status, setStatus] = useState<UpdateStatus | null>(null);
  const [updating, setUpdating] = useState(false);
  const [, setPollInterval] = useState<ReturnType<typeof setInterval> | null>(null);

  const startUpdate = async (forceRefresh = false) => {
    setUpdating(true);
    try {
      await fetch('/api/admin/trigger-update', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ force_refresh: forceRefresh }),
      });
      // Start polling status
      const interval = setInterval(async () => {
        const res = await fetch('/api/admin/update-status');
        const data = await res.json();
        setStatus(data);
        if (!data.running) {
          clearInterval(interval);
          setPollInterval(null);
          setUpdating(false);
        }
      }, 800);
      setPollInterval(interval);
    } catch (err) {
      setUpdating(false);
      console.error('Update trigger failed:', err);
    }
  };

  const clearCache = async () => {
    await fetch('/api/admin/clear-cache', { method: 'POST' });
    alert('Cache cleared!');
  };

  const syncCandidates = async () => {
    try {
      const response = await fetch('/api/admin/candidate-sync', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({}),
      });
      if (!response.ok) {
        const text = await response.text();
        throw new Error(text || 'Candidate sync failed');
      }
      alert('Candidate database sync started/completed. Refresh in a few seconds.');
    } catch (err) {
      console.error('Candidate sync failed:', err);
      alert('Candidate sync failed. Check backend logs or source URLs.');
    }
  };

  const timeSince = (iso: string | null) => {
    if (!iso) return 'Never';
    const diff = (Date.now() - new Date(iso).getTime()) / 1000 / 60;
    if (diff < 1) return 'Just now';
    if (diff < 60) return `${Math.round(diff)}m ago`;
    return `${Math.round(diff / 60)}h ago`;
  };

  return (
    <>
      <header className="sticky top-0 z-50 w-full border-b border-border/40 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container flex h-16 items-center justify-between px-4 md:px-8">
          <div className="flex gap-2 items-center">
            <div className="bg-primary/20 p-2 rounded-xl">
              <Target className="h-6 w-6 text-primary" />
            </div>
            <div>
              <h1 className="font-bold text-xl tracking-tight bg-gradient-to-r from-primary to-blue-500 bg-clip-text text-transparent">
                Tamil Nadu Assembly Election 2026
              </h1>
              <p className="text-[10px] text-muted-foreground uppercase font-semibold tracking-wider">
                AI-Powered Psephology
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="hidden md:flex items-center text-sm text-muted-foreground bg-muted/50 px-3 py-1.5 rounded-full border border-border/50">
              <Activity className="h-4 w-4 mr-2 text-green-500" />
              <span>Model: {timeSince(status?.last_run ?? null)}</span>
            </div>

            {/* Admin Panel Button */}
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => setShowAdmin(true)}
              className={cn(
                "flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-bold border transition-all",
                updating
                  ? "bg-amber-50 border-amber-300 text-amber-700"
                  : "bg-primary/10 border-primary/30 text-primary hover:bg-primary/20"
              )}
            >
              {updating ? (
                <><Loader2 className="h-3.5 w-3.5 animate-spin" /> Updating...</>
              ) : (
                <><Shield className="h-3.5 w-3.5" /> Admin<ChevronDown className="h-3 w-3" /></>
              )}
            </motion.button>

            <button className="p-2 hover:bg-muted rounded-full transition-colors relative">
              <Bell className="h-5 w-5 text-foreground/70" />
              <span className="absolute top-1.5 right-1.5 h-2 w-2 rounded-full bg-destructive" />
            </button>
          </div>
        </div>
      </header>

      {/* Admin Panel Modal */}
      <AnimatePresence>
        {showAdmin && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-[3000] flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm"
            onClick={() => setShowAdmin(false)}
          >
            <motion.div
              initial={{ scale: 0.9, y: 20 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.95, y: 10 }}
              className="bg-white dark:bg-slate-900 w-full max-w-2xl rounded-3xl shadow-2xl border border-border/40 overflow-hidden"
              onClick={e => e.stopPropagation()}
            >
              <div className="p-6 border-b border-border/20 flex justify-between items-center bg-slate-50 dark:bg-slate-800/30">
                <div>
                  <h2 className="text-xl font-black flex items-center gap-2">
                    <Shield className="h-5 w-5 text-primary" /> Admin Control Panel
                  </h2>
                  <p className="text-xs text-muted-foreground mt-0.5">Manual update triggers & cache management</p>
                </div>
                <button onClick={() => setShowAdmin(false)} className="p-2 hover:bg-muted rounded-full">
                  <X className="h-5 w-5" />
                </button>
              </div>

              <div className="p-6 space-y-6">
                {/* Status Row */}
                <div className="grid grid-cols-3 gap-3">
                  {[
                    { label: 'Last Update', value: timeSince(status?.last_run ?? null) },
                    { label: 'Duration', value: status?.last_run_duration ?? '—' },
                    { label: 'Progress', value: status ? `${status.constituencies_updated}/${status.total_constituencies}` : '0/234' },
                  ].map(s => (
                    <div key={s.label} className="p-4 rounded-2xl bg-muted/30 border border-border/20 text-center">
                      <div className="text-[10px] font-black uppercase tracking-widest text-muted-foreground mb-1">{s.label}</div>
                      <div className="text-sm font-black">{s.value}</div>
                    </div>
                  ))}
                </div>

                {/* Progress Bar */}
                {status && (
                  <div className="space-y-2">
                    <div className="flex justify-between text-xs font-bold text-muted-foreground">
                      <span>Update Progress</span>
                      <span>{status.progress}%</span>
                    </div>
                    <div className="h-2 bg-muted rounded-full overflow-hidden">
                      <motion.div
                        animate={{ width: `${status.progress}%` }}
                        className="h-full bg-primary rounded-full"
                        transition={{ duration: 0.3 }}
                      />
                    </div>
                    {status.running && (
                      <p className="text-xs text-primary animate-pulse font-bold">
                        Scraping news & updating Bayesian model...
                      </p>
                    )}
                    {!status.running && status.last_run && (
                      <p className="text-xs text-green-600 font-bold flex items-center gap-1">
                        <CheckCircle className="h-3 w-3" /> Update complete
                      </p>
                    )}
                  </div>
                )}

                {/* Action Buttons */}
                <div className="grid grid-cols-2 gap-3">
                  <motion.button
                    whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
                    onClick={() => startUpdate(false)}
                    disabled={updating}
                    className="flex items-center justify-center gap-2 p-4 rounded-2xl bg-primary text-white font-bold text-sm hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {updating ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
                    Smart Update
                  </motion.button>

                  <motion.button
                    whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
                    onClick={() => startUpdate(true)}
                    disabled={updating}
                    className="flex items-center justify-center gap-2 p-4 rounded-2xl bg-amber-500 text-white font-bold text-sm hover:bg-amber-600 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <AlertCircle className="h-4 w-4" />
                    Force Refresh All
                  </motion.button>

                  <motion.button
                    whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
                    onClick={clearCache}
                    className="flex items-center justify-center gap-2 p-4 rounded-2xl border border-border/60 text-muted-foreground font-bold text-sm hover:bg-muted/50"
                  >
                    Clear Cache
                  </motion.button>

                  <motion.button
                    whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
                    onClick={syncCandidates}
                    className="flex items-center justify-center gap-2 p-4 rounded-2xl border border-border/60 text-muted-foreground font-bold text-sm hover:bg-muted/50"
                  >
                    Sync Candidates
                  </motion.button>

                  <a
                    href="/api/predictions/summary"
                    target="_blank"
                    className="flex items-center justify-center gap-2 p-4 rounded-2xl border border-border/60 text-muted-foreground font-bold text-sm hover:bg-muted/50"
                  >
                    View API Docs
                  </a>
                </div>

                {/* Live Log */}
                {status && status.log.length > 0 && (
                  <div className="p-4 rounded-2xl bg-slate-900 dark:bg-black text-green-400 font-mono text-[11px] max-h-40 overflow-y-auto">
                    {status.log.slice(-20).map((line, i) => (
                      <div key={i}>{line}</div>
                    ))}
                  </div>
                )}
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
};
