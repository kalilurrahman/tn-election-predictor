import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { RotateCcw, ChevronLeft, Zap, TrendingUp, Settings2, Map as MapIcon, Globe } from 'lucide-react';
import { DEFAULT_PARAMS } from '../../data/constituencies2026';
import type { SimulationParams, Region } from '../../data/constituencies2026';
import { cn } from '../../lib/utils';

interface SimulationPanelProps {
  params: SimulationParams;
  onParamChange: (newParams: SimulationParams) => void;
  embedded?: boolean;
}

type Tab = 'global' | 'regional';

const SCENARIO_PRESETS: { name: string; params: Partial<SimulationParams> }[] = [
  { name: 'Baseline', params: { spaSwing: 0, ndaSwing: 0, tvkInfluence: 12, ntkInfluence: 6.5, antiIncumbency: 0, governanceApproval: 0 } },
  { name: 'Anti-Incumbency', params: { spaSwing: -2.5, ndaSwing: 2.0, tvkInfluence: 13.0, ntkInfluence: 7.0, antiIncumbency: 3, governanceApproval: -2 } },
  { name: 'Youth Surge', params: { spaSwing: -2.0, ndaSwing: -1.5, tvkInfluence: 16.0, ntkInfluence: 8.5, youthShiftToTvk: 5 } },
  { name: 'Leadership Wave', params: { spaSwing: 4.0, ndaSwing: -2.0, tvkInfluence: 10.0, ntkInfluence: 5.5, governanceApproval: 4, allianceCohesion: 2 } },
  { name: 'Hung Assembly', params: { spaSwing: -1.5, ndaSwing: -1.5, tvkInfluence: 15.0, ntkInfluence: 9.5, turnoutDelta: -2 } },
];

