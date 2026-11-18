import React, { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  UserCheck,
  Search,
  Trophy,
  Activity,
  Layers,
  ShieldCheck,
  Zap,
  TrendingUp,
  Scale,
  X,
} from 'lucide-react';
import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import {
  api,
  PlayerItem,
  PlayerDetail,
  PlayerComparisonResponse,
} from '../services/api';
import { formatNum, formatDelta, formatPercent } from '../utils/format';
import { RoyalCrownIcon } from '../components/common/RoyalEmblem';

export const PlayerIntelligence: React.FC = () => {
  const [searchParams] = useSearchParams();
  const initialPlayerId = searchParams.get('player_id')
    ? Number(searchParams.get('player_id'))
    : null;
  const initialDiscipline = searchParams.get('discipline') || 'batting';

  const [discipline, setDiscipline] = useState<'batting' | 'bowling'>(
    initialDiscipline === 'bowling' ? 'bowling' : 'batting'
  );
  const [search, setSearch] = useState('');
  const [playersList, setPlayersList] = useState<PlayerItem[]>([]);
  const [selectedPlayerId, setSelectedPlayerId] = useState<number | null>(
    initialPlayerId || (discipline === 'batting' ? 46066 : 6237)
  );
  const [playerDetail, setPlayerDetail] = useState<PlayerDetail | null>(null);
  const [loadingDetail, setLoadingDetail] = useState(false);

  // Comparison State
  const [compareModalOpen, setCompareModalOpen] = useState(false);
  const [comparisonResult, setComparisonResult] = useState<PlayerComparisonResponse | null>(null);
  const [loadingCompare, setLoadingCompare] = useState(false);

  // Load players directory
  useEffect(() => {
    const loadPlayers = async () => {
      try {
        const list = await api.getPlayers(discipline, 'all', search || undefined, 100);
        setPlayersList(list);
        if (list.length > 0 && !selectedPlayerId) {
          setSelectedPlayerId(list[0].player_id);
        }
      } catch (err) {
        console.error('Failed to load players list:', err);
      }
    };
    loadPlayers();
  }, [discipline, search]);

  // Load active player detail
  useEffect(() => {
    if (!selectedPlayerId) return;
    const loadDetail = async () => {
      try {
        setLoadingDetail(true);
        const data = await api.getPlayerDetail(selectedPlayerId, discipline);
        setPlayerDetail(data);
      } catch (err) {
        console.error('Failed to load player detail:', err);
      } finally {
        setLoadingDetail(false);
      }
    };
    loadDetail();
  }, [selectedPlayerId, discipline]);

  // Handle comparison query
  const triggerComparison = async (pBId: number) => {
    if (!selectedPlayerId) return;
    try {
      setLoadingCompare(true);
      const res = await api.comparePlayers(selectedPlayerId, pBId, discipline);
      setComparisonResult(res);
      setCompareModalOpen(true);
    } catch (err) {
      console.error('Failed to execute comparison:', err);
    } finally {
      setLoadingCompare(false);
    }
  };

  const pSummary = playerDetail?.summary;

  // Comparison Radar Data
  const radarData = comparisonResult
    ? Object.entries(comparisonResult.radar_comparison).map(([metric, values]) => {
        const pAName = comparisonResult.player_a.summary.player_name;
        const pBName = comparisonResult.player_b.summary.player_name;
        return {
          metric:
            metric === 'reliability'
              ? 'Reliability'
              : metric === 'hp_impact'
              ? 'HP Impact'
              : metric === 'uplift'
              ? 'Uplift'
              : metric === 'consistency'
              ? 'Consistency'
              : 'Sample Certainty',
          [pAName]: Math.round(values[pAName] || 0),
          [pBName]: Math.round(values[pBName] || 0),
        };
      })
    : [];

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header and Filter Toolbar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-6 rounded-3xl bg-[#120817] border border-[#400A2D] shadow-rr-card">
        <div>
          <h2 className="text-xl sm:text-2xl font-extrabold text-white flex items-center gap-2">
            <UserCheck className="text-[#C21868]" size={24} />
            Player Intelligence & Clutch Dossier
          </h2>
          <p className="text-xs text-[#BFA8BA] mt-1">
            Empirical Bayes performance evaluations, relative pressure uplift, and match-to-match consistency.
          </p>
        </div>

        {/* Discipline Toggle */}
        <div className="flex items-center gap-3">
          <div className="flex rounded-xl bg-[#20091F] border border-[#400A2D] p-1">
            <button
              onClick={() => {
                setDiscipline('batting');
                setSelectedPlayerId(46066);
              }}
              className={`px-4 py-1.5 rounded-lg text-xs font-bold transition-all ${
                discipline === 'batting'
                  ? 'bg-gradient-to-r from-[#C21868] to-[#8F2455] text-white shadow-rr-glow'
                  : 'text-[#BFA8BA] hover:text-white'
              }`}
            >
              Batting Intelligence
            </button>
            <button
              onClick={() => {
                setDiscipline('bowling');
                setSelectedPlayerId(6237);
              }}
              className={`px-4 py-1.5 rounded-lg text-xs font-bold transition-all ${
                discipline === 'bowling'
                  ? 'bg-gradient-to-r from-[#8F2455] to-[#400A2D] text-white shadow-rr-glow border border-[#C21868]/40'
                  : 'text-[#BFA8BA] hover:text-white'
              }`}
            >
              Bowling Intelligence
            </button>
          </div>
        </div>
      </div>

      {/* Main Grid: Player Directory vs Dossier */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Directory Sidebar */}
        <div className="lg:col-span-4 space-y-4">
          <div className="p-4 rounded-3xl bg-[#120817] border border-[#400A2D] shadow-rr-card space-y-3">
            <div className="relative">
              <Search size={15} className="absolute left-3 top-2.5 text-[#BFA8BA]" />
              <input
                type="text"
                placeholder="Search player name or ID..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full pl-9 pr-3 py-2 rounded-xl bg-[#20091F] border border-[#400A2D] text-xs text-white placeholder-[#826D7D] focus:outline-none focus:border-[#C21868]"
              />
            </div>

            <div className="max-h-[560px] overflow-y-auto space-y-2 pr-1">
              {playersList.map((p) => {
                const isSelected = selectedPlayerId === p.player_id;
                return (
                  <div
                    key={p.player_id}
                    onClick={() => setSelectedPlayerId(p.player_id)}
                    className={`p-3 rounded-2xl cursor-pointer transition-all border ${
                      isSelected
                        ? 'bg-[#20091F] border-[#C21868] shadow-rr-card'
                        : 'bg-[#080510]/60 border-[#400A2D]/50 hover:bg-[#20091F]/40 hover:border-[#400A2D]'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        {p.rank ? (
                          <span
                            className={`w-6 h-6 rounded-lg text-xs font-mono font-black flex items-center justify-center ${
                              p.rank === 1
                                ? 'bg-[#D4AF37] text-[#080510]'
                                : p.rank === 2
                                ? 'bg-[#E2E8F0] text-[#080510]'
                                : p.rank === 3
                                ? 'bg-[#CD7F32] text-white'
                                : 'bg-[#400A2D] text-[#F5EAF2]'
                            }`}
                          >
                            {p.rank}
                          </span>
                        ) : (
                          <span className="w-6 h-6 rounded-lg text-[10px] font-mono text-[#826D7D] bg-[#120817] flex items-center justify-center">
                            —
                          </span>
                        )}
                        <div>
                          <div className="text-xs font-bold text-white">{p.player_name}</div>
                          <div className="text-[10px] text-[#826D7D] font-mono">ID: {p.player_id}</div>
                        </div>
                      </div>

                      <div className="text-right">
                        <div className="text-sm font-black text-[#D4AF37] font-mono">
                          {formatNum(p.reliability_score, 1)}
                        </div>
                        <div className="text-[9px] text-[#826D7D] uppercase font-semibold">Reliability</div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Right Dossier Panel */}
        <div className="lg:col-span-8 space-y-6">
          {loadingDetail || !playerDetail || !pSummary ? (
            <div className="p-16 text-center rounded-3xl bg-[#120817] border border-[#400A2D]">
              <div className="w-8 h-8 border-3 border-[#C21868] border-t-transparent rounded-full animate-spin mx-auto"></div>
              <p className="text-xs text-[#BFA8BA] mt-2 font-mono">Loading player analytical dossier...</p>
            </div>
          ) : (
            <div className="space-y-6">
              {/* Player Header Banner */}
              <div className="p-6 rounded-3xl bg-gradient-to-r from-[#20091F] via-[#120817] to-[#080510] border border-[#C21868]/40 shadow-rr-card space-y-4">
                <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      {pSummary.rank ? (
                        <span className="px-3 py-1 rounded-full text-xs font-black bg-[#D4AF37] text-[#080510] flex items-center gap-1.5 shadow-sm">
                          <RoyalCrownIcon size={14} /> OFFICIAL RANK #{pSummary.rank}
                        </span>
                      ) : (
                        <span className="px-3 py-1 rounded-full text-xs font-semibold bg-[#20091F] border border-[#400A2D] text-[#BFA8BA]">
                          Status: {pSummary.eligibility_status}
                        </span>
                      )}
                      <span className="text-xs font-mono text-[#826D7D]">
                        {playerDetail.competitions_count} Tournaments
                      </span>
                    </div>

                    <h3 className="text-2xl sm:text-3xl font-black text-white mt-1">
                      {pSummary.player_name}
                    </h3>
                    <p className="text-xs text-[#BFA8BA] font-mono">
                      Player ID: <span className="text-white font-bold">{pSummary.player_id}</span> • Discipline: {discipline.toUpperCase()}
                    </p>
                  </div>

                  {/* Composite Reliability Score Metric */}
                  <div className="p-4 rounded-2xl bg-[#080510]/90 border border-[#400A2D] text-right min-w-[150px]">
                    <div className="text-3xl font-black text-[#D4AF37] font-mono">
                      {formatNum(pSummary.reliability_score, 2)}
                    </div>
                    <div className="text-[10px] text-[#826D7D] uppercase font-semibold">Reliability Score</div>
                    <div className="text-[10px] text-[#BFA8BA] font-mono mt-0.5">
                      90% CI: [{formatNum(playerDetail.ci_lower_90, 2)}, {formatNum(playerDetail.ci_upper_90, 2)}]
                    </div>
                  </div>
                </div>

                {/* Compare Player Button */}
                <div className="pt-3 border-t border-[#400A2D]/60 flex items-center justify-between">
                  <div className="text-xs text-[#BFA8BA]">
                    Sample Size:{' '}
                    <span className="text-white font-mono font-bold">
                      {pSummary.hp_deliveries ?? (pSummary as any).hp_balls ?? 0} HP Balls
                    </span>{' '}
                    ({pSummary.total_deliveries ?? (playerDetail as any).total_balls ?? 0} total) across{' '}
                    <span className="text-white font-mono">
                      {pSummary.matches_count ?? (playerDetail as any).total_matches ?? 0} matches
                    </span>
                  </div>

                  <button
                    onClick={() => {
                      const candidate = playersList.find((p) => p.player_id !== pSummary.player_id);
                      if (candidate) triggerComparison(candidate.player_id);
                    }}
                    disabled={loadingCompare}
                    className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-[#20091F] border border-[#C21868] text-white hover:bg-[#C21868] text-xs font-bold transition-all shadow-rr-glow"
                  >
                    <Scale size={14} /> Compare Player
                  </button>
                </div>
              </div>

              {/* 4 Core Quantitative Pillars */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                <div className="p-4 rounded-2xl bg-[#120817] border border-[#400A2D] space-y-1">
                  <div className="text-xs text-[#BFA8BA] font-medium flex items-center gap-1">
                    <Zap size={13} className="text-[#C21868]" /> HP Impact / Ball
                  </div>
                  <div className="text-xl font-black text-white font-mono">
                    {formatDelta(pSummary.hp_impact_per_ball, 3)}
                  </div>
                  <div className="text-[10px] text-[#826D7D]">Runs added/saved per HP ball</div>
                </div>

                <div className="p-4 rounded-2xl bg-[#120817] border border-[#400A2D] space-y-1">
                  <div className="text-xs text-[#BFA8BA] font-medium flex items-center gap-1">
                    <TrendingUp size={13} className="text-[#D4AF37]" /> Pressure Uplift (Δ)
                  </div>
                  <div className="text-xl font-black text-[#D4AF37] font-mono">
                    {formatDelta(pSummary.pressure_uplift, 3)}
                  </div>
                  <div className="text-[10px] text-[#826D7D]">Elevation vs normal baseline</div>
                </div>

                <div className="p-4 rounded-2xl bg-[#120817] border border-[#400A2D] space-y-1">
                  <div className="text-xs text-[#BFA8BA] font-medium flex items-center gap-1">
                    <ShieldCheck size={13} className="text-[#F5EAF2]" /> Consistency (C)
                  </div>
                  <div className="text-xl font-black text-[#F5EAF2] font-mono">
                    {formatPercent(pSummary.consistency_metric, 1)}
                  </div>
                  <div className="text-[10px] text-[#826D7D]">Match-to-match reliability</div>
                </div>

                <div className="p-4 rounded-2xl bg-[#120817] border border-[#400A2D] space-y-1">
                  <div className="text-xs text-[#BFA8BA] font-medium flex items-center gap-1">
                    <Layers size={13} className="text-[#8F2455]" /> Sample Weight (W)
                  </div>
                  <div className="text-xl font-black text-[#F5EAF2] font-mono">
                    {formatPercent(pSummary.shrinkage_weight, 1)}
                  </div>
                  <div className="text-[10px] text-[#826D7D]">Empirical Bayes certainty</div>
                </div>
              </div>

              {/* Match Appearances Breakdown */}
              <div className="p-6 rounded-3xl bg-[#120817] border border-[#400A2D] shadow-rr-card space-y-3">
                <h4 className="text-sm font-bold text-white flex items-center gap-2">
                  <Activity size={16} className="text-[#C21868]" />
                  Pressure Match Appearances & Outings
                </h4>

                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs font-mono">
                    <thead>
                      <tr className="bg-[#20091F] text-[#BFA8BA] border-b border-[#400A2D]">
                        <th className="py-2.5 px-3">Date</th>
                        <th className="py-2.5 px-3">Tournament</th>
                        <th className="py-2.5 px-3">Opponent</th>
                        <th className="py-2.5 px-3 text-right">HP Balls</th>
                        <th className="py-2.5 px-3 text-right">
                          {discipline === 'batting' ? 'HP Runs' : 'HP Wickets'}
                        </th>
                        <th className="py-2.5 px-3 text-right">Match Impact</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#400A2D]/40">
                      {(playerDetail.match_appearances || []).map((m, idx) => {
                        const oppName = m.opponent_name || (m as any).opponent_team || 'Opponent';
                        const ballsCount = m.hp_balls ?? (m as any).balls ?? 0;
                        const scoreCount = m.hp_runs_or_wkts ?? (m as any).runs_or_wkts ?? 0;
                        const matchImpact = Number(m.hp_impact ?? (m as any).net_impact ?? 0);
                        return (
                          <tr key={idx} className="hover:bg-[#20091F]/40 transition-colors">
                            <td className="py-2.5 px-3 text-[#BFA8BA]">{m.match_date || '—'}</td>
                            <td className="py-2.5 px-3 text-white font-sans truncate max-w-[150px]">
                              {m.comp_name || 'T20 Match'}
                            </td>
                            <td className="py-2.5 px-3 text-white font-sans">{oppName}</td>
                            <td className="py-2.5 px-3 text-right text-white">{ballsCount}</td>
                            <td className="py-2.5 px-3 text-right text-[#D4AF37] font-bold">
                              {scoreCount}
                            </td>
                            <td className="py-2.5 px-3 text-right text-[#F5EAF2]">
                              {formatDelta(matchImpact, 2)}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Head-to-Head Comparison Modal / Drawer */}
      {compareModalOpen && comparisonResult && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md">
          <div className="bg-[#120817] border border-[#C21868] rounded-3xl max-w-4xl w-full max-h-[90vh] overflow-y-auto p-6 space-y-6 shadow-2xl">
            <div className="flex items-center justify-between pb-3 border-b border-[#400A2D]">
              <div className="flex items-center gap-2">
                <Scale className="text-[#D4AF37]" size={20} />
                <h3 className="text-lg font-black text-white">
                  Head-to-Head Analytical Comparison
                </h3>
              </div>
              <button
                onClick={() => setCompareModalOpen(false)}
                className="p-1.5 rounded-lg text-[#BFA8BA] hover:text-white hover:bg-[#20091F] transition-colors"
              >
                <X size={18} />
              </button>
            </div>

            {/* Selector for Opponent */}
            <div className="flex items-center gap-3">
              <span className="text-xs text-[#BFA8BA]">Compare against:</span>
              <select
                value={comparisonResult.player_b.summary.player_id}
                onChange={(e) => triggerComparison(Number(e.target.value))}
                className="px-3 py-1.5 rounded-xl bg-[#20091F] border border-[#400A2D] text-white text-xs font-semibold focus:outline-none focus:border-[#C21868]"
              >
                {playersList
                  .filter((p) => p.player_id !== comparisonResult.player_a.summary.player_id)
                  .map((p) => (
                    <option key={p.player_id} value={p.player_id}>
                      {p.player_name} (Reliability: {formatNum(p.reliability_score, 1)})
                    </option>
                  ))}
              </select>
            </div>

            {/* Players Comparison Cards */}
            <div className="grid grid-cols-2 gap-4">
              <div className="p-4 rounded-2xl bg-[#20091F] border border-[#C21868] space-y-2">
                <div className="text-xs text-[#C21868] font-bold">PLAYER A</div>
                <div className="text-base sm:text-lg font-black text-white">
                  {comparisonResult.player_a.summary.player_name}
                </div>
                <div className="text-2xl font-black text-[#D4AF37] font-mono">
                  {formatNum(comparisonResult.player_a.summary.reliability_score, 2)}
                </div>
                <div className="text-[11px] text-[#BFA8BA]">
                  Uplift: {formatDelta(comparisonResult.player_a.summary.pressure_uplift, 3)} • Consistency:{' '}
                  {formatPercent(comparisonResult.player_a.summary.consistency_metric, 1)}
                </div>
              </div>

              <div className="p-4 rounded-2xl bg-[#20091F] border border-[#8F2455] space-y-2">
                <div className="text-xs text-[#F5EAF2] font-bold">PLAYER B</div>
                <div className="text-base sm:text-lg font-black text-white">
                  {comparisonResult.player_b.summary.player_name}
                </div>
                <div className="text-2xl font-black text-[#F5EAF2] font-mono">
                  {formatNum(comparisonResult.player_b.summary.reliability_score, 2)}
                </div>
                <div className="text-[11px] text-[#BFA8BA]">
                  Uplift: {formatDelta(comparisonResult.player_b.summary.pressure_uplift, 3)} • Consistency:{' '}
                  {formatPercent(comparisonResult.player_b.summary.consistency_metric, 1)}
                </div>
              </div>
            </div>

            {/* Radar Comparison Chart */}
            <div className="p-4 rounded-2xl bg-[#080510] border border-[#400A2D] h-72">
              <ResponsiveContainer width="100%" height="100%">
                <RadarChart data={radarData}>
                  <PolarGrid stroke="#400A2D" />
                  <PolarAngleAxis dataKey="metric" stroke="#BFA8BA" fontSize={11} />
                  <PolarRadiusAxis stroke="#400A2D" domain={[0, 100]} />
                  <Radar
                    name={comparisonResult.player_a.summary.player_name}
                    dataKey={comparisonResult.player_a.summary.player_name}
                    stroke="#C21868"
                    fill="#C21868"
                    fillOpacity={0.4}
                  />
                  <Radar
                    name={comparisonResult.player_b.summary.player_name}
                    dataKey={comparisonResult.player_b.summary.player_name}
                    stroke="#D4AF37"
                    fill="#D4AF37"
                    fillOpacity={0.35}
                  />
                  <Legend />
                </RadarChart>
              </ResponsiveContainer>
            </div>

            {/* Automated Advantage Analysis Bullets */}
            <div className="p-4 rounded-2xl bg-[#20091F]/60 border border-[#400A2D] space-y-2">
              <h5 className="text-xs font-bold text-white uppercase tracking-wider">
                Statistical Advantage Findings
              </h5>
              <ul className="space-y-1.5 text-xs text-[#BFA8BA]">
                {comparisonResult.advantage_analysis.map((adv, i) => (
                  <li key={i} className="flex items-start gap-2">
                    <span className="text-[#D4AF37] font-bold">•</span>
                    <span>{adv}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
