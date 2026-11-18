import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Trophy,
  Award,
  Medal,
  Download,
  Search,
  ArrowUpDown,
  AlertCircle,
  ArrowRight,
  Info,
} from 'lucide-react';
import { api, RankingsResponse } from '../services/api';
import { RoyalCrownIcon } from '../components/common/RoyalEmblem';
import { formatNum, formatDelta, formatPercent } from '../utils/format';

export const ReliabilityRankings: React.FC = () => {
  const [discipline, setDiscipline] = useState<'batting' | 'bowling'>('batting');
  const [rankingsData, setRankingsData] = useState<RankingsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [sortBy, setSortBy] = useState<string>('rank');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');

  useEffect(() => {
    const loadRankings = async () => {
      try {
        setLoading(true);
        const data =
          discipline === 'batting'
            ? await api.getBattingRankings(search || undefined, sortBy || undefined, sortOrder)
            : await api.getBowlingRankings(search || undefined, sortBy || undefined, sortOrder);
        setRankingsData(data);
      } catch (err) {
        console.error('Failed to load rankings:', err);
      } finally {
        setLoading(false);
      }
    };
    loadRankings();
  }, [discipline, search, sortBy, sortOrder]);

  const handleSort = (col: string) => {
    if (sortBy === col) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(col);
      setSortOrder('asc');
    }
  };

  const top10 = rankingsData?.top_10 || [];
  const nearMiss = rankingsData?.near_miss_11_15 || [];
  const fullRankings = rankingsData?.full_rankings || [];

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {/* Header & Discipline Selector */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-6 rounded-3xl bg-[#120817] border border-[#400A2D] shadow-rr-card">
        <div>
          <h2 className="text-xl sm:text-2xl font-extrabold text-white flex items-center gap-2">
            <Trophy className="text-[#D4AF37]" size={26} />
            SupeRR Reliability Rankings — Official Round 1 Selections
          </h2>
          <p className="text-xs text-[#BFA8BA] mt-1">
            Official Top 10 Batters and Top 10 Bowlers evaluated across 200,999 balls with empirical Bayes shrinkage.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex rounded-xl bg-[#20091F] border border-[#400A2D] p-1">
            <button
              onClick={() => {
                setDiscipline('batting');
                setSortBy('rank');
                setSortOrder('asc');
              }}
              className={`px-4 py-1.5 rounded-lg text-xs font-bold transition-all ${
                discipline === 'batting'
                  ? 'bg-gradient-to-r from-[#C21868] to-[#8F2455] text-white shadow-rr-glow'
                  : 'text-[#BFA8BA] hover:text-white'
              }`}
            >
              Top 10 Batters
            </button>
            <button
              onClick={() => {
                setDiscipline('bowling');
                setSortBy('rank');
                setSortOrder('asc');
              }}
              className={`px-4 py-1.5 rounded-lg text-xs font-bold transition-all ${
                discipline === 'bowling'
                  ? 'bg-gradient-to-r from-[#8F2455] to-[#400A2D] text-white shadow-rr-glow border border-[#C21868]/40'
                  : 'text-[#BFA8BA] hover:text-white'
              }`}
            >
              Top 10 Bowlers
            </button>
          </div>

          <a
            href={api.getRankingsExportUrl(discipline)}
            download
            className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-[#20091F] border border-[#400A2D] text-white hover:border-[#C21868] text-xs font-bold transition-all shadow-rr-card"
          >
            <Download size={14} className="text-[#C21868]" />
            Export CSV
          </a>
        </div>
      </div>

      {loading || !rankingsData ? (
        <div className="p-16 text-center rounded-3xl bg-[#120817] border border-[#400A2D]">
          <div className="w-8 h-8 border-3 border-[#C21868] border-t-transparent rounded-full animate-spin mx-auto"></div>
          <p className="text-xs text-[#BFA8BA] mt-2 font-mono">Loading official rankings data...</p>
        </div>
      ) : (
        <div className="space-y-8">
          {/* Top 3 Royal Podium Display */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-2">
            {/* Rank 2 (Silver) */}
            {top10[1] && (
              <div className="p-6 rounded-3xl bg-gradient-to-b from-[#20091F] to-[#120817] border border-[#E2E8F0]/40 shadow-rr-card relative overflow-hidden flex flex-col justify-between order-2 md:order-1 mt-0 md:mt-6">
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="px-3 py-1 rounded-full text-xs font-black bg-[#E2E8F0]/15 text-[#E2E8F0] border border-[#E2E8F0]/40 flex items-center gap-1 font-mono">
                      <Medal size={13} /> RANK #2 (SILVER)
                    </span>
                    <span className="text-2xl font-black text-[#E2E8F0] font-mono">
                      {formatNum(top10[1].reliability_score, 2)}
                    </span>
                  </div>
                  <div>
                    <h3 className="text-xl font-black text-white">{top10[1].player_name}</h3>
                    <p className="text-xs text-[#826D7D] font-mono">ID: {top10[1].player_id}</p>
                  </div>
                  <div className="p-3 rounded-xl bg-[#080510]/80 border border-[#400A2D] text-xs space-y-1">
                    <div className="text-white font-semibold">{top10[1].pressure_stat_display}</div>
                    <div className="text-[#BFA8BA] font-mono">
                      Uplift: {formatDelta(top10[1].pressure_uplift, 3)} / ball
                    </div>
                  </div>
                </div>

                <div className="pt-4 border-t border-[#400A2D]/50 mt-4 flex items-center justify-between">
                  <Link
                    to={`/players?player_id=${top10[1].player_id}&discipline=${discipline}`}
                    className="text-xs font-bold text-[#E2E8F0] hover:text-[#C21868] flex items-center gap-1 transition-colors"
                  >
                    View Dossier <ArrowRight size={13} />
                  </Link>
                </div>
              </div>
            )}

            {/* Rank 1 (Gold Champion) */}
            {top10[0] && (
              <div className="p-6 rounded-3xl bg-gradient-to-b from-[#400A2D] via-[#20091F] to-[#120817] border-2 border-[#C21868] shadow-rr-elevated relative overflow-hidden flex flex-col justify-between order-1 md:order-2">
                <div className="absolute top-0 right-0 w-32 h-32 bg-[#C21868]/20 rounded-full blur-2xl pointer-events-none"></div>
                <div className="space-y-3 relative z-10">
                  <div className="flex items-center justify-between">
                    <span className="px-3.5 py-1.5 rounded-full text-xs font-black bg-[#D4AF37] text-[#080510] flex items-center gap-1.5 shadow-rr-glow font-mono">
                      <RoyalCrownIcon size={14} /> RANK #1 (GOLD CHAMPION)
                    </span>
                    <span className="text-3xl font-black text-[#D4AF37] font-mono">
                      {formatNum(top10[0].reliability_score, 2)}
                    </span>
                  </div>
                  <div>
                    <h3 className="text-2xl font-black text-white">{top10[0].player_name}</h3>
                    <p className="text-xs text-[#F5EAF2] font-mono">ID: {top10[0].player_id}</p>
                  </div>
                  <div className="p-3.5 rounded-xl bg-[#080510]/90 border border-[#C21868] text-xs space-y-1.5">
                    <div className="text-white font-bold">{top10[0].pressure_stat_display}</div>
                    <div className="text-[#D4AF37] font-mono">
                      Pressure Uplift: {formatDelta(top10[0].pressure_uplift, 3)} / ball
                    </div>
                    <div className="text-[#BFA8BA] font-mono text-[11px]">
                      Consistency: {formatPercent(top10[0].consistency_metric, 1)} • Uncertainty SE: {formatNum(top10[0].uncertainty_measure, 3)}
                    </div>
                  </div>
                </div>

                <div className="pt-4 border-t border-[#C21868]/40 mt-4 flex items-center justify-between relative z-10">
                  <Link
                    to={`/players?player_id=${top10[0].player_id}&discipline=${discipline}`}
                    className="text-xs font-bold text-[#D4AF37] hover:text-white flex items-center gap-1 transition-colors"
                  >
                    View Comprehensive Dossier <ArrowRight size={13} />
                  </Link>
                </div>
              </div>
            )}

            {/* Rank 3 (Bronze) */}
            {top10[2] && (
              <div className="p-6 rounded-3xl bg-gradient-to-b from-[#20091F] to-[#120817] border border-[#CD7F32]/40 shadow-rr-card relative overflow-hidden flex flex-col justify-between order-3 md:order-3 mt-0 md:mt-8">
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="px-3 py-1 rounded-full text-xs font-black bg-[#CD7F32]/20 text-[#CD7F32] border border-[#CD7F32]/40 flex items-center gap-1 font-mono">
                      <Medal size={13} /> RANK #3 (BRONZE)
                    </span>
                    <span className="text-2xl font-black text-[#CD7F32] font-mono">
                      {formatNum(top10[2].reliability_score, 2)}
                    </span>
                  </div>
                  <div>
                    <h3 className="text-xl font-black text-white">{top10[2].player_name}</h3>
                    <p className="text-xs text-[#826D7D] font-mono">ID: {top10[2].player_id}</p>
                  </div>
                  <div className="p-3 rounded-xl bg-[#080510]/80 border border-[#400A2D] text-xs space-y-1">
                    <div className="text-white font-semibold">{top10[2].pressure_stat_display}</div>
                    <div className="text-[#BFA8BA] font-mono">
                      Uplift: {formatDelta(top10[2].pressure_uplift, 3)} / ball
                    </div>
                  </div>
                </div>

                <div className="pt-4 border-t border-[#400A2D]/50 mt-4 flex items-center justify-between">
                  <Link
                    to={`/players?player_id=${top10[2].player_id}&discipline=${discipline}`}
                    className="text-xs font-bold text-[#CD7F32] hover:text-[#C21868] flex items-center gap-1 transition-colors"
                  >
                    View Dossier <ArrowRight size={13} />
                  </Link>
                </div>
              </div>
            )}
          </div>

          {/* Ranks 4 to 10 Grid */}
          <div className="p-6 rounded-3xl bg-[#120817] border border-[#400A2D] shadow-rr-card space-y-4">
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <Award className="text-[#C21868]" size={18} />
              Top 4–10 Ranked Contenders
            </h3>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {top10.slice(3, 10).map((p) => (
                <div
                  key={p.player_id}
                  className="p-4 rounded-2xl bg-[#20091F]/60 border border-[#400A2D] hover:border-[#C21868] transition-all space-y-2"
                >
                  <div className="flex items-center justify-between">
                    <span className="w-7 h-7 rounded-lg bg-[#400A2D] text-white text-xs font-black font-mono flex items-center justify-center">
                      #{p.rank}
                    </span>
                    <span className="text-base font-black text-[#D4AF37] font-mono">
                      {formatNum(p.reliability_score, 2)}
                    </span>
                  </div>
                  <div>
                    <h4 className="text-sm font-bold text-white">{p.player_name}</h4>
                    <p className="text-[11px] text-[#826D7D] font-mono">ID: {p.player_id}</p>
                  </div>
                  <div className="pt-2 border-t border-[#400A2D]/40 text-[11px] text-[#BFA8BA] flex justify-between font-mono">
                    <span>{p.pressure_matches} matches ({p.pressure_balls} HP balls)</span>
                    <span className="text-[#F5EAF2]">
                      Δ: {formatDelta(p.pressure_uplift, 2)}
                    </span>
                  </div>
                  <Link
                    to={`/players?player_id=${p.player_id}&discipline=${discipline}`}
                    className="pt-1 text-[11px] font-bold text-[#C21868] hover:underline inline-flex items-center gap-1"
                  >
                    Analytical Dossier <ArrowRight size={11} />
                  </Link>
                </div>
              ))}
            </div>
          </div>

          {/* Near-Miss Contenders Section (Ranks 11–15) */}
          {nearMiss.length > 0 && (
            <div className="p-6 rounded-3xl bg-[#20091F]/40 border border-[#400A2D] shadow-rr-card space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Info className="text-[#D4AF37]" size={18} />
                  <h4 className="text-sm font-bold text-white uppercase tracking-wider">
                    Near-Miss Contenders (Ranks 11–15)
                  </h4>
                </div>
                <span className="text-xs text-[#826D7D]">Narrowly missed Top 10 podium</span>
              </div>
              <p className="text-xs text-[#BFA8BA] leading-relaxed">
                These players met the $\ge 30$ high-pressure deliveries threshold and demonstrated elevated performance,
                falling just short due to variance penalties or slightly lower consistency scores.
              </p>

              <div className="grid grid-cols-1 sm:grid-cols-5 gap-3 pt-2">
                {nearMiss.map((p) => (
                  <div
                    key={p.player_id}
                    className="p-3 rounded-xl bg-[#080510]/70 border border-[#400A2D] space-y-1"
                  >
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-mono text-[#826D7D]">#{p.rank}</span>
                      <span className="font-mono font-bold text-[#D4AF37]">{formatNum(p.reliability_score, 1)}</span>
                    </div>
                    <div className="text-xs font-bold text-white truncate">{p.player_name}</div>
                    <div className="text-[10px] text-[#826D7D] font-mono">
                      {p.pressure_balls} HP balls (Δ: {formatDelta(p.pressure_uplift, 2)})
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Full Official Standings Table */}
          <div className="p-6 rounded-3xl bg-[#120817] border border-[#400A2D] shadow-rr-card space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div>
                <h3 className="text-base font-bold text-white">Full Evaluated Candidate Pool</h3>
                <p className="text-xs text-[#BFA8BA]">
                  {rankingsData.total_eligible} eligible players meeting the $\ge 30$ HP deliveries criterion out of{' '}
                  {rankingsData.total_candidates} evaluated.
                </p>
              </div>

              <div className="relative max-w-xs w-full">
                <Search size={15} className="absolute left-3 top-2.5 text-[#BFA8BA]" />
                <input
                  type="text"
                  placeholder="Filter candidate..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="w-full pl-9 pr-3 py-1.5 rounded-xl bg-[#20091F] border border-[#400A2D] text-xs text-white placeholder-[#826D7D] focus:outline-none focus:border-[#C21868]"
                />
              </div>
            </div>

            {/* Official Rankings Integrity Notice */}
            <div className="p-3 rounded-xl bg-[#20091F]/70 border border-[#C21868]/30 flex items-center gap-2 text-xs text-[#BFA8BA]">
              <AlertCircle size={15} className="text-[#C21868] shrink-0" />
              <span>
                <strong className="text-white">Audit Integrity:</strong> Official Top 10 rankings are permanently locked
                per Phase 5 and verified in the submission package. Sorting or filtering this view affects presentation only.
              </span>
            </div>

            {/* Table */}
            <div className="overflow-x-auto rounded-2xl border border-[#400A2D]/70">
              <table className="w-full text-left text-xs font-mono">
                <thead>
                  <tr className="bg-[#20091F] text-[#BFA8BA] border-b border-[#400A2D]">
                    <th
                      onClick={() => handleSort('rank')}
                      className="py-3 px-3 cursor-pointer hover:text-white"
                    >
                      <div className="flex items-center gap-1">
                        <span>Rank</span>
                        <ArrowUpDown size={11} />
                      </div>
                    </th>
                    <th
                      onClick={() => handleSort('player_name')}
                      className="py-3 px-3 cursor-pointer hover:text-white font-sans"
                    >
                      <div className="flex items-center gap-1">
                        <span>Player Name</span>
                        <ArrowUpDown size={11} />
                      </div>
                    </th>
                    <th
                      onClick={() => handleSort('reliability_score')}
                      className="py-3 px-3 text-right cursor-pointer hover:text-white"
                    >
                      <div className="flex items-center justify-end gap-1">
                        <span>Reliability</span>
                        <ArrowUpDown size={11} />
                      </div>
                    </th>
                    <th className="py-3 px-3 text-right">HP Balls</th>
                    <th className="py-3 px-3 text-right">HP Impact</th>
                    <th className="py-3 px-3 text-right">Ord. Baseline</th>
                    <th className="py-3 px-3 text-right">Uplift (Δ)</th>
                    <th className="py-3 px-3 text-right">Consistency</th>
                    <th className="py-3 px-3 text-right">Uncertainty</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#400A2D]/40">
                  {fullRankings.map((p) => (
                    <tr
                      key={p.player_id}
                      className={`hover:bg-[#20091F]/50 transition-colors ${
                        p.rank <= 10 ? 'bg-[#20091F]/20' : ''
                      }`}
                    >
                      <td className="py-2.5 px-3">
                        <span
                          className={`font-bold ${
                            p.rank === 1
                              ? 'text-[#D4AF37]'
                              : p.rank === 2
                              ? 'text-[#E2E8F0]'
                              : p.rank === 3
                              ? 'text-[#CD7F32]'
                              : p.rank <= 10
                              ? 'text-[#C21868]'
                              : 'text-[#826D7D]'
                          }`}
                        >
                          #{p.rank}
                        </span>
                      </td>
                      <td className="py-2.5 px-3 font-sans font-semibold text-white">
                        <Link
                          to={`/players?player_id=${p.player_id}&discipline=${discipline}`}
                          className="hover:text-[#C21868] transition-colors"
                        >
                          {p.player_name}
                        </Link>
                      </td>
                      <td className="py-2.5 px-3 text-right font-bold text-[#D4AF37]">
                        {formatNum(p.reliability_score, 2)}
                      </td>
                      <td className="py-2.5 px-3 text-right text-[#F5EAF2]">{p.pressure_balls ?? 0}</td>
                      <td className="py-2.5 px-3 text-right text-[#F5EAF2]">
                        {formatDelta(p.high_pressure_impact, 3)}
                      </td>
                      <td className="py-2.5 px-3 text-right text-[#826D7D]">
                        {formatNum(p.ordinary_performance_baseline, 3)}
                      </td>
                      <td className="py-2.5 px-3 text-right text-[#C21868] font-semibold">
                        {formatDelta(p.pressure_uplift, 3)}
                      </td>
                      <td className="py-2.5 px-3 text-right text-[#F5EAF2]">
                        {formatPercent(p.consistency_metric, 1)}
                      </td>
                      <td className="py-2.5 px-3 text-right text-[#826D7D]">
                        ±{formatNum(p.uncertainty_measure, 3)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
