import { useEffect, useMemo, useState } from 'react';
import { motion } from 'framer-motion';

type AdminStatus = {
  running?: boolean;
  last_run?: string | null;
  last_result?: unknown;
  mode?: string;
};

type ModelCatalog = {
  sentiment_models?: Array<{ id: string; label: string; hf_model: string; description?: string }>;
  forecast_profiles?: Array<{ id: string; label: string; multiplier: number; description?: string }>;
};

type ModelSelectionResponse = {
  current: {
    sentiment_model_id?: string;
    sentiment_hf_model?: string;
    forecast_profile_id?: string;
    updated_at?: string;
  };
  catalog: ModelCatalog;
};

type CandidatePreset = { id: string; label: string; urls: string[]; notes?: string };

type DatasetCatalog = {
  datasets?: Array<{
    dataset_id: string;
    name: string;
    priority: number;
    url: string;
    format: string;
    requires_auth: boolean;
    notes: string;
  }>;
};

type AdminAuthStatus = {
  auth_required: boolean;
  configured: boolean;
};

const jsonHeaders = { 'Content-Type': 'application/json' };
const ADMIN_KEY_STORAGE = 'tn_admin_key';

export const AdminConsolePage = () => {
  const [modelData, setModelData] = useState<ModelSelectionResponse | null>(null);
  const [candidateStatus, setCandidateStatus] = useState<AdminStatus | null>(null);
  const [datasetStatus, setDatasetStatus] = useState<AdminStatus | null>(null);
  const [extractStatus, setExtractStatus] = useState<AdminStatus | null>(null);
  const [checkin, setCheckin] = useState<Record<string, unknown> | null>(null);
  const [candidatePresets, setCandidatePresets] = useState<CandidatePreset[]>([]);
  const [datasetCatalog, setDatasetCatalog] = useState<DatasetCatalog | null>(null);
  const [selectedSentiment, setSelectedSentiment] = useState('');
  const [selectedForecast, setSelectedForecast] = useState('');
  const [candidateSources, setCandidateSources] = useState('');
  const [intervalMinutes, setIntervalMinutes] = useState('180');
  const [busyKey, setBusyKey] = useState<string | null>(null);
  const [message, setMessage] = useState<string>('');
  const [authStatus, setAuthStatus] = useState<AdminAuthStatus>({ auth_required: true, configured: false });
  const [adminKeyInput, setAdminKeyInput] = useState('');
  const [isUnlocked, setIsUnlocked] = useState(false);

  useEffect(() => {
    const saved = typeof window !== 'undefined' ? window.sessionStorage.getItem(ADMIN_KEY_STORAGE) || '' : '';
    if (saved) {
      setAdminKeyInput(saved);
    }
  }, []);

  const adminFetch = (url: string, init?: RequestInit) => {
    const headers = new Headers(init?.headers || {});
    if (adminKeyInput.trim()) {
      headers.set('X-Admin-Key', adminKeyInput.trim());
    }
    return fetch(url, { ...init, headers });
  };

  const ensureUnlocked = async (showMessage = true) => {
    const statusResp = await fetch('/api/admin/auth/status').catch(() => null);
    if (!statusResp?.ok) {
      if (showMessage) setMessage('Unable to read admin auth status from server.');
      return false;
    }
    const statusPayload = (await statusResp.json()) as AdminAuthStatus;
    setAuthStatus(statusPayload);

    if (!statusPayload.auth_required) {
      setIsUnlocked(true);
      return true;
    }

    if (!statusPayload.configured) {
      setIsUnlocked(false);
      if (showMessage) setMessage('Admin key is required, but server key is not configured. Set ADMIN_ACCESS_KEY in environment.');
      return false;
    }

    if (!adminKeyInput.trim()) {
      setIsUnlocked(false);
      if (showMessage) setMessage('Enter the admin key to unlock protected admin actions.');
      return false;
    }

    const verifyResp = await adminFetch('/api/admin/auth/verify').catch(() => null);
    if (!verifyResp?.ok) {
      setIsUnlocked(false);
      const payload = await verifyResp?.json().catch(() => ({}));
      if (showMessage) setMessage((payload as any)?.detail || 'Invalid admin key.');
      return false;
    }

    if (typeof window !== 'undefined') {
      window.sessionStorage.setItem(ADMIN_KEY_STORAGE, adminKeyInput.trim());
    }
    setIsUnlocked(true);
    return true;
  };

  const refreshAll = async () => {
    setMessage('');
    const unlocked = await ensureUnlocked(false);
    if (!unlocked) {
      return;
    }

    const [
      modelsRes,
      candidateStatusRes,
      datasetStatusRes,
      extractStatusRes,
      checkinRes,
      presetsRes,
      datasetCatalogRes,
    ] = await Promise.all([
      adminFetch('/api/admin/models').then((res) => res.json()).catch(() => null),
      adminFetch('/api/admin/candidate-sync/status').then((res) => res.json()).catch(() => null),
      adminFetch('/api/admin/datasets/bootstrap/status').then((res) => res.json()).catch(() => null),
      adminFetch('/api/admin/extract-worker/status').then((res) => res.json()).catch(() => null),
      adminFetch('/api/admin/extract-checkin/latest').then((res) => res.json()).catch(() => null),
      adminFetch('/api/admin/candidate-sync/presets').then((res) => res.json()).catch(() => []),
      adminFetch('/api/admin/datasets/catalog').then((res) => res.json()).catch(() => null),
    ]);

    setModelData(modelsRes);
    setCandidateStatus(candidateStatusRes);
    setDatasetStatus(datasetStatusRes);
    setExtractStatus(extractStatusRes);
    setCheckin(checkinRes);
    setCandidatePresets(parseCandidatePresets(presetsRes));
    setDatasetCatalog(datasetCatalogRes);

    if (modelsRes?.current) {
      setSelectedSentiment(modelsRes.current.sentiment_model_id || '');
      setSelectedForecast(modelsRes.current.forecast_profile_id || '');
    }
  };

  useEffect(() => {
    refreshAll().catch(() => undefined);
  }, []);

  const presetSourceText = useMemo(
    () => candidatePresets.flatMap((preset) => preset.urls).join('\n'),
    [candidatePresets],
  );

  const runAction = async (key: string, action: () => Promise<Response>) => {
    const unlocked = await ensureUnlocked(true);
    if (!unlocked) return;

    setBusyKey(key);
    setMessage('');
    try {
      const response = await action();
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error((payload as any)?.message || (payload as any)?.detail || `Request failed with ${response.status}`);
      }
      setMessage((payload as any)?.message || (payload as any)?.status || 'Action completed successfully.');
      await refreshAll();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Unable to complete admin action.');
    } finally {
      setBusyKey(null);
    }
  };

  const lockConsole = () => {
    if (typeof window !== 'undefined') {
      window.sessionStorage.removeItem(ADMIN_KEY_STORAGE);
    }
    setAdminKeyInput('');
    setIsUnlocked(false);
    setMessage('Admin console locked.');
  };

  return (
    <main className="flex-1 container mx-auto px-4 md:px-8 py-8">
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass-panel rounded-3xl p-6 md:p-7 border border-border/40 bg-gradient-to-br from-white/85 to-slate-50/60 dark:from-slate-900/70 dark:to-slate-900/40"
      >
        <h2 className="text-2xl md:text-3xl font-black tracking-tight leading-tight">Admin Console</h2>
        <p className="text-sm md:text-[15px] text-muted-foreground mt-2 leading-relaxed">
          Trigger backend sync pipelines, choose forecasting models, inspect extraction check-ins, and manage dataset refresh operations from one place.
        </p>
        <div className="mt-3 rounded-xl border border-border/30 bg-white/70 dark:bg-slate-900/50 px-4 py-3 text-xs leading-relaxed">
          <span className="font-black uppercase tracking-widest text-muted-foreground">Access</span>
          <div className="mt-1">Open from top menu: <span className="font-semibold">Admin</span>, or use URL query <span className="font-semibold">`?view=admin`</span>.</div>
          <div className="mt-1">Protection: set server env <span className="font-semibold">`ADMIN_ACCESS_KEY`</span>, then enter the same key below.</div>
        </div>

        <div className="mt-4 rounded-2xl border border-border/30 bg-white/75 dark:bg-slate-900/55 p-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 items-end">
            <label className="text-xs font-black uppercase tracking-widest text-muted-foreground md:col-span-2">
              Admin key
              <input
                type="password"
                value={adminKeyInput}
                onChange={(event) => setAdminKeyInput(event.target.value)}
                placeholder="Enter ADMIN_ACCESS_KEY"
                className="mt-2 w-full rounded-2xl border border-border/40 bg-white/80 dark:bg-slate-900/70 px-4 py-3 text-sm font-medium"
              />
            </label>
            <div className="flex gap-2">
              <button
                onClick={() => ensureUnlocked(true).then((ok) => ok && setMessage('Admin console unlocked.'))}
                className="rounded-xl bg-primary px-4 py-3 text-xs font-black uppercase tracking-widest text-white"
              >
                Unlock
              </button>
              <button
                onClick={lockConsole}
                className="rounded-xl border border-border/40 px-4 py-3 text-xs font-black uppercase tracking-widest"
              >
                Lock
              </button>
            </div>
          </div>
          <div className="mt-3 grid grid-cols-1 sm:grid-cols-3 gap-2 text-xs">
            <MiniStat label="Auth Required" value={authStatus.auth_required ? 'Yes' : 'No'} />
            <MiniStat label="Server Configured" value={authStatus.configured ? 'Yes' : 'No'} />
            <MiniStat label="Session" value={isUnlocked ? 'Unlocked' : 'Locked'} />
          </div>
        </div>

        <div className="mt-4 flex flex-wrap gap-3">
          <button
            onClick={() => refreshAll().then(() => setMessage('Admin dashboard refreshed.')).catch(() => setMessage('Refresh failed.'))}
            className="rounded-xl bg-primary px-4 py-2 text-xs font-black uppercase tracking-widest text-white"
          >
            Refresh Admin State
          </button>
          {message && <div className="rounded-xl bg-slate-100 dark:bg-slate-800 px-4 py-2 text-xs font-semibold">{message}</div>}
        </div>
      </motion.div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6 mt-6">
        <Panel title="Model Control" subtitle="Choose the active sentiment backend and forecast aggressiveness profile.">
          <div className="grid grid-cols-1 gap-4">
            <label className="text-xs font-black uppercase tracking-widest text-muted-foreground">
              Sentiment model
              <select
                value={selectedSentiment}
                onChange={(event) => setSelectedSentiment(event.target.value)}
                className="mt-2 w-full rounded-2xl border border-border/40 bg-white/80 dark:bg-slate-900/70 px-4 py-3 text-sm font-medium"
              >
                {(modelData?.catalog?.sentiment_models || []).map((model) => (
                  <option key={model.id} value={model.id}>
                    {model.label}
                  </option>
                ))}
              </select>
            </label>

            <label className="text-xs font-black uppercase tracking-widest text-muted-foreground">
              Forecast profile
              <select
                value={selectedForecast}
                onChange={(event) => setSelectedForecast(event.target.value)}
                className="mt-2 w-full rounded-2xl border border-border/40 bg-white/80 dark:bg-slate-900/70 px-4 py-3 text-sm font-medium"
              >
                {(modelData?.catalog?.forecast_profiles || []).map((profile) => (
                  <option key={profile.id} value={profile.id}>
                    {profile.label}
                  </option>
                ))}
              </select>
            </label>

            <div className="rounded-2xl border border-border/30 bg-white/60 dark:bg-slate-900/50 p-4 text-xs leading-relaxed">
              <div className="font-black uppercase tracking-widest text-muted-foreground">Current runtime</div>
              <div className="mt-2">Sentiment HF model: <span className="font-semibold">{modelData?.current?.sentiment_hf_model || 'unknown'}</span></div>
              <div>Forecast profile: <span className="font-semibold">{modelData?.current?.forecast_profile_id || 'balanced'}</span></div>
              <div>Updated at: <span className="font-semibold">{formatDate(modelData?.current?.updated_at)}</span></div>
            </div>

            <button
              onClick={() =>
                runAction('models', () =>
                  adminFetch('/api/admin/models/select', {
                    method: 'POST',
                    headers: jsonHeaders,
                    body: JSON.stringify({
                      sentiment_model_id: selectedSentiment || undefined,
                      forecast_profile_id: selectedForecast || undefined,
                    }),
                  }),
                )
              }
              disabled={busyKey === 'models'}
              className="rounded-2xl bg-primary px-4 py-3 text-xs font-black uppercase tracking-widest text-white disabled:opacity-60"
            >
              {busyKey === 'models' ? 'Saving model selection...' : 'Apply model selection'}
            </button>
          </div>
        </Panel>

        <Panel title="Candidate Sync" subtitle="Run constituency candidate refresh using ECI/public-source presets or custom URLs.">
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-3 text-xs">
              <MiniStat label="Status" value={candidateStatus?.running ? 'Running' : 'Idle'} />
              <MiniStat label="Last run" value={formatDate(candidateStatus?.last_run)} />
            </div>

            <label className="text-xs font-black uppercase tracking-widest text-muted-foreground">
              Source URLs
              <textarea
                value={candidateSources}
                onChange={(event) => setCandidateSources(event.target.value)}
                placeholder={presetSourceText || 'One URL per line'}
                className="mt-2 min-h-[140px] w-full rounded-2xl border border-border/40 bg-white/80 dark:bg-slate-900/70 px-4 py-3 text-sm font-medium"
              />
            </label>

            <div className="rounded-2xl border border-border/30 bg-white/60 dark:bg-slate-900/50 p-4">
              <div className="text-xs font-black uppercase tracking-widest text-muted-foreground">Available presets</div>
              <div className="mt-3 space-y-2">
                {candidatePresets.slice(0, 6).map((preset) => (
                  <button
                    key={preset.id}
                    onClick={() =>
                      setCandidateSources((current) => {
                        const incoming = preset.urls.join('\n');
                        return current.trim() ? `${current.trim()}\n${incoming}` : incoming;
                      })
                    }
                    className="w-full rounded-xl border border-border/30 bg-white/80 dark:bg-slate-900/60 px-3 py-2 text-left text-xs"
                  >
                    <div className="font-bold">{preset.label}</div>
                    <div className="text-muted-foreground break-all">{preset.urls.join(' | ')}</div>
                  </button>
                ))}
              </div>
            </div>

            <button
              onClick={() =>
                runAction('candidate-sync', () =>
                  adminFetch('/api/admin/candidate-sync', {
                    method: 'POST',
                    headers: jsonHeaders,
                    body: JSON.stringify({
                      source_urls: splitLines(candidateSources),
                    }),
                  }),
                )
              }
              disabled={busyKey === 'candidate-sync'}
              className="rounded-2xl bg-primary px-4 py-3 text-xs font-black uppercase tracking-widest text-white disabled:opacity-60"
            >
              {busyKey === 'candidate-sync' ? 'Running candidate sync...' : 'Run candidate sync'}
            </button>
          </div>
        </Panel>

        <Panel title="Dataset Bootstrap" subtitle="Download public TN datasets and regenerate processed feature artifacts.">
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-3 text-xs">
              <MiniStat label="Status" value={datasetStatus?.running ? 'Running' : 'Idle'} />
              <MiniStat label="Last run" value={formatDate(datasetStatus?.last_run)} />
            </div>

            <div className="rounded-2xl border border-border/30 bg-white/60 dark:bg-slate-900/50 p-4">
              <div className="text-xs font-black uppercase tracking-widest text-muted-foreground">Dataset catalog</div>
              <div className="mt-3 space-y-2 max-h-[240px] overflow-y-auto pr-1">
                {(datasetCatalog?.datasets || []).map((dataset) => (
                  <div key={dataset.dataset_id} className="rounded-xl border border-border/20 px-3 py-2 text-xs">
                    <div className="font-bold">{dataset.name}</div>
                    <div className="text-muted-foreground">{dataset.format} | priority {dataset.priority} | {dataset.requires_auth ? 'manual auth' : 'auto-fetchable'}</div>
                  </div>
                ))}
              </div>
            </div>

            <button
              onClick={() => runAction('bootstrap', () => adminFetch('/api/admin/datasets/bootstrap', { method: 'POST' }))}
              disabled={busyKey === 'bootstrap'}
              className="rounded-2xl bg-primary px-4 py-3 text-xs font-black uppercase tracking-widest text-white disabled:opacity-60"
            >
              {busyKey === 'bootstrap' ? 'Bootstrapping datasets...' : 'Run dataset bootstrap'}
            </button>
          </div>
        </Panel>

        <Panel title="Extraction Worker" subtitle="Generate admin review check-ins or start a recurring extraction daemon.">
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-3 text-xs">
              <MiniStat label="Worker status" value={extractStatus?.running ? 'Running' : 'Idle'} />
              <MiniStat label="Mode" value={extractStatus?.mode || 'disabled'} />
            </div>

            <label className="text-xs font-black uppercase tracking-widest text-muted-foreground">
              Daemon interval minutes
              <input
                value={intervalMinutes}
                onChange={(event) => setIntervalMinutes(event.target.value)}
                className="mt-2 w-full rounded-2xl border border-border/40 bg-white/80 dark:bg-slate-900/70 px-4 py-3 text-sm font-medium"
              />
            </label>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <button
                onClick={() => runAction('extract-once', () => adminFetch('/api/admin/extract-worker/run-once', { method: 'POST' }))}
                disabled={busyKey === 'extract-once'}
                className="rounded-2xl bg-primary px-4 py-3 text-xs font-black uppercase tracking-widest text-white disabled:opacity-60"
              >
                {busyKey === 'extract-once' ? 'Generating check-in...' : 'Run extract once'}
              </button>
              <button
                onClick={() =>
                  runAction('extract-daemon', () =>
                    adminFetch('/api/admin/extract-worker/start-daemon', {
                      method: 'POST',
                      headers: jsonHeaders,
                      body: JSON.stringify({ interval_minutes: Number(intervalMinutes || '180') }),
                    }),
                  )
                }
                disabled={busyKey === 'extract-daemon'}
                className="rounded-2xl border border-primary/30 bg-primary/10 px-4 py-3 text-xs font-black uppercase tracking-widest text-primary disabled:opacity-60"
              >
                {busyKey === 'extract-daemon' ? 'Starting daemon...' : 'Start background daemon'}
              </button>
            </div>

            <div className="rounded-2xl border border-border/30 bg-white/60 dark:bg-slate-900/50 p-4">
              <div className="text-xs font-black uppercase tracking-widest text-muted-foreground">Latest admin check-in</div>
              <pre className="mt-3 max-h-[220px] overflow-auto rounded-xl bg-slate-950 p-3 text-[11px] text-slate-100 whitespace-pre-wrap">
                {JSON.stringify(checkin, null, 2)}
              </pre>
            </div>
          </div>
        </Panel>
      </div>
    </main>
  );
};

