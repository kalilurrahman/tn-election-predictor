import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';

type MethodologyPayload = {
  name: string;
  version: string;
  architecture_layers: string[];
  models: string[];
  feature_family: string[];
  validation_strategy: string[];
  data_sources: string[];
};

const FALLBACK: MethodologyPayload = {
  name: 'Tamil Nadu Assembly Election Predictor',
  version: '3.0-methodology',
  architecture_layers: [
    'Data ingestion',
    'Feature engineering',
    'Prediction engine',
    'Forecasting and simulation',
    'Analytics UI',
  ],
  models: [
    'Baseline probabilistic seat prior',
    'Bayesian logit updater for incoming sentiment/news evidence',
    'Scenario simulation with structural feature adjustments',
  ],
  feature_family: [
    'Incumbency fatigue index',
    'Competitiveness index',
    'Welfare saturation proxy',
    'Demographic fractionalization proxy',
    'Sentiment and swing signals',
  ],
  validation_strategy: [
    'Time-aware validation',
    'Constituency holdout checks',
    'Probability calibration checks',
    'Cross-source data consistency checks',
  ],
  data_sources: [
    'ECI / TN CEO official records',
    'ADR / MyNeta candidate affidavits',
    'Historical election datasets',
    'Geo-boundary and demographic data',
    'News and sentiment streams',
  ],
};

export const MethodologyPage = () => {
  const [data, setData] = useState<MethodologyPayload>(FALLBACK);

  useEffect(() => {
    fetch('/api/system/methodology')
      .then((res) => res.json())
      .then((json) => setData(json))
      .catch(() => setData(FALLBACK));
  }, []);

  return (
    <main className="flex-1 container mx-auto px-4 md:px-8 py-8 h-full">
      <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="glass-panel rounded-3xl p-6 border border-border/40">
        <h2 className="text-xl font-black tracking-tight">{data.name} - Methodology</h2>
        <p className="text-sm text-muted-foreground mt-2">
          README-style system architecture and modeling blueprint used for Tamil Nadu Assembly forecast analytics.
        </p>
        <div className="mt-3 inline-flex rounded-xl bg-blue-100 text-blue-700 dark:bg-blue-950/50 dark:text-blue-200 px-3 py-1.5 text-xs font-black uppercase tracking-wider">
          Model version: {data.version}
        </div>
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
        <MethodCard title="Architecture Layers" items={data.architecture_layers} />
        <MethodCard title="Model Stack" items={data.models} />
        <MethodCard title="Feature Engineering" items={data.feature_family} />
        <MethodCard title="Validation Strategy" items={data.validation_strategy} />
      </div>

      <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="glass-panel rounded-3xl p-6 border border-border/40 mt-6">
        <h3 className="text-sm font-black uppercase tracking-widest">Data Sources and Governance</h3>
        <ul className="mt-3 space-y-2 text-sm">
          {data.data_sources.map((item) => (
            <li key={item} className="rounded-xl border border-border/30 px-3 py-2 bg-white/60 dark:bg-slate-900/40">
              {item}
            </li>
          ))}
        </ul>
        <p className="text-xs text-muted-foreground mt-4">
          Disclaimer: Forecasts are probabilistic simulations for informational use only and can differ from ground outcomes.
        </p>
      </motion.div>
    </main>
  );
};

const MethodCard = ({ title, items }: { title: string; items: string[] }) => (
  <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="glass-panel rounded-3xl p-5 border border-border/40">
    <h3 className="text-sm font-black uppercase tracking-widest">{title}</h3>
    <ul className="mt-3 space-y-2 text-sm">
      {items.map((item) => (
        <li key={item} className="rounded-xl border border-border/20 px-3 py-2 bg-white/60 dark:bg-slate-900/40">
          {item}
        </li>
      ))}
    </ul>
  </motion.div>
);
