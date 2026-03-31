import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  Cell,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  PolarAngleAxis,
  PolarGrid,
  PolarRadiusAxis,
  Radar,
  RadarChart,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

const HISTORICAL_RESULTS = [
  { year: 2011, winner: 'AIADMK Alliance', winnerSeats: 203, runnerSeats: 31, turnout: 78.0, dmkVote: 22.4, aiadmkVote: 38.4, ntkVote: 0.4 },
  { year: 2016, winner: 'AIADMK Alliance', winnerSeats: 134, runnerSeats: 98, turnout: 74.3, dmkVote: 31.6, aiadmkVote: 40.8, ntkVote: 1.1 },
  { year: 2021, winner: 'DMK Alliance', winnerSeats: 159, runnerSeats: 75, turnout: 73.6, dmkVote: 37.7, aiadmkVote: 33.3, ntkVote: 6.6 },
];

const ALLIANCE_TREND = [
  { year: '2011', DMK: 22.4, AIADMK: 38.4, NTK: 0.4, BJP: 2.2 },
  { year: '2016', DMK: 31.6, AIADMK: 40.8, NTK: 1.1, BJP: 2.8 },
  { year: '2021', DMK: 37.7, AIADMK: 33.3, NTK: 6.6, BJP: 2.6 },
  { year: '2026*', DMK: 38.9, AIADMK: 36.2, NTK: 6.1, BJP: 4.0 },
];

const REGION_2021 = [
  { name: 'Chennai', value: 16 },
  { name: 'North TN', value: 48 },
  { name: 'West TN', value: 46 },
  { name: 'Central TN', value: 40 },
  { name: 'South TN', value: 84 },
];

const TURNOUT_VS_WIN_MARGIN = [
  { year: '2011', turnout: 78.0, margin: 172 },
  { year: '2016', turnout: 74.3, margin: 36 },
  { year: '2021', turnout: 73.6, margin: 84 },
];

const SEAT_CLASS_BY_YEAR = [
  { year: '2011', safe: 156, swing: 58, bellwether: 20 },
  { year: '2016', safe: 124, swing: 80, bellwether: 30 },
  { year: '2021', safe: 139, swing: 66, bellwether: 29 },
];

const MARGIN_BUCKETS_BY_YEAR = [
  { year: '2011', under3: 18, p3to8: 42, p8to15: 55, over15: 119 },
  { year: '2016', under3: 31, p3to8: 58, p8to15: 61, over15: 84 },
  { year: '2021', under3: 24, p3to8: 49, p8to15: 63, over15: 98 },
];

const CLASS_TRANSITIONS = [
  { period: '2011 → 2016', from: 'Safe', to: 'Safe', count: 90 },
  { period: '2011 → 2016', from: 'Safe', to: 'Swing', count: 48 },
  { period: '2011 → 2016', from: 'Safe', to: 'Bellwether', count: 18 },
  { period: '2011 → 2016', from: 'Swing', to: 'Safe', count: 24 },
  { period: '2011 → 2016', from: 'Swing', to: 'Swing', count: 24 },
  { period: '2011 → 2016', from: 'Swing', to: 'Bellwether', count: 10 },
  { period: '2011 → 2016', from: 'Bellwether', to: 'Safe', count: 10 },
  { period: '2011 → 2016', from: 'Bellwether', to: 'Swing', count: 8 },
  { period: '2011 → 2016', from: 'Bellwether', to: 'Bellwether', count: 2 },
  { period: '2016 → 2021', from: 'Safe', to: 'Safe', count: 82 },
  { period: '2016 → 2021', from: 'Safe', to: 'Swing', count: 28 },
  { period: '2016 → 2021', from: 'Safe', to: 'Bellwether', count: 14 },
  { period: '2016 → 2021', from: 'Swing', to: 'Safe', count: 46 },
  { period: '2016 → 2021', from: 'Swing', to: 'Swing', count: 21 },
  { period: '2016 → 2021', from: 'Swing', to: 'Bellwether', count: 13 },
  { period: '2016 → 2021', from: 'Bellwether', to: 'Safe', count: 11 },
  { period: '2016 → 2021', from: 'Bellwether', to: 'Swing', count: 17 },
  { period: '2016 → 2021', from: 'Bellwether', to: 'Bellwether', count: 2 },
];

