import { useEffect, useMemo, useState } from 'react';
import { GeoJSON, MapContainer, TileLayer } from 'react-leaflet';
import type { FeatureCollection, GeoJsonObject } from 'geojson';
import 'leaflet/dist/leaflet.css';

type CandidateRow = {
  ac_no: number;
  ac_name: string;
  district: string;
  candidate_name: string;
  party: string;
  alliance: string;
  eci_approved: boolean;
  party_approved: boolean;
  is_incumbent?: boolean;
  is_rerunner?: boolean;
  is_celebrity?: boolean;
  nomination_status?: string;
  education?: string;
  profession?: string;
  age?: number;
  gender?: string;
  assets?: string;
  liabilities?: string;
  criminal_cases?: number;
  affidavit_url?: string;
  validation_reports?: string[];
  source?: string;
};

type ElectionHistory = {
  elections: Array<{
    year: number;
    winner_alliance: string;
    winner_seats: number | null;
    runner_alliance: string;
    runner_seats: number | null;
    turnout_percent: number | null;
    summary: string;
  }>;
};

type CommunitySplit = {
  source_note: string;
  rows: Array<{ group: string; vote_share_estimate: number }>;
};

export const CandidateRegistryPage = () => {
  const [geoData, setGeoData] = useState<FeatureCollection | null>(null);
  const [selectedAc, setSelectedAc] = useState<number | null>(null);
  const [selectedName, setSelectedName] = useState<string>('Select a constituency on map');
  const [candidates, setCandidates] = useState<CandidateRow[]>([]);
  const [history, setHistory] = useState<ElectionHistory | null>(null);
  const [communitySplit, setCommunitySplit] = useState<CommunitySplit | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetch('/tn_assembly.geojson')
      .then((res) => res.json())
      .then((data) => setGeoData(data))
      .catch(() => setGeoData(null));

    fetch('/api/elections/history')
      .then((res) => res.json())
      .then((data) => setHistory(data))
      .catch(() => setHistory(null));
  }, []);

  useEffect(() => {
    if (!selectedAc) return;
    setLoading(true);
    Promise.all([
      fetch(`/api/candidates?ac_no=${selectedAc}`).then((res) => res.json()).catch(() => ({ rows: [] })),
      fetch(`/api/elections/community-split?ac_no=${selectedAc}`).then((res) => res.json()).catch(() => ({ rows: [] })),
    ])
      .then(([candidateData, communityData]) => {
        setCandidates(candidateData.rows || []);
        setCommunitySplit(communityData);
      })
      .finally(() => setLoading(false));
  }, [selectedAc]);

  const approvedCount = useMemo(
    () => candidates.filter((candidate) => candidate.eci_approved || candidate.party_approved).length,
    [candidates],
  );

  const incumbentCount = candidates.filter((candidate) => candidate.is_incumbent).length;
  const rerunnerCount = candidates.filter((candidate) => candidate.is_rerunner).length;
  const celebCount = candidates.filter((candidate) => candidate.is_celebrity).length;

  return (
    <main className="flex-1 container mx-auto px-4 md:px-8 py-8">
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        <section className="lg:col-span-5 rounded-3xl border border-border/40 overflow-hidden bg-gradient-to-br from-white/85 to-slate-50/60 dark:from-slate-900/70 dark:to-slate-900/40 shadow-sm">
          <div className="px-5 py-4 border-b border-border/30 flex items-center justify-between">
            <h3 className="font-black text-sm md:text-[13px] uppercase tracking-widest">Constituency Selector</h3>
            <a href="/api/candidates/export.csv" target="_blank" rel="noreferrer" className="text-xs font-bold text-primary hover:underline">
              Download CSV
            </a>
          </div>
          <div className="h-[560px]">
            {geoData ? (
              <MapContainer center={[11.0, 78.5]} zoom={7} style={{ height: '100%', width: '100%' }} attributionControl={false}>
                <TileLayer url="https://{s}.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}{r}.png" />
                <GeoJSON
                  data={geoData as GeoJsonObject}
                  onEachFeature={(feature: any, layer: any) => {
                    const acNo = Number(feature?.properties?.ac_no || 0);
                    const acName = String(feature?.properties?.ac_name || `AC #${acNo}`);
                    layer.bindTooltip(`<b>${acName}</b>`, { sticky: true });
                    layer.on('click', () => {
                      setSelectedAc(acNo);
                      setSelectedName(acName);
                    });
                  }}
                />
              </MapContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-sm text-muted-foreground">Unable to load assembly map.</div>
            )}
          </div>
        </section>

        <section className="lg:col-span-7 rounded-3xl border border-border/40 bg-gradient-to-br from-white/85 to-slate-50/60 dark:from-slate-900/70 dark:to-slate-900/40 shadow-sm">
          <div className="px-5 py-4 border-b border-border/30">
            <h3 className="font-black text-base md:text-lg uppercase tracking-widest">Comprehensive Candidate Dossier</h3>
            <p className="text-xs md:text-sm text-muted-foreground mt-1">{selectedName} {selectedAc ? `(AC #${selectedAc})` : ''}</p>
            <p className="text-[11px] text-muted-foreground mt-1">
              Validation mode: ECI/party/public-source tagged records. Use citation links in each card for audit trail.
            </p>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2 mt-2 text-[11px]">
              <Stat label="Verified" value={`${approvedCount}/${candidates.length}`} />
              <Stat label="Incumbents" value={String(incumbentCount)} />
              <Stat label="Re-runners" value={String(rerunnerCount)} />
              <Stat label="Celebrities" value={String(celebCount)} />
            </div>
          </div>

          <div className="p-5 max-h-[560px] overflow-y-auto space-y-5">
            {loading && <p className="text-sm text-muted-foreground">Loading dossier...</p>}
            {!loading && candidates.length === 0 && (
              <p className="text-sm text-muted-foreground">No candidates found for this constituency. Use candidate sync with validated ECI/party sources.</p>
            )}

            {!loading && candidates.length > 0 && candidates.map((candidate, idx) => (
              <div key={`${candidate.candidate_name}-${idx}`} className="rounded-2xl border border-border/40 p-4 bg-white/80 dark:bg-slate-900/55 shadow-sm">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <h4 className="font-black text-base md:text-lg leading-tight">{candidate.candidate_name}</h4>
                    <p className="text-xs md:text-sm text-muted-foreground mt-0.5">{candidate.party} | {candidate.alliance}</p>
                  </div>
                  <div className="flex flex-wrap gap-1.5 justify-end">
                    {candidate.eci_approved && <Badge text="ECI Verified" tone="emerald" />}
                    {candidate.party_approved && <Badge text="Party Confirmed" tone="blue" />}
                    {candidate.is_incumbent && <Badge text="Incumbent" tone="amber" />}
                    {candidate.is_rerunner && <Badge text="Re-runner" tone="violet" />}
                    {candidate.is_celebrity && <Badge text="Celebrity" tone="rose" />}
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-2 mt-3 text-xs">
                  <div>Nomination: <span className="font-semibold">{candidate.nomination_status || 'unknown'}</span></div>
                  <div>Age/Gender: <span className="font-semibold">{candidate.age || 'NA'} / {candidate.gender || 'NA'}</span></div>
                  <div>Education: <span className="font-semibold">{candidate.education || 'NA'}</span></div>
                  <div>Profession: <span className="font-semibold">{candidate.profession || 'NA'}</span></div>
                  <div>Assets: <span className="font-semibold">{candidate.assets || 'NA'}</span></div>
                  <div>Liabilities: <span className="font-semibold">{candidate.liabilities || 'NA'}</span></div>
                  <div>Cases: <span className="font-semibold">{candidate.criminal_cases ?? 0}</span></div>
                  <div>Source: <span className="font-semibold">{candidate.source || 'curated'}</span></div>
                </div>
                <div className="flex flex-wrap gap-3 mt-2">
                  {candidate.affidavit_url && (
                    <a href={candidate.affidavit_url} target="_blank" rel="noreferrer" className="text-xs text-primary hover:underline">ECI affidavit</a>
                  )}
                  {(candidate.validation_reports || []).map((link, reportIndex) => (
                    <a key={`${link}-${reportIndex}`} href={link} target="_blank" rel="noreferrer" className="text-xs text-primary hover:underline">
                      Validation report {reportIndex + 1}
                    </a>
                  ))}
                </div>
              </div>
            ))}

            <div className="rounded-2xl border border-border/40 p-4 bg-white/80 dark:bg-slate-900/55 shadow-sm">
              <h4 className="font-black text-xs uppercase tracking-widest">Assembly Election Summary</h4>
              <div className="mt-3 space-y-2">
                {(history?.elections || []).map((item) => (
                  <div key={item.year} className="text-xs rounded-xl border border-border/30 p-2">
                    <div className="font-bold">{item.year}: {item.winner_alliance} {item.winner_seats ? `(${item.winner_seats})` : '(TBD)'}</div>
                    <div className="text-muted-foreground">{item.summary}</div>
                  </div>
                ))}
              </div>
            </div>

            <div className="rounded-2xl border border-border/40 p-4 bg-white/80 dark:bg-slate-900/55 shadow-sm">
              <h4 className="font-black text-xs uppercase tracking-widest">Constituency Community Vote Split (Indicative)</h4>
              <p className="text-[11px] text-muted-foreground mt-1">{communitySplit?.source_note || 'No community split data loaded.'}</p>
              <div className="mt-3 space-y-2">
                {(communitySplit?.rows || []).map((row, idx) => (
                  <div key={`${row.group}-${idx}`} className="text-xs">
                    <div className="flex justify-between"><span className="font-semibold">{row.group}</span><span>{row.vote_share_estimate}%</span></div>
                    <div className="h-2 rounded bg-muted overflow-hidden"><div className="h-full bg-primary" style={{ width: `${row.vote_share_estimate}%` }} /></div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>
      </div>
    </main>
  );
};

const Stat = ({ label, value }: { label: string; value: string }) => (
  <div className="rounded-xl border border-border/30 bg-white/60 dark:bg-slate-900/40 px-2 py-1.5">
    <div className="text-[9px] uppercase tracking-wider text-muted-foreground font-bold">{label}</div>
    <div className="text-xs font-black">{value}</div>
  </div>
);

const Badge = ({ text, tone }: { text: string; tone: 'emerald' | 'blue' | 'amber' | 'violet' | 'rose' }) => {
  const styles: Record<string, string> = {
    emerald: 'bg-emerald-100 text-emerald-700',
    blue: 'bg-blue-100 text-blue-700',
    amber: 'bg-amber-100 text-amber-700',
    violet: 'bg-violet-100 text-violet-700',
    rose: 'bg-rose-100 text-rose-700',
  };
  return <span className={`text-[10px] font-black px-2 py-1 rounded-lg ${styles[tone]}`}>{text}</span>;
};
