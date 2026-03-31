import { useState } from 'react'
import { Header } from './components/layout/Header'
import { StateOverview } from './components/dashboard/StateOverview'
import { ConstituencyList } from './components/dashboard/ConstituencyList'
import { MapComponent } from './components/dashboard/MapComponent'
import { CandidateRegistryPage } from './components/candidates/CandidateRegistryPage'
import { StrategyLabPage } from './components/strategy/StrategyLabPage'
import { OpinionPollsPage } from './components/polls/OpinionPollsPage'
import { StatisticsPage } from './components/stats/StatisticsPage'
import { DEFAULT_PARAMS } from './data/constituencies2026'
import type { SimulationParams } from './data/constituencies2026'

function App() {
  const [params, setParams] = useState<SimulationParams>(DEFAULT_PARAMS);
  const [view, setView] = useState<'dashboard' | 'strategy' | 'polls' | 'candidates' | 'stats'>('dashboard');

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 text-foreground flex flex-col font-sans relative overflow-x-hidden">
      <Header />

      <div className="container mx-auto px-4 md:px-8 pt-6">
        <div className="overflow-x-auto no-scrollbar">
        <div className="inline-flex rounded-2xl border border-border/40 bg-white/70 dark:bg-slate-900/60 p-1 min-w-max">
          <button
            onClick={() => setView('dashboard')}
            className={`shrink-0 px-4 py-2 rounded-xl text-xs font-black uppercase tracking-widest ${view === 'dashboard' ? 'bg-primary text-white' : 'text-muted-foreground hover:text-foreground'}`}
          >
            Dashboard
          </button>
          <button
            onClick={() => setView('candidates')}
            className={`shrink-0 px-4 py-2 rounded-xl text-xs font-black uppercase tracking-widest ${view === 'candidates' ? 'bg-primary text-white' : 'text-muted-foreground hover:text-foreground'}`}
          >
            Candidate Registry
          </button>
          <button
            onClick={() => setView('strategy')}
            className={`shrink-0 px-4 py-2 rounded-xl text-xs font-black uppercase tracking-widest ${view === 'strategy' ? 'bg-primary text-white' : 'text-muted-foreground hover:text-foreground'}`}
          >
            Strategy Lab
          </button>
          <button
            onClick={() => setView('polls')}
            className={`shrink-0 px-4 py-2 rounded-xl text-xs font-black uppercase tracking-widest ${view === 'polls' ? 'bg-primary text-white' : 'text-muted-foreground hover:text-foreground'}`}
          >
            Opinion Polls
          </button>
          <button
            onClick={() => setView('stats')}
            className={`shrink-0 px-4 py-2 rounded-xl text-xs font-black uppercase tracking-widest ${view === 'stats' ? 'bg-primary text-white' : 'text-muted-foreground hover:text-foreground'}`}
          >
            Statistics
          </button>
        </div>
        </div>
      </div>

      {view === 'dashboard' ? (
        <>
          <main className="flex-1 container mx-auto px-4 md:px-8 py-8 h-full">
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 h-full">
              <div className="lg:col-span-8 flex flex-col gap-8">
                <StateOverview simulationParams={params} />
                <div className="glass-panel p-6 rounded-3xl flex-1 min-h-[500px] relative mt-2 shadow-[inset_0_-10px_30px_rgba(0,0,0,0.05)] border-[rgba(255,255,255,0.8)] backdrop-blur">
                  <div className="absolute top-6 left-6 z-10 pointer-events-none">
                    <h3 className="font-bold text-lg text-foreground/80 flex items-center gap-2 mb-2">Battleground Map</h3>
                    <div className="flex flex-col gap-1.5 opacity-80 backdrop-blur-md bg-white/50 dark:bg-slate-900/50 p-3 rounded-xl border">
                      <div className="text-xs font-semibold mb-1 uppercase tracking-wider text-muted-foreground">Legend</div>
                      <div className="flex items-center gap-2 text-[10px] font-bold"><div className="w-2.5 h-2.5 rounded bg-[#d72828] shadow-sm"></div><span>SPA (DMK+)</span></div>
                      <div className="flex items-center gap-2 text-[10px] font-bold"><div className="w-2.5 h-2.5 rounded bg-[#1e7b1e] shadow-sm"></div><span>NDA (ADMK+)</span></div>
                      <div className="flex items-center gap-2 text-[10px] font-bold"><div className="w-2.5 h-2.5 rounded bg-[#FFD700] shadow-sm"></div><span>TVK (Vijay)</span></div>
                      <div className="flex items-center gap-2 text-[10px] font-bold"><div className="w-2.5 h-2.5 rounded bg-[#de425b] shadow-sm"></div><span>NTK (Seeman)</span></div>
                    </div>
                  </div>
                  <div className="w-full h-full pt-12 md:pt-0">
                    <MapComponent simulationParams={params} />
                  </div>
                </div>
              </div>
              <div className="lg:col-span-4 h-full">
                <ConstituencyList simulationParams={params} />
              </div>
            </div>
          </main>
        </>
      ) : view === 'strategy' ? (
        <StrategyLabPage params={params} onParamChange={setParams} />
      ) : view === 'polls' ? (
        <OpinionPollsPage />
      ) : view === 'stats' ? (
        <StatisticsPage />
      ) : (
        <CandidateRegistryPage />
      )}
      <footer className="border-t border-border/40 bg-white/70 dark:bg-slate-950/70 backdrop-blur px-4 md:px-8 py-5 text-xs text-muted-foreground">
        <div className="container mx-auto flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
          <p>
            Built and curated by Kalilur Rahman -{" "}
            <a
              href="https://kalilurrahman.lovable.app"
              target="_blank"
              rel="noreferrer"
              className="font-semibold text-primary hover:underline"
            >
              kalilurrahman.lovable.app
            </a>
          </p>
          <p className="max-w-3xl">
            Disclaimer: This platform is for informational and simulation purposes only. These projections are model-based estimates; actual on-ground election outcomes may differ.
          </p>
        </div>
      </footer>
    </div>
  )
}

export default App
