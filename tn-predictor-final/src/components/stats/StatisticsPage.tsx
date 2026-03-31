import { motion } from 'framer-motion';
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  Cell,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
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

const COLORS = ['#d72828', '#1e7b1e', '#0ea5e9', '#f59e0b', '#8b5cf6'];

export const StatisticsPage = () => {
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

  return (
    <main className="flex-1 container mx-auto px-4 md:px-8 py-8 h-full">
      <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="glass-panel rounded-3xl p-6 border border-border/40">
        <h2 className="text-xl font-black tracking-tight">Tamil Nadu Election Statistics and Visualization Hub</h2>
        <p className="text-sm text-muted-foreground mt-2">
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
      </div>

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
  <div className="rounded-2xl border border-border/30 p-4 bg-white/60 dark:bg-slate-900/40">
    <div className="text-[10px] font-black uppercase tracking-widest text-muted-foreground">{title}</div>
    <div className="text-2xl font-black mt-1">{value}</div>
    <div className="text-[11px] text-muted-foreground mt-1">{subtitle}</div>
  </div>
);

const ChartPanel = ({ title, children }: { title: string; children: React.ReactNode }) => (
  <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="glass-panel rounded-3xl p-5 border border-border/40">
    <h3 className="text-sm font-black uppercase tracking-widest mb-3">{title}</h3>
    {children}
  </motion.div>
);

const InsightCard = ({ title, text }: { title: string; text: string }) => (
  <div className="rounded-2xl border border-border/30 p-4 bg-gradient-to-br from-white/80 to-slate-50 dark:from-slate-900/60 dark:to-slate-900/20">
    <h4 className="font-black text-sm">{title}</h4>
    <p className="text-xs text-muted-foreground mt-2 leading-relaxed">{text}</p>
  </div>
);
