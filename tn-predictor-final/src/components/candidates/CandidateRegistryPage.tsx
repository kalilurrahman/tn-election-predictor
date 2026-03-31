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
  nomination_status?: string;
  education?: string;
  profession?: string;
  age?: number;
  gender?: string;
  assets?: string;
  liabilities?: string;
  criminal_cases?: number;
  affidavit_url?: string;
  source?: string;
};

export const CandidateRegistryPage = () => {
  const [geoData, setGeoData] = useState<FeatureCollection | null>(null);
  const [selectedAc, setSelectedAc] = useState<number | null>(null);
  const [selectedName, setSelectedName] = useState<string>('Select a constituency on map');
  const [candidates, setCandidates] = useState<CandidateRow[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetch('/tn_assembly.geojson')
      .then((res) => res.json())
      .then((data) => setGeoData(data))
      .catch(() => setGeoData(null));
  }, []);

  useEffect(() => {
    if (!selectedAc) return;
    setLoading(true);
    fetch(`/api/candidates?ac_no=${selectedAc}`)
      .then((res) => res.json())
      .then((data) => setCandidates(data.rows || []))
      .catch(() => setCandidates([]))
      .finally(() => setLoading(false));
  }, [selectedAc]);

  const approvedCount = useMemo(
    () => candidates.filter((candidate) => candidate.eci_approved || candidate.party_approved).length,
    [candidates],
  );

  return (
    <main className="flex-1 container mx-auto px-4 md:px-8 py-8">
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        <section className="lg:col-span-6 rounded-3xl border border-border/40 overflow-hidden bg-white/60 dark:bg-slate-900/50">
          <div className="px-5 py-4 border-b border-border/30 flex items-center justify-between">
            <h3 className="font-black text-sm uppercase tracking-widest">Constituency Selector</h3>
            <a
              href="/api/candidates/export.csv"
              target="_blank"
              rel="noreferrer"
              className="text-xs font-bold text-primary hover:underline"
            >
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
              <div className="h-full flex items-center justify-center text-sm text-muted-foreground">
                Unable to load assembly map.
              </div>
            )}
          </div>
        </section>

        <section className="lg:col-span-6 rounded-3xl border border-border/40 bg-white/70 dark:bg-slate-900/60">
          <div className="px-5 py-4 border-b border-border/30">
            <h3 className="font-black text-sm uppercase tracking-widest">Candidate Registry</h3>
            <p className="text-xs text-muted-foreground mt-1">
              {selectedName} {selectedAc ? `(AC #${selectedAc})` : ''}
            </p>
            <p className="text-xs text-muted-foreground">
              Approved/verified candidates shown: {approvedCount}/{candidates.length}
            </p>
          </div>

          <div className="p-5 max-h-[560px] overflow-y-auto">
            {loading && <p className="text-sm text-muted-foreground">Loading candidates...</p>}
            {!loading && candidates.length === 0 && (
              <p className="text-sm text-muted-foreground">
                No candidates found for this constituency. Run candidate sync with ECI/party sources.
              </p>
            )}

            {!loading && candidates.length > 0 && (
              <div className="space-y-4">
                {candidates.map((candidate, idx) => (
                  <div key={`${candidate.candidate_name}-${idx}`} className="rounded-2xl border border-border/40 p-4">
                    <div className="flex items-center justify-between gap-3">
                      <div>
                        <h4 className="font-bold text-base">{candidate.candidate_name}</h4>
                        <p className="text-xs text-muted-foreground">
                          {candidate.party} | {candidate.alliance}
                        </p>
                      </div>
                      <div className="flex gap-2">
                        {candidate.eci_approved && <span className="text-[10px] font-black bg-emerald-100 text-emerald-700 px-2 py-1 rounded-lg">ECI</span>}
                        {candidate.party_approved && <span className="text-[10px] font-black bg-blue-100 text-blue-700 px-2 py-1 rounded-lg">Party</span>}
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
                    {candidate.affidavit_url && (
                      <a href={candidate.affidavit_url} target="_blank" rel="noreferrer" className="text-xs text-primary hover:underline mt-2 inline-block">
                        View affidavit
                      </a>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </section>
      </div>
    </main>
  );
};