const COLORS = ['#d72828', '#1e7b1e', '#0ea5e9', '#f59e0b', '#8b5cf6'];

type SeatDynamicsRow = {
  ac_no: number;
  name: string;
  district: string;
  margin_2021_pct: number;
  projected_margin_pct: number;
  vote_swing_pct: number;
  class_2021: string;
  class_2026: string;
};

type SeatDynamicsPayload = {
  counts_2026: { safe: number; swing: number; bellwether: number };
  transition_counts_2021_to_2026: Record<string, number>;
  safe_seats: SeatDynamicsRow[];
  swing_seats: SeatDynamicsRow[];
  bellwether_seats: SeatDynamicsRow[];
};

type CandidateModelSummaryRow = {
  party: string;
  candidates: number;
  wins: number;
  avg_vote_share_pct: number;
};

type CandidateModelSummary = {
  year: number;
  rows: CandidateModelSummaryRow[];
};

export const StatisticsPage = () => {
  const [seatDynamics, setSeatDynamics] = useState<SeatDynamicsPayload | null>(null);
  const [candidateSummary, setCandidateSummary] = useState<CandidateModelSummary | null>(null);
  const avgTurnout =
    Math.round((HISTORICAL_RESULTS.reduce((sum, row) => sum + row.turnout, 0) / HISTORICAL_RESULTS.length) * 10) / 10;
  const avgWinnerSeats =
    Math.round((HISTORICAL_RESULTS.reduce((sum, row) => sum + row.winnerSeats, 0) / HISTORICAL_RESULTS.length) * 10) / 10;
  const volatilityIndex = Math.round(
    (Math.abs(HISTORICAL_RESULTS[0].winnerSeats - HISTORICAL_RESULTS[1].winnerSeats) +
      Math.abs(HISTORICAL_RESULTS[1].winnerSeats - HISTORICAL_RESULTS[2].winnerSeats)) /
      2
  );
  const closestCycle = HISTORICAL_RESULTS.reduce((prev, curr) =>
    Math.abs(curr.winnerSeats - curr.runnerSeats) < Math.abs(prev.winnerSeats - prev.runnerSeats) ? curr : prev
  );
  const transitionsOnly = CLASS_TRANSITIONS.filter((row) => row.from !== row.to);
  const switchedSeats = transitionsOnly.reduce((sum, row) => sum + row.count, 0);
  const dynamicSwitched = seatDynamics
    ? Object.entries(seatDynamics.transition_counts_2021_to_2026)
        .filter(([key]) => {
          const [from, to] = key.split('->');
          return from !== to;
        })
        .reduce((sum, [, value]) => sum + value, 0)
    : switchedSeats;

  useEffect(() => {
    fetch('/api/elections/seat-dynamics?limit=24')
      .then((res) => res.json())
      .then((json) => setSeatDynamics(json))
      .catch(() => setSeatDynamics(null));
    fetch('/api/elections/candidate-model-summary')
      .then((res) => res.json())
      .then((json) => setCandidateSummary(json))
      .catch(() => setCandidateSummary(null));
  }, []);

  const partyPower = (candidateSummary?.rows ?? [])
    .slice(0, 8)
    .map((row) => ({
      ...row,
      strike_rate: row.candidates > 0 ? Number(((row.wins / row.candidates) * 100).toFixed(2)) : 0,
      influence: row.wins * 3 + row.avg_vote_share_pct,
    }));

  const radarData = partyPower.slice(0, 5).map((row) => ({
    party: row.party,
    wins: row.wins,
    voteShare: row.avg_vote_share_pct,
    strikeRate: row.strike_rate,
  }));

  const swingWaveData = (() => {
    if (!seatDynamics) return [];
    const all = [...seatDynamics.safe_seats, ...seatDynamics.swing_seats, ...seatDynamics.bellwether_seats];
    const bins = [
      { bucket: '< -8%', min: -999, max: -8, seats: 0 },
      { bucket: '-8% to -3%', min: -8, max: -3, seats: 0 },
      { bucket: '-3% to +3%', min: -3, max: 3, seats: 0 },
      { bucket: '+3% to +8%', min: 3, max: 8, seats: 0 },
      { bucket: '> +8%', min: 8, max: 999, seats: 0 },
    ];
    for (const row of all) {
      const v = row.vote_swing_pct;
      const hit = bins.find((b) => v >= b.min && v < b.max);
      if (hit) hit.seats += 1;
    }
    return bins;
  })();

  return (
    <main className="flex-1 container mx-auto px-4 md:px-8 py-8 h-full">
      <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="glass-panel rounded-3xl p-6 md:p-7 border border-border/40 bg-gradient-to-br from-white/85 to-slate-50/60 dark:from-slate-900/70 dark:to-slate-900/40">
        <h2 className="text-2xl md:text-3xl font-black tracking-tight leading-tight">Tamil Nadu Election Statistics and Visualization Hub</h2>
        <p className="text-sm md:text-[15px] text-muted-foreground mt-2 leading-relaxed">
          Historical records, vote-share movement, turnout behavior, and constituency-level context summarized for fast decision making.
        </p>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-5">
          <StatCard title="Elections Covered" value="2011-2026*" subtitle="Assembly cycles" />
          <StatCard title="Total Seats" value="234" subtitle="Tamil Nadu Assembly" />
          <StatCard title="Avg Turnout" value={`${avgTurnout}%`} subtitle="Across 3 cycles" />
          <StatCard title="Current Mode" value="Forecast + Archive" subtitle="Historical + simulation" />
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-3">
          <StatCard title="Avg Winner Seats" value={`${avgWinnerSeats}`} subtitle="Cycle baseline" />
          <StatCard title="Volatility Index" value={`${volatilityIndex}`} subtitle="Seat swing pressure" />
          <StatCard title="Closest Cycle" value={`${closestCycle.year}`} subtitle={`${Math.abs(closestCycle.winnerSeats - closestCycle.runnerSeats)} seat margin`} />
          <StatCard title="Neck & Neck Risk" value="High" subtitle="In swing clusters" />
        </div>
      </motion.div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6 mt-6">
        <ChartPanel title="Seat Outcome History (Winner vs Runner-up)">
          <div className="h-[260px] sm:h-[300px]">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={HISTORICAL_RESULTS}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="year" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="winnerSeats" name="Winner Seats" fill="#d72828" radius={[8, 8, 0, 0]} />
              <Bar dataKey="runnerSeats" name="Runner-up Seats" fill="#1e7b1e" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
          </div>
        </ChartPanel>

        <ChartPanel title="Turnout Trajectory">
          <div className="h-[260px] sm:h-[300px]">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={HISTORICAL_RESULTS}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="year" />
              <YAxis domain={[70, 80]} />
              <Tooltip />
              <Area type="monotone" dataKey="turnout" name="Turnout %" fill="#0ea5e9" stroke="#0284c7" fillOpacity={0.3} />
            </AreaChart>
          </ResponsiveContainer>
          </div>
        </ChartPanel>

        <ChartPanel title="Party Vote Share Trend (Major Blocs)">
          <div className="h-[260px] sm:h-[300px]">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={ALLIANCE_TREND}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="year" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="DMK" stroke="#d72828" strokeWidth={3} dot />
              <Line type="monotone" dataKey="AIADMK" stroke="#1e7b1e" strokeWidth={3} dot />
              <Line type="monotone" dataKey="NTK" stroke="#de425b" strokeWidth={2} dot />
              <Line type="monotone" dataKey="BJP" stroke="#f59e0b" strokeWidth={2} dot />
            </LineChart>
          </ResponsiveContainer>
          </div>
        </ChartPanel>

        <ChartPanel title="Regional Seat Distribution (Assembly Share)">
          <div className="h-[260px] sm:h-[300px]">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie data={REGION_2021} dataKey="value" nameKey="name" outerRadius={100} innerRadius={55} label>
                {REGION_2021.map((entry, index) => (
                  <Cell key={entry.name} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
          </div>
        </ChartPanel>

        <ChartPanel title="Turnout vs Winning Margin">
          <div className="h-[260px] sm:h-[300px]">
          <ResponsiveContainer width="100%" height="100%">
            <ScatterChart>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" dataKey="turnout" name="Turnout" unit="%" />
              <YAxis type="number" dataKey="margin" name="Seat Margin" />
              <Tooltip cursor={{ strokeDasharray: '3 3' }} />
              <Scatter data={TURNOUT_VS_WIN_MARGIN} fill="#6366f1" />
            </ScatterChart>
          </ResponsiveContainer>
          </div>
        </ChartPanel>

        <ChartPanel title="Seat Class Trend (Safe, Swing, Bellwether)">
          <div className="h-[260px] sm:h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={SEAT_CLASS_BY_YEAR}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="year" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="safe" stackId="a" name="Safe Seats" fill="#166534" />
                <Bar dataKey="swing" stackId="a" name="Swing Seats" fill="#f59e0b" />
                <Bar dataKey="bellwether" stackId="a" name="Bellwether Seats" fill="#7c3aed" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </ChartPanel>

        <ChartPanel title="Winning Margin Bands by Election">
          <div className="h-[260px] sm:h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={MARGIN_BUCKETS_BY_YEAR}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="year" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="under3" stackId="b" name="<3%" fill="#dc2626" />
                <Bar dataKey="p3to8" stackId="b" name="3-8%" fill="#fb923c" />
                <Bar dataKey="p8to15" stackId="b" name="8-15%" fill="#eab308" />
                <Bar dataKey="over15" stackId="b" name=">15%" fill="#16a34a" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </ChartPanel>
      </div>

      {candidateSummary && (
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-6 mt-6">
          <ChartPanel title="Party Power Matrix (Wins + Vote Share)">
            <div className="h-[300px] sm:h-[340px]">
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={partyPower}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="party" interval={0} angle={-20} height={60} textAnchor="end" />
                  <YAxis yAxisId="left" />
                  <YAxis yAxisId="right" orientation="right" />
                  <Tooltip />
                  <Legend />
                  <Bar yAxisId="left" dataKey="wins" name="Wins" fill="#0f766e" radius={[8, 8, 0, 0]} />
                  <Line yAxisId="right" type="monotone" dataKey="avg_vote_share_pct" name="Avg Vote Share %" stroke="#7c3aed" strokeWidth={3} dot />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          </ChartPanel>

          <ChartPanel title="Candidate Strength Radar (Top Parties)">
            <div className="h-[300px] sm:h-[340px]">
              <ResponsiveContainer width="100%" height="100%">
                <RadarChart data={radarData}>
                  <PolarGrid />
                  <PolarAngleAxis dataKey="party" />
                  <PolarRadiusAxis />
                  <Tooltip />
                  <Legend />
                  <Radar name="Wins" dataKey="wins" stroke="#dc2626" fill="#dc2626" fillOpacity={0.35} />
                  <Radar name="Strike Rate %" dataKey="strikeRate" stroke="#2563eb" fill="#2563eb" fillOpacity={0.25} />
                </RadarChart>
              </ResponsiveContainer>
            </div>
          </ChartPanel>
        </div>
      )}

      {swingWaveData.length > 0 && (
        <div className="grid grid-cols-1 mt-6">
          <ChartPanel title="Swing Shockwave (Seat Count by Swing Band)">
            <div className="h-[280px] sm:h-[320px]">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={swingWaveData}>
                  <defs>
                    <linearGradient id="shockwave" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#ef4444" stopOpacity={0.8} />
                      <stop offset="95%" stopColor="#f59e0b" stopOpacity={0.2} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="bucket" interval={0} angle={-8} height={40} />
                  <YAxis />
                  <Tooltip />
                  <Area type="monotone" dataKey="seats" stroke="#ef4444" fill="url(#shockwave)" strokeWidth={3} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </ChartPanel>
        </div>
      )}

      <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="glass-panel rounded-3xl p-5 border border-border/40 mt-6">
        <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
          <h3 className="text-sm font-black uppercase tracking-widest">Seat Class Heatmap and Transition Matrix</h3>
          <p className="text-xs text-muted-foreground">Switched class seats across two transitions: {dynamicSwitched}</p>
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mt-4">
          <div className="rounded-2xl border border-border/30 p-4 bg-white/60 dark:bg-slate-900/40">
            <div className="text-xs font-black uppercase tracking-widest mb-3 text-muted-foreground">Heatmap by Election</div>
            <div className="grid grid-cols-4 gap-2 text-xs">
              <div className="font-semibold">Year</div>
              <div className="font-semibold">Safe</div>
              <div className="font-semibold">Swing</div>
              <div className="font-semibold">Bellwether</div>
              {SEAT_CLASS_BY_YEAR.map((row) => (
                <HeatmapRow key={row.year} year={row.year} safe={row.safe} swing={row.swing} bellwether={row.bellwether} />
              ))}
            </div>
          </div>
          <div className="rounded-2xl border border-border/30 p-4 bg-white/60 dark:bg-slate-900/40">
            <div className="text-xs font-black uppercase tracking-widest mb-3 text-muted-foreground">Switch Matrix</div>
            <div className="space-y-2">
              {['2011 → 2016', '2016 → 2021'].map((period, idx) => (
                <motion.div
                  key={period}
                  initial={{ opacity: 0, y: 8 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: idx * 0.08 }}
                  className="rounded-xl border border-border/20 p-3 bg-gradient-to-r from-slate-50 to-white dark:from-slate-900 dark:to-slate-800"
                >
                  <div className="text-xs font-black mb-2">{period}</div>
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <ShiftChip period={period} from="Safe" to="Swing" />
                    <ShiftChip period={period} from="Safe" to="Bellwether" />
                    <ShiftChip period={period} from="Swing" to="Safe" />
                    <ShiftChip period={period} from="Bellwether" to="Swing" />
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        </div>
      </motion.div>

      {seatDynamics && (
        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="mt-6 grid grid-cols-1 xl:grid-cols-3 gap-4">
          <NamedSeatPanel title={`Safe Seats (${seatDynamics.counts_2026.safe})`} rows={seatDynamics.safe_seats} tone="safe" />
          <NamedSeatPanel title={`Swing Seats (${seatDynamics.counts_2026.swing})`} rows={seatDynamics.swing_seats} tone="swing" />
          <NamedSeatPanel title={`Bellwether Seats (${seatDynamics.counts_2026.bellwether})`} rows={seatDynamics.bellwether_seats} tone="bellwether" />
        </motion.div>
      )}

      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.15 }} className="mt-6 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <InsightCard
          title="Turnout-Competitiveness Link"
          text="Lower turnout cycles have shown tighter regional competition and sharper booth-level variance."
        />
        <InsightCard
          title="Historical Pattern"
          text="Tamil Nadu remains strongly bipolar at alliance level, but third-force vote share growth has increased volatility in tight constituencies."
        />
        <InsightCard
          title="Turnout Signal"
          text="Turnout softened after 2011 highs, which usually amplifies localized campaign intensity and candidate-level differentials."
        />
        <InsightCard
          title="2026 Reading"
          text="Current trend signals a competitive frame with a wider uncertainty band in swing seats and stronger need for seat-level micro strategy."
        />
        <InsightCard
          title="Micro-targeting Signal"
          text="High-impact constituencies are increasingly those with narrow 2021 margins and differentiated local issue salience."
        />
      </motion.div>

      <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="glass-panel rounded-3xl p-5 border border-border/40 mt-6">
        <h3 className="text-sm font-black uppercase tracking-widest mb-3">Election Cycle Snapshot Table</h3>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[640px] text-xs">
            <thead>
              <tr className="text-left border-b border-border/40">
                <th className="py-2 pr-4">Year</th>
                <th className="py-2 pr-4">Winner</th>
                <th className="py-2 pr-4">Winner Seats</th>
                <th className="py-2 pr-4">Runner Seats</th>
                <th className="py-2 pr-4">Margin</th>
                <th className="py-2 pr-4">Turnout</th>
              </tr>
            </thead>
            <tbody>
              {HISTORICAL_RESULTS.map((row) => (
                <tr key={row.year} className="border-b border-border/20">
                  <td className="py-2 pr-4 font-semibold">{row.year}</td>
                  <td className="py-2 pr-4">{row.winner}</td>
                  <td className="py-2 pr-4">{row.winnerSeats}</td>
                  <td className="py-2 pr-4">{row.runnerSeats}</td>
                  <td className="py-2 pr-4">{Math.abs(row.winnerSeats - row.runnerSeats)}</td>
                  <td className="py-2 pr-4">{row.turnout}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </motion.div>
    </main>
  );
};

const StatCard = ({ title, value, subtitle }: { title: string; value: string; subtitle: string }) => (
  <div className="rounded-2xl border border-border/30 p-4 bg-gradient-to-br from-white to-slate-50/70 dark:from-slate-900/60 dark:to-slate-900/25 shadow-sm">
    <div className="text-[10px] md:text-[11px] font-black uppercase tracking-widest text-muted-foreground">{title}</div>
    <div className="text-2xl md:text-3xl font-black mt-1">{value}</div>
    <div className="text-[11px] md:text-xs text-muted-foreground mt-1">{subtitle}</div>
  </div>
);

const ChartPanel = ({ title, children }: { title: string; children: React.ReactNode }) => (
  <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="glass-panel rounded-3xl p-5 md:p-6 border border-border/40 bg-white/75 dark:bg-slate-900/55 shadow-sm">
    <h3 className="text-sm md:text-[13px] font-black uppercase tracking-widest mb-3 text-foreground/90">{title}</h3>
    {children}
  </motion.div>
);

const InsightCard = ({ title, text }: { title: string; text: string }) => (
  <div className="rounded-2xl border border-border/30 p-4 bg-gradient-to-br from-white/80 to-slate-50 dark:from-slate-900/60 dark:to-slate-900/20">
    <h4 className="font-black text-sm">{title}</h4>
    <p className="text-xs text-muted-foreground mt-2 leading-relaxed">{text}</p>
  </div>
);

const getIntensity = (value: number, max = 180) => {
  const opacity = Math.min(1, Math.max(0.12, value / max));
  return { backgroundColor: `rgba(37, 99, 235, ${opacity})` };
};

const HeatmapRow = ({ year, safe, swing, bellwether }: { year: string; safe: number; swing: number; bellwether: number }) => (
  <>
    <div className="py-1 font-semibold">{year}</div>
    <div className="py-1 px-2 rounded text-white font-bold" style={getIntensity(safe)}>{safe}</div>
    <div className="py-1 px-2 rounded text-white font-bold" style={getIntensity(swing)}>{swing}</div>
    <div className="py-1 px-2 rounded text-white font-bold" style={getIntensity(bellwether)}>{bellwether}</div>
  </>
);

const ShiftChip = ({ period, from, to }: { period: string; from: string; to: string }) => {
  const flow = CLASS_TRANSITIONS.find((x) => x.period === period && x.from === from && x.to === to);
  return (
    <div className="rounded-lg border border-border/30 px-2 py-1">
      <div className="text-[10px] text-muted-foreground">{from} → {to}</div>
      <div className="text-sm font-black">{flow?.count ?? 0} seats</div>
    </div>
  );
};

const NamedSeatPanel = ({ title, rows, tone }: { title: string; rows: SeatDynamicsRow[]; tone: 'safe' | 'swing' | 'bellwether' }) => {
  const toneClass =
    tone === 'safe'
      ? 'from-emerald-100/80 to-emerald-50 dark:from-emerald-900/20 dark:to-emerald-800/10'
      : tone === 'swing'
        ? 'from-amber-100/80 to-amber-50 dark:from-amber-900/20 dark:to-amber-800/10'
        : 'from-violet-100/80 to-violet-50 dark:from-violet-900/20 dark:to-violet-800/10';
  return (
    <div className={`rounded-2xl border border-border/30 p-4 bg-gradient-to-br ${toneClass}`}>
      <h4 className="font-black text-sm mb-3 uppercase tracking-wider">{title}</h4>
      <div className="space-y-2 max-h-[420px] overflow-y-auto pr-1">
        {rows.slice(0, 14).map((row) => (
          <div key={row.ac_no} className="rounded-lg border border-border/30 p-2 bg-white/80 dark:bg-slate-900/70">
            <div className="text-xs font-bold">{row.name} ({row.ac_no})</div>
            <div className="text-[11px] text-muted-foreground">{row.district}</div>
            <div className="text-[11px] mt-1">
              Swing: <span className="font-semibold">{row.vote_swing_pct > 0 ? '+' : ''}{row.vote_swing_pct}%</span> · 2021 Margin: <span className="font-semibold">{row.margin_2021_pct}%</span> · Projected: <span className="font-semibold">{row.projected_margin_pct}%</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
