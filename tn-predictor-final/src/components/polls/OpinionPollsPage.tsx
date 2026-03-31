import { OPINION_POLLS_2026 } from '../../data/constituencies2026';

export const OpinionPollsPage = () => {
  const enriched = OPINION_POLLS_2026.map((poll) => {
    const midpoint = (v: { min: number; max: number }) => (v.min + v.max) / 2;
    return {
      ...poll,
      seatMid: {
        spa: midpoint(poll.spa),
        nda: midpoint(poll.nda),
        tvk: midpoint(poll.tvk),
        ntk: midpoint(poll.ntk),
      },
    };
  });

  const pollOfPolls = {
    spa: avg(enriched.map((p) => p.seatMid.spa)),
    nda: avg(enriched.map((p) => p.seatMid.nda)),
    tvk: avg(enriched.map((p) => p.seatMid.tvk)),
    ntk: avg(enriched.map((p) => p.seatMid.ntk)),
  };

  return (
    <main className="flex-1 container mx-auto px-4 md:px-8 py-8 h-full">
      <div className="glass-panel rounded-3xl p-6 border border-border/40">
        <h2 className="text-lg font-black uppercase tracking-widest text-foreground/90">Opinion Polls and Poll-of-Polls</h2>
        <p className="text-xs text-muted-foreground mt-2">Aggregated poll seat indication for Tamil Nadu Assembly 2026. This is a directional estimate, not a forecast guarantee.</p>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-5">
          <SeatCard label="SPA" value={pollOfPolls.spa} color="text-red-600" />
          <SeatCard label="NDA" value={pollOfPolls.nda} color="text-green-600" />
          <SeatCard label="TVK" value={pollOfPolls.tvk} color="text-amber-600" />
          <SeatCard label="NTK" value={pollOfPolls.ntk} color="text-rose-600" />
        </div>
      </div>

      <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-4">
        {enriched.map((poll) => (
          <div key={`${poll.agency}-${poll.date}`} className="glass-panel rounded-3xl p-5 border border-border/40">
            <div className="flex justify-between items-center">
              <h3 className="font-black text-sm">{poll.agency}</h3>
              <span className="text-[11px] text-muted-foreground">{poll.date}</span>
            </div>
            <div className="grid grid-cols-2 gap-2 mt-4 text-xs">
              <PollRow label="SPA seats" value={`${poll.spa.min} - ${poll.spa.max}`} />
              <PollRow label="NDA seats" value={`${poll.nda.min} - ${poll.nda.max}`} />
              <PollRow label="TVK seats" value={`${poll.tvk.min} - ${poll.tvk.max}`} />
              <PollRow label="NTK seats" value={`${poll.ntk.min} - ${poll.ntk.max}`} />
              <PollRow label="SPA vote %" value={poll.spaVoteShare.toFixed(1)} />
              <PollRow label="NDA vote %" value={poll.ndaVoteShare.toFixed(1)} />
              <PollRow label="TVK vote %" value={poll.tvkVoteShare.toFixed(1)} />
              <PollRow label="NTK vote %" value={poll.ntkVoteShare.toFixed(1)} />
            </div>
          </div>
        ))}
      </div>
    </main>
  );
};

const avg = (vals: number[]) => vals.length ? Math.round((vals.reduce((a, b) => a + b, 0) / vals.length) * 10) / 10 : 0;

const SeatCard = ({ label, value, color }: { label: string; value: number; color: string }) => (
  <div className="rounded-2xl border border-border/30 p-3 bg-white/60 dark:bg-slate-900/40">
    <div className="text-[10px] font-black uppercase tracking-widest text-muted-foreground">{label}</div>
    <div className={`text-2xl font-black mt-1 ${color}`}>{value}</div>
    <div className="text-[11px] text-muted-foreground">Poll-of-polls seats</div>
  </div>
);

const PollRow = ({ label, value }: { label: string; value: string }) => (
  <div className="flex items-center justify-between rounded-xl border border-border/30 px-3 py-2 bg-white/50 dark:bg-slate-900/30 hover:bg-white/70 dark:hover:bg-slate-900/50 transition-colors">
    <div className="flex items-center gap-2">
      <div className="w-1.5 h-1.5 rounded-full bg-primary/60 shrink-0" />
      <div className="text-[10px] uppercase tracking-wider text-muted-foreground font-bold">{label}</div>
    </div>
    <div className="font-black">{value}</div>
  </div>
);