const Panel = ({ title, subtitle, children }: { title: string; subtitle: string; children: React.ReactNode }) => (
  <motion.section
    initial={{ opacity: 0, y: 8 }}
    animate={{ opacity: 1, y: 0 }}
    className="glass-panel rounded-3xl p-5 md:p-6 border border-border/40 bg-white/75 dark:bg-slate-900/55 shadow-sm"
  >
    <h3 className="text-sm md:text-[13px] font-black uppercase tracking-widest text-foreground/90">{title}</h3>
    <p className="mt-2 text-sm text-muted-foreground leading-relaxed">{subtitle}</p>
    <div className="mt-4">{children}</div>
  </motion.section>
);

const MiniStat = ({ label, value }: { label: string; value: string }) => (
  <div className="rounded-2xl border border-border/30 bg-white/70 dark:bg-slate-900/50 px-4 py-3">
    <div className="text-[10px] font-black uppercase tracking-widest text-muted-foreground">{label}</div>
    <div className="mt-1 text-sm font-black">{value}</div>
  </div>
);

const formatDate = (value?: string | null) => {
  if (!value) return 'Not yet run';
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  return parsed.toLocaleString();
};

const splitLines = (value: string) =>
  value
    .split('\n')
    .map((item) => item.trim())
    .filter(Boolean);

const parseCandidatePresets = (raw: unknown): CandidatePreset[] => {
  if (Array.isArray(raw)) {
    return raw
      .map((item: any) => ({
        id: String(item?.id || 'preset'),
        label: String(item?.label || item?.id || 'Preset'),
        urls: item?.url ? [String(item.url)] : Array.isArray(item?.urls) ? item.urls.map((url: any) => String(url)) : [],
        notes: item?.notes ? String(item.notes) : undefined,
      }))
      .filter((preset) => preset.urls.length > 0);
  }

  const data = raw as any;
  if (data && Array.isArray(data.presets)) {
    return data.presets
      .map((item: any) => ({
        id: String(item?.id || 'preset'),
        label: String(item?.label || item?.id || 'Preset'),
        urls: Array.isArray(item?.urls) ? item.urls.map((url: any) => String(url)) : [],
        notes: item?.notes ? String(item.notes) : undefined,
      }))
      .filter((preset: CandidatePreset) => preset.urls.length > 0);
  }

  return [];
};