export const SimulationPanel = ({ params, onParamChange, embedded = false }: SimulationPanelProps) => {
  const [isOpen, setIsOpen] = useState(false);
  const [activeTab, setActiveTab] = useState<Tab>('global');
  const panelOpen = embedded ? true : isOpen;

  const updateParam = (key: keyof SimulationParams, value: number) => {
    onParamChange({ ...params, [key]: value });
  };

  const updateRegionalParam = (region: Region, alliance: 'spa' | 'nda', value: number) => {
    const newRegional = { ...params.regionalSwings };
    newRegional[region] = { ...newRegional[region], [alliance]: value };
    onParamChange({ ...params, regionalSwings: newRegional });
  };
  const updatePhaseParam = (phase: 'early' | 'mid' | 'late', value: number) => {
    onParamChange({ ...params, phaseSwings: { ...params.phaseSwings, [phase]: value } });
  };

  const resetParams = () => onParamChange(DEFAULT_PARAMS);
  const applyScenario = (scenario: Partial<SimulationParams>) => {
    onParamChange({
      ...params,
      ...scenario,
      regionalSwings: params.regionalSwings,
    });
  };

  const regions: Region[] = ['CHENNAI', 'NORTH', 'WEST', 'CENTRAL', 'SOUTH'];

  return (
    <>
      {!embedded && (
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={() => setIsOpen(!isOpen)}
          className="fixed left-6 bottom-6 z-[1001] bg-primary text-primary-foreground p-4 rounded-2xl shadow-2xl flex items-center gap-3 font-bold group overflow-hidden"
        >
          <div className="absolute inset-0 bg-white/20 translate-y-full group-hover:translate-y-0 transition-transform duration-300" />
          {isOpen ? <ChevronLeft className="h-5 w-5" /> : <Settings2 className="h-5 w-5 animate-spin-slow" />}
          <span className="hidden md:inline">Strategy Simulator</span>
          {!isOpen && (
              <span className="absolute -top-1 -right-1 flex h-4 w-4">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-accent opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-4 w-4 bg-accent"></span>
              </span>
          )}
        </motion.button>
      )}

      <AnimatePresence>
        {panelOpen && (
          <motion.div
            initial={embedded ? { opacity: 0, y: 8 } : { x: -400, opacity: 0 }}
            animate={embedded ? { opacity: 1, y: 0 } : { x: 0, opacity: 1 }}
            exit={embedded ? { opacity: 0, y: 8 } : { x: -400, opacity: 0 }}
            transition={{ type: 'spring', damping: 25, stiffness: 200 }}
            className={cn(
              "glass-panel rounded-[2.5rem] shadow-2xl border-border/40 flex flex-col overflow-hidden",
              embedded ? "w-full max-w-none h-full min-h-[700px]" : "fixed left-6 top-24 bottom-24 w-[380px] z-[1000]"
            )}
          >
            {/* Header */}
            <div className="p-6 pb-4 border-b border-border/20 bg-primary/5">
              <div className="flex justify-between items-center mb-4">
                <div>
                  <h2 className="text-xl font-black tracking-tight flex items-center gap-2">
                    <Zap className="h-5 w-5 text-accent fill-accent" />
                    2026 Simulator
                  </h2>
                  <p className="text-[10px] text-muted-foreground font-bold uppercase tracking-widest mt-0.5">Strategic Conflict Engine</p>
                </div>
                <button 
                  onClick={resetParams}
                  className="p-2 hover:bg-background rounded-full transition-colors text-muted-foreground hover:text-primary"
                  title="Reset to Baseline"
                >
                  <RotateCcw className="h-4 w-4" />
                </button>
              </div>

              {/* Tabs */}
              <div className="flex bg-muted/30 p-1 rounded-xl gap-1">
                <button 
                  onClick={() => setActiveTab('global')}
                  className={cn(
                    "flex-1 py-2 text-[10px] font-black uppercase tracking-tighter rounded-lg transition-all flex items-center justify-center gap-1.5",
                    activeTab === 'global' ? "bg-background shadow-sm text-primary" : "text-muted-foreground hover:text-foreground"
                  )}
                >
                  <Globe className="h-3 w-3" /> Global
                </button>
                <button 
                  onClick={() => setActiveTab('regional')}
                  className={cn(
                    "flex-1 py-2 text-[10px] font-black uppercase tracking-tighter rounded-lg transition-all flex items-center justify-center gap-1.5",
                    activeTab === 'regional' ? "bg-background shadow-sm text-primary" : "text-muted-foreground hover:text-foreground"
                  )}
                >
                  <MapIcon className="h-3 w-3" /> Regional
                </button>
              </div>
            </div>

            {/* Scrollable Content */}
            <div className="flex-1 overflow-y-auto p-6 space-y-8 no-scrollbar">
              
              {activeTab === 'global' && (
                <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-8">
                  <div className="space-y-3">
                    <SectionHeader icon={<Zap className="h-4 w-4" />} title="Scenario Presets" />
                    <div className="grid grid-cols-2 gap-2">
                      {SCENARIO_PRESETS.map((scenario) => (
                        <button
                          key={scenario.name}
                          onClick={() => applyScenario(scenario.params)}
                          className="rounded-xl border border-border/40 bg-background/60 px-3 py-2 text-[10px] font-black uppercase tracking-widest text-muted-foreground hover:text-primary hover:border-primary/30 transition-all"
                        >
                          {scenario.name}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Alliance Swings */}
                  <div className="space-y-6">
                    <SectionHeader icon={<TrendingUp className="h-4 w-4" />} title="State-wide Momentum" />
                    
                    <SimulatorSlider 
                      label="SPA Wave (DMK+)"
                      value={params.spaSwing}
                      min={-10} max={10} step={0.5}
                      color="#d72828"
                      onChange={(v) => updateParam('spaSwing', v)}
                    />

                    <SimulatorSlider 
                      label="NDA Wave (AIADMK+)"
                      value={params.ndaSwing}
                      min={-10} max={10} step={0.5}
                      color="#1e7b1e"
                      onChange={(v) => updateParam('ndaSwing', v)}
                    />
                  </div>

                  {/* Disruptors */}
                  <div className="space-y-6 pt-4 border-t border-border/20">
                    <SectionHeader icon={<Zap className="h-4 w-4" />} title="The Disruptor Factor" />
                    
                    <SimulatorSlider 
                      label="Vijay Factor (TVK)"
                      value={params.tvkInfluence}
                      min={0} max={25} step={0.5}
                      color="#FFD700"
                      onChange={(v) => updateParam('tvkInfluence', v)}
                    />

                    <SimulatorSlider 
                      label="Seeman Factor (NTK)"
                      value={params.ntkInfluence}
                      min={0} max={15} step={0.5}
                      color="#de425b"
                      onChange={(v) => updateParam('ntkInfluence', v)}
                    />

                    <SimulatorSlider
                      label="Youth Drift to TVK"
                      value={params.youthShiftToTvk}
                      min={-5} max={8} step={0.5}
                      color="#f59e0b"
                      onChange={(v) => updateParam('youthShiftToTvk', v)}
                    />
                  </div>

                  <div className="space-y-6 pt-4 border-t border-border/20">
                    <SectionHeader icon={<TrendingUp className="h-4 w-4" />} title="Cross-Cutting Dynamics" />
                    <SimulatorSlider label="Anti-Incumbency" value={params.antiIncumbency} min={-6} max={6} step={0.5} color="#64748b" onChange={(v) => updateParam('antiIncumbency', v)} />
                    <SimulatorSlider label="Women Voter Shift" value={params.womenShift} min={-6} max={6} step={0.5} color="#ec4899" onChange={(v) => updateParam('womenShift', v)} />
                    <SimulatorSlider label="Governance Approval" value={params.governanceApproval} min={-6} max={6} step={0.5} color="#22c55e" onChange={(v) => updateParam('governanceApproval', v)} />
                    <SimulatorSlider label="Turnout Delta" value={params.turnoutDelta} min={-8} max={8} step={0.5} color="#3b82f6" onChange={(v) => updateParam('turnoutDelta', v)} />
                    <SimulatorSlider label="Alliance Cohesion" value={params.allianceCohesion} min={-6} max={6} step={0.5} color="#8b5cf6" onChange={(v) => updateParam('allianceCohesion', v)} />
                    <SimulatorSlider label="Campaign Intensity" value={params.campaignIntensity} min={-6} max={6} step={0.5} color="#0ea5e9" onChange={(v) => updateParam('campaignIntensity', v)} />
                  </div>

                  <div className="space-y-4 pt-4 border-t border-border/20">
                    <SectionHeader icon={<Zap className="h-4 w-4" />} title="Multi-Point Momentum Slider" />
                    <p className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">Campaign phases</p>
                    <PhaseSlider label="Early Phase" value={params.phaseSwings.early} onChange={(v) => updatePhaseParam('early', v)} />
                    <PhaseSlider label="Mid Phase" value={params.phaseSwings.mid} onChange={(v) => updatePhaseParam('mid', v)} />
                    <PhaseSlider label="Late Phase" value={params.phaseSwings.late} onChange={(v) => updatePhaseParam('late', v)} />
                  </div>
                </motion.div>
              )}

              {activeTab === 'regional' && (
                <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
                   <SectionHeader icon={<MapIcon className="h-4 w-4" />} title="Region-specific Swings" />
                   {regions.map(region => (
                     <div key={region} className="p-4 rounded-2xl bg-muted/20 border border-border/20 space-y-4">
                        <h4 className="text-[10px] font-black uppercase tracking-widest text-primary flex justify-between items-center">
                          {region} 
                          <span className="text-muted-foreground opacity-50">Impact: High</span>
                        </h4>
                        <SimulatorSlider 
                          label="SPA Shift"
                          value={params.regionalSwings[region].spa}
                          min={-5} max={10} step={0.5}
                          color="#d72828"
                          onChange={(v) => updateRegionalParam(region, 'spa', v)}
                        />
                        <SimulatorSlider 
                          label="NDA Shift"
                          value={params.regionalSwings[region].nda}
                          min={-5} max={10} step={0.5}
                          color="#1e7b1e"
                          onChange={(v) => updateRegionalParam(region, 'nda', v)}
                        />
                     </div>
                   ))}
                </motion.div>
              )}

            </div>

            {/* Footer / Status */}
            <div className="p-6 bg-muted/10 border-t border-border/20">
                <div className="flex items-center gap-3 text-[10px] font-bold text-muted-foreground">
                    <div className="h-2 w-2 rounded-full bg-green-500 animate-pulse" />
                    SIMULATION ENGINE ACTIVE
                </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
};

const SectionHeader = ({ icon, title }: { icon: React.ReactNode, title: string }) => (
  <div className="flex items-center gap-2 mb-4">
    <div className="p-1.5 rounded-lg bg-primary/10 text-primary">
      {icon}
    </div>
    <h3 className="text-xs font-black uppercase tracking-widest text-foreground/80">{title}</h3>
  </div>
);

interface SliderProps {
    label: string;
    value: number;
    min: number;
    max: number;
    step: number;
    color: string;
    onChange: (val: number) => void;
}

const SimulatorSlider = ({ label, value, min, max, step, color, onChange }: SliderProps) => (
  <div className="space-y-3">
    <div className="flex justify-between items-center">
      <span className="text-[11px] font-bold text-muted-foreground uppercase">{label}</span>
      <span className={cn(
        "text-xs font-black px-2 py-0.5 rounded shadow-sm",
        value > 0 ? "bg-green-100 text-green-700" : value < 0 ? "bg-red-100 text-red-700" : "bg-muted text-muted-foreground"
      )}>
        {value > 0 ? '+' : ''}{value}%
      </span>
    </div>
    <input
      type="range"
      min={min}
      max={max}
      step={step}
      value={value}
      onChange={(e) => onChange(parseFloat(e.target.value))}
      className="w-full h-1.5 bg-muted rounded-full appearance-none cursor-pointer accent-primary"
      style={{ accentColor: color }}
    />
  </div>
);

const PhaseSlider = ({ label, value, onChange }: { label: string; value: number; onChange: (v: number) => void }) => (
  <div className="space-y-2">
    <div className="flex items-center justify-between">
      <span className="text-[11px] font-bold text-muted-foreground uppercase">{label}</span>
      <span className="text-xs font-black px-2 py-0.5 rounded bg-muted text-muted-foreground">{value > 0 ? '+' : ''}{value}%</span>
    </div>
    <input
      type="range"
      min={-10}
      max={10}
      step={0.5}
      value={value}
      onChange={(e) => onChange(parseFloat(e.target.value))}
      className="w-full h-1.5 bg-muted rounded-full appearance-none cursor-pointer accent-primary"
    />
  </div>
);
