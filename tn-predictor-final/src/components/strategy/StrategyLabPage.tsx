import { useMemo } from 'react';
import { MapComponent } from '../dashboard/MapComponent';
import { ConstituencyList } from '../dashboard/ConstituencyList';
import { SimulationPanel } from '../dashboard/SimulationPanel';
import { getDynamicPredictions } from '../../data/constituencies2026';
import type { SimulationParams } from '../../data/constituencies2026';

interface StrategyLabPageProps {
  params: SimulationParams;
  onParamChange: (next: SimulationParams) => void;
}

export const StrategyLabPage = ({ params, onParamChange }: StrategyLabPageProps) => {
  const { summary, constituencies } = useMemo(() => getDynamicPredictions(params), [params]);
  const endState = useMemo(() => {
    if (summary.spaSeats >= 140) return 'SPA strong majority';
    if (summary.ndaSeats >= 140) return 'NDA strong majority';
    if (summary.spaSeats >= 118) return 'SPA narrow majority';
    if (summary.ndaSeats >= 118) return 'NDA narrow majority';
    if (summary.tvkSeats >= 20) return 'High 3rd-front disruption';
    return 'Hung assembly / coalition bargaining';
  }, [summary]);

  const highLeverageSeats = useMemo(() => {
    return [...constituencies]
      .map((seat) => {
        const top = Math.max(
          seat.prediction.spaWinProb,
          seat.prediction.ndaWinProb,
          seat.prediction.tvkWinProb,
          seat.prediction.ntkWinProb
        );
        return { ...seat, volatility: Math.max(0, 100 - top) };
      })
      .sort((a, b) => b.volatility - a.volatility)
      .slice(0, 12);
  }, [constituencies]);

  return (
    <main className="flex-1 container mx-auto px-4 md:px-8 py-8 h-full">
      <div className="grid grid-cols-1 xl:grid-cols-12 gap-8">
        <div className="xl:col-span-4 min-h-[680px]">
          <SimulationPanel params={params} onParamChange={onParamChange} embedded />
        </div>
        <div className="xl:col-span-8 space-y-8">
          <div className="glass-panel rounded-3xl p-6 border border-border/40">
            <h2 className="text-lg font-black uppercase tracking-widest text-foreground/90">Strategy End-State Explorer</h2>
            <p className="text-xs text-muted-foreground mt-2">Seat-level and statewide outputs react to the control panel in real time.</p>
            <div className="inline-flex mt-3 rounded-xl px-3 py-1.5 text-[11px] font-black uppercase tracking-widest bg-amber-100 text-amber-700">
              End-state: {endState}
            </div>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mt-5">
              <Metric title="SPA" value={summary.spaSeats} />
              <Metric title="NDA" value={summary.ndaSeats} />
              <Metric title="TVK" value={summary.tvkSeats} />
              <Metric title="NTK" value={summary.ntkSeats} />
              <Metric title="Toss-ups" value={summary.tossups} />
            </div>
          </div>

          <div className="glass-panel rounded-3xl p-6 border border-border/40">
            <h3 className="text-sm font-black uppercase tracking-widest text-foreground/90">Seat-Level Strategy Targets</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mt-4">
              {highLeverageSeats.map((seat) => (
                <div key={seat.acNo} className="rounded-2xl border border-border/40 p-3 bg-white/50 dark:bg-slate-900/40">
                  <div className="text-[10px] font-black uppercase tracking-widest text-muted-foreground">AC #{seat.acNo}</div>
                  <div className="font-bold text-sm">{seat.name}</div>
                  <div className="text-[11px] text-muted-foreground mt-1">{seat.district} • Volatility {seat.volatility.toFixed(1)}%</div>
                  <div className="text-[11px] font-bold mt-1 text-primary">Lead: {seat.prediction.predictedWinner} • Margin: {seat.prediction.margin}</div>
                </div>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
            <div className="lg:col-span-8 min-h-[520px]">
              <MapComponent simulationParams={params} />
            </div>
            <div className="lg:col-span-4 min-h-[520px]">
              <ConstituencyList simulationParams={params} />
            </div>
          </div>
        </div>
      </div>
    </main>
  );
};

const Metric = ({ title, value }: { title: string; value: number }) => (
  <div className="rounded-2xl border border-border/30 p-3 bg-white/60 dark:bg-slate-900/40">
    <div className="text-[10px] font-black uppercase tracking-widest text-muted-foreground">{title}</div>
    <div className="text-2xl font-black mt-1">{value}</div>
  </div>
);
