import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  ShieldCheck,
  Flame,
  Award,
  Layers,
  BarChart3,
  RefreshCw,
  XCircle,
  HelpCircle,
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';
import { api, OverviewResponse } from '../services/api';
import { RoyalCrownIcon, FramedBrandCard } from '../components/common/RoyalEmblem';
import { formatNum, formatDelta, formatPercent } from '../utils/format';

export const Overview: React.FC = () => {
  const [data, setData] = useState<OverviewResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadOverview = async () => {
    try {
      setLoading(true);
      setError(null);
      const resp = await api.getOverview();
      setData(resp);
    } catch (err: any) {
      setError(err?.message || 'Failed to load overview data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadOverview();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center space-y-3">
          <div className="w-10 h-10 border-3 border-[#C21868] border-t-transparent rounded-full animate-spin mx-auto"></div>
          <p className="text-xs text-[#BFA8BA] font-mono">Initializing SupeRR Intelligence Lab...</p>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="p-6 bg-[#20091F] border border-[#C21868] rounded-2xl text-center space-y-3 max-w-xl mx-auto my-12">
        <AlertTriangle className="text-[#C21868] mx-auto" size={32} />
        <h3 className="text-sm font-bold text-white">System Data Load Error</h3>
        <p className="text-xs text-[#BFA8BA] font-mono leading-relaxed bg-[#080510] p-3 rounded-xl border border-[#400A2D]">
          {error || 'Unknown error occurred while connecting to backend.'}
        </p>
        <button
          onClick={loadOverview}
          className="inline-flex items-center gap-1.5 px-4 py-2 bg-gradient-to-r from-[#C21868] to-[#8F2455] text-white rounded-xl text-xs font-semibold hover:shadow-rr-glow transition-all"
        >
          <RefreshCw size={13} /> Retry Connection
        </button>
      </div>
    );
  }

  // Format competition distribution data for chart from CompetitionStat[]
  const compChartData = Array.isArray(data.competitions_distribution)
    ? data.competitions_distribution.map((c) => ({
        name: c.comp_name.length > 20 ? c.comp_name.substring(0, 18) + '...' : c.comp_name,
        fullName: c.comp_name,
        matches: Number(c.matches_count) || 0,
        deliveries: Number(c.deliveries_count) || 0,
      }))
    : [];

  // Rajasthan Royals Inspired Harmonious Chart Palette
  const chartPalette = ['#C21868', '#8F2455', '#D4AF37', '#A83279', '#5A1342', '#3D0D2E'];

  // Pressure Distribution Counts to Percentages calculation
  const battingCounts = data.pressure_distribution?.batting || {};
  const totalBattingBalls =
    Object.values(battingCounts).reduce((sum, n) => sum + (Number(n) || 0), 0) || 1;

  // Actual Phase 3 continuous threshold definitions (< 40.0, 40.0 - 64.9, >= 65.0)
  const pressureMeta: Record<string, { label: string; threshold: string; color: string }> = {
    LOW_PRESSURE: {
      label: 'Low Pressure',
      threshold: '< 40.0',
      color: 'bg-[#64748B]',
    },
    MEDIUM_PRESSURE: {
      label: 'Medium Pressure',
      threshold: '40.0 – 64.9',
      color: 'bg-[#D97706]',
    },
    HIGH_PRESSURE: {
      label: 'High Pressure',
      threshold: '≥ 65.0',
      color: 'bg-[#C21868]',
    },
  };

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {/* Framed Rajasthan Royals Brand Card */}
      <FramedBrandCard />

      {/* Hero Analytics Command Banner */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-[#20091F] via-[#120817] to-[#080510] border border-[#400A2D] p-6 sm:p-8 shadow-rr-card">
        <div className="absolute top-0 right-0 w-80 h-80 bg-[#C21868]/10 rounded-full blur-3xl pointer-events-none -mr-16 -mt-16"></div>
        <div className="relative z-10 space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#400A2D] border border-[#C21868]/40 text-[#C21868] text-xs font-semibold">
              <RoyalCrownIcon size={14} />
              <span>Rajasthan Royals Analytics Command Center</span>
            </div>
            <span className="text-xs font-mono text-[#D4AF37] bg-[#20091F] px-3 py-1 rounded-full border border-[#400A2D]">
              Dataset: {data.total_deliveries.toLocaleString()} Deliveries • {data.total_matches.toLocaleString()} Matches
            </span>
          </div>

          <h2 className="text-2xl sm:text-3xl font-black text-white tracking-tight leading-tight">
            Pressure-Engineered Player Reliability System <br />
            <span className="text-[#C21868]">SupeRR Selector Season 2</span>
          </h2>
          <p className="text-xs sm:text-sm text-[#BFA8BA] max-w-3xl leading-relaxed">
            A statistically defensible intelligence engine measuring how reliably batters and bowlers execute under high match tension. Reconstructed ball-by-ball with strict zero future leakage, leave-one-match-out baselines, and empirical Bayes shrinkage.
          </p>

          {/* Quick Metrics Bar with Royal Framing */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 pt-4 border-t border-[#400A2D]/60">
            <div className="p-4 rounded-2xl bg-[#080510]/80 border border-[#400A2D]">
              <div className="text-[11px] text-[#BFA8BA] font-medium">Deliveries Analysed</div>
              <div className="text-xl sm:text-2xl font-black text-white font-mono mt-1">
                {data.total_deliveries.toLocaleString()}
              </div>
              <div className="text-[10px] text-[#D4AF37] mt-0.5 font-mono">100% Zero-Leakage</div>
            </div>
            <div className="p-4 rounded-2xl bg-[#080510]/80 border border-[#400A2D]">
              <div className="text-[11px] text-[#BFA8BA] font-medium">Matches Recorded</div>
              <div className="text-xl sm:text-2xl font-black text-white font-mono mt-1">
                {data.total_matches.toLocaleString()}
              </div>
              <div className="text-[10px] text-[#C21868] mt-0.5 font-mono">
                {data.total_competitions} Tournaments
              </div>
            </div>
            <div className="p-4 rounded-2xl bg-[#080510]/80 border border-[#400A2D]">
              <div className="text-[11px] text-[#BFA8BA] font-medium">Eligible Batters</div>
              <div className="text-xl sm:text-2xl font-black text-white font-mono mt-1">
                {data.eligible_batters}{' '}
                <span className="text-xs font-normal text-[#BFA8BA]">
                  / {data.total_batters_evaluated || data.total_players}
                </span>
              </div>
              <div className="text-[10px] text-[#8F2455] mt-0.5 font-mono">≥30 High-Pressure Balls</div>
            </div>
            <div className="p-4 rounded-2xl bg-[#080510]/80 border border-[#400A2D]">
              <div className="text-[11px] text-[#BFA8BA] font-medium">Eligible Bowlers</div>
              <div className="text-xl sm:text-2xl font-black text-white font-mono mt-1">
                {data.eligible_bowlers}{' '}
                <span className="text-xs font-normal text-[#BFA8BA]">
                  / {data.total_bowlers_evaluated || data.total_players}
                </span>
              </div>
              <div className="text-[10px] text-[#8F2455] mt-0.5 font-mono">≥30 High-Pressure Balls</div>
            </div>
          </div>
        </div>
      </div>

      {/* Top 1 Batter & Bowler Champions Showcase */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Top 1 Batter */}
        <div className="p-6 rounded-3xl bg-[#120817] border border-[#C21868]/60 shadow-rr-card relative overflow-hidden group hover:border-[#C21868] transition-all">
          <div className="flex items-start justify-between">
            <div className="space-y-1">
              <span className="px-3 py-1 rounded-full text-[11px] font-black bg-[#C21868]/20 border border-[#C21868] text-[#C21868] inline-flex items-center gap-1.5">
                <RoyalCrownIcon size={14} /> #1 RANKED BATTER UNDER PRESSURE
              </span>
              <h3 className="text-2xl font-black text-white mt-2.5">
                {data.top_batter_summary.player_name}
              </h3>
              <p className="text-xs text-[#BFA8BA] font-mono">
                Player ID: <span className="text-white font-bold">{data.top_batter_summary.player_id}</span>
              </p>
            </div>
            <div className="text-right p-3 rounded-2xl bg-[#20091F] border border-[#400A2D]">
              <div className="text-3xl font-black text-[#D4AF37] font-mono">
                {formatNum(data.top_batter_summary?.reliability_score, 2)}
              </div>
              <div className="text-[9px] text-[#BFA8BA] uppercase tracking-wider font-semibold">Reliability Score</div>
            </div>
          </div>

          <div className="mt-4 p-4 rounded-2xl bg-[#080510]/80 border border-[#400A2D] space-y-2 text-xs">
            <div className="flex justify-between">
              <span className="text-[#BFA8BA]">Pressure Record:</span>
              <span className="text-white font-semibold font-mono">
                {data.top_batter_summary.hp_stat_display || data.top_batter_summary.pressure_stat || 'High Pressure Record'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-[#BFA8BA]">Performance Signature:</span>
              <span className="text-[#F5EAF2] font-mono text-[11px]">
                {data.top_batter_summary.key_trait ||
                  `Uplift: ${formatDelta(data.top_batter_summary.uplift, 3)}/ball • Consistency: ${formatPercent(data.top_batter_summary.consistency, 1)}`}
              </span>
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-[#400A2D]/50 flex items-center justify-between">
            <Link
              to={`/players?player_id=${data.top_batter_summary.player_id}&discipline=batting`}
              className="text-xs font-bold text-[#C21868] hover:text-[#D4AF37] inline-flex items-center gap-1.5 transition-colors"
            >
              Examine Analytical Dossier <ArrowRight size={13} />
            </Link>
          </div>
        </div>

        {/* Top 1 Bowler */}
        <div className="p-6 rounded-3xl bg-[#120817] border border-[#8F2455]/60 shadow-rr-card relative overflow-hidden group hover:border-[#C21868] transition-all">
          <div className="flex items-start justify-between">
            <div className="space-y-1">
              <span className="px-3 py-1 rounded-full text-[11px] font-black bg-[#8F2455]/30 border border-[#8F2455] text-[#F5EAF2] inline-flex items-center gap-1.5">
                <Award size={14} className="text-[#D4AF37]" /> #1 RANKED BOWLER UNDER PRESSURE
              </span>
              <h3 className="text-2xl font-black text-white mt-2.5">
                {data.top_bowler_summary.player_name}
              </h3>
              <p className="text-xs text-[#BFA8BA] font-mono">
                Player ID: <span className="text-white font-bold">{data.top_bowler_summary.player_id}</span>
              </p>
            </div>
            <div className="text-right p-3 rounded-2xl bg-[#20091F] border border-[#400A2D]">
              <div className="text-3xl font-black text-[#D4AF37] font-mono">
                {formatNum(data.top_bowler_summary?.reliability_score, 2)}
              </div>
              <div className="text-[9px] text-[#BFA8BA] uppercase tracking-wider font-semibold">Reliability Score</div>
            </div>
          </div>

          <div className="mt-4 p-4 rounded-2xl bg-[#080510]/80 border border-[#400A2D] space-y-2 text-xs">
            <div className="flex justify-between">
              <span className="text-[#BFA8BA]">Pressure Record:</span>
              <span className="text-white font-semibold font-mono">
                {data.top_bowler_summary.hp_stat_display || data.top_bowler_summary.pressure_stat || 'High Pressure Record'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-[#BFA8BA]">Performance Signature:</span>
              <span className="text-[#F5EAF2] font-mono text-[11px]">
                {data.top_bowler_summary.key_trait ||
                  `Uplift: ${formatDelta(data.top_bowler_summary.uplift, 3)}/ball • Consistency: ${formatPercent(data.top_bowler_summary.consistency, 1)}`}
              </span>
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-[#400A2D]/50 flex items-center justify-between">
            <Link
              to={`/players?player_id=${data.top_bowler_summary.player_id}&discipline=bowling`}
              className="text-xs font-bold text-[#C21868] hover:text-[#D4AF37] inline-flex items-center gap-1.5 transition-colors"
            >
              Examine Analytical Dossier <ArrowRight size={13} />
            </Link>
          </div>
        </div>
      </div>

      {/* 6-Phase Pipeline Architecture Status */}
      <div className="p-6 rounded-3xl bg-[#120817] border border-[#400A2D] shadow-rr-card">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-6">
          <div className="space-y-1">
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <Layers className="text-[#C21868]" size={18} />
              Full Analytics Pipeline Verification (Phases 1–6)
            </h3>
            <p className="text-xs text-[#BFA8BA]">
              Every development phase is verified with automated tests, regression parity, and zero future leakage.
            </p>
          </div>
          <span className={`px-3 py-1 bg-[#20091F] border ${
            data.overall_verification_status === 'FAIL'
              ? 'border-rose-500/50 text-rose-400'
              : data.overall_verification_status === 'UNVERIFIED'
              ? 'border-slate-500/50 text-slate-400'
              : data.overall_verification_status === 'PASS_WITH_WARNINGS'
              ? 'border-amber-400/50 text-amber-300'
              : 'border-[#D4AF37]/50 text-[#D4AF37]'
          } text-xs font-bold font-mono rounded-full`}>
            Status: {data.overall_verification_status || 'VERIFIED'} • {data.total_tests_passed ? `${data.total_tests_passed} Tests Verified` : `${formatNum(data.reconstructed_state_coverage, 1)}% Coverage`}
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {data.pipeline_phases.map((phase) => {
            const phaseName = phase.phase_name || phase.name || `Phase ${phase.phase_number}`;
            const phaseDeliverable = phase.deliverable || phase.key_output || 'Verified artifact';
            return (
              <div
                key={phase.phase_number}
                className="p-4 rounded-2xl bg-[#20091F]/60 border border-[#400A2D] hover:border-[#C21868]/50 transition-colors space-y-2 flex flex-col justify-between"
              >
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-[#C21868] font-mono">
                      PHASE {phase.phase_number}
                    </span>
                    <span className={`flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded-full border ${
                      phase.status === 'FAIL'
                        ? 'text-rose-400 bg-rose-400/10 border-rose-400/30'
                        : phase.status === 'UNVERIFIED'
                        ? 'text-slate-400 bg-slate-400/10 border-slate-400/30'
                        : phase.status === 'PASS_WITH_WARNINGS'
                        ? 'text-amber-300 bg-amber-400/10 border-amber-400/30'
                        : 'text-[#D4AF37] bg-[#D4AF37]/10 border-[#D4AF37]/30'
                    }`}>
                      {phase.status === 'FAIL' ? (
                        <><XCircle size={12} /> FAIL</>
                      ) : phase.status === 'UNVERIFIED' ? (
                        <><HelpCircle size={12} /> UNVERIFIED</>
                      ) : phase.status === 'PASS_WITH_WARNINGS' ? (
                        <><AlertTriangle size={12} /> PASS (Notes)</>
                      ) : (
                        <><CheckCircle2 size={12} /> PASS</>
                      )}
                    </span>
                  </div>
                  <h4 className="text-sm font-bold text-white">{phaseName}</h4>
                  <p className="text-xs text-[#BFA8BA] leading-relaxed line-clamp-2">
                    {phase.description}
                  </p>
                  {phase.test_count ? (
                    <div className="text-[10px] text-[#D4AF37]/80 font-mono">
                      {phase.passed_tests} / {phase.test_count} tests passed
                    </div>
                  ) : null}
                </div>
                <div className="pt-2 border-t border-[#400A2D]/60 text-[11px] text-[#BFA8BA] font-mono truncate">
                  {phaseDeliverable}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Analytics Distributions: Tournaments & Pressure Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Tournament Matches Chart */}
        <div className="lg:col-span-2 p-6 rounded-3xl bg-[#120817] border border-[#400A2D] shadow-rr-card space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <BarChart3 className="text-[#C21868]" size={18} />
              Tournament Match Distribution
            </h3>
            <span className="text-xs text-[#BFA8BA] font-mono">
              {data.total_matches.toLocaleString()} Matches Total ({compChartData.length} Competitions)
            </span>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={compChartData} margin={{ top: 10, right: 10, left: -20, bottom: 40 }}>
                <XAxis
                  dataKey="name"
                  stroke="#826D7D"
                  fontSize={10}
                  tickLine={false}
                  angle={-25}
                  textAnchor="end"
                />
                <YAxis stroke="#826D7D" fontSize={10} tickLine={false} />
                <Tooltip
                  content={({ active, payload }) => {
                    if (active && payload && payload.length) {
                      const p = payload[0].payload;
                      return (
                        <div className="p-3 bg-[#20091F] border border-[#C21868] rounded-xl text-xs space-y-1 shadow-2xl">
                          <div className="font-bold text-white">{p.fullName}</div>
                          <div className="text-[#D4AF37] font-mono">{p.matches} Matches Recorded</div>
                          <div className="text-[#BFA8BA] font-mono text-[11px]">
                            {Number(p.deliveries || 0).toLocaleString()} Deliveries
                          </div>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
                <Bar dataKey="matches" radius={[6, 6, 0, 0]}>
                  {compChartData.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={chartPalette[index % chartPalette.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Pressure Class Share */}
        <div className="p-6 rounded-3xl bg-[#120817] border border-[#400A2D] shadow-rr-card space-y-4 flex flex-col justify-between">
          <div>
            <h3 className="text-base font-bold text-white flex items-center gap-2 mb-4">
              <Flame className="text-[#C21868]" size={18} />
              Pressure Class Distribution
            </h3>

            <div className="space-y-3">
              {Object.entries(battingCounts).map(([cls, rawCount]) => {
                const count = Number(rawCount) || 0;
                const pct = (count / totalBattingBalls) * 100;
                const meta = pressureMeta[cls] || {
                  label: cls.replace(/_/g, ' '),
                  threshold: '',
                  color: 'bg-[#C21868]',
                };
                return (
                  <div key={cls} className="space-y-1">
                    <div className="flex justify-between text-xs">
                      <span className="font-semibold text-white">
                        {meta.label}{' '}
                        {meta.threshold && (
                          <span className="text-[10px] text-[#826D7D] font-mono">({meta.threshold})</span>
                        )}
                      </span>
                      <span className="font-mono text-[#BFA8BA]">
                        {count.toLocaleString()} ({formatNum(pct, 1)}%)
                      </span>
                    </div>
                    <div className="w-full h-2 rounded-full bg-[#080510] overflow-hidden border border-[#400A2D]">
                      <div
                        className={`h-full rounded-full ${meta.color}`}
                        style={{ width: `${Math.min(100, pct)}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="pt-4 border-t border-[#400A2D]/60 text-xs text-[#BFA8BA] leading-relaxed">
            <span className="text-[#C21868] font-semibold">High Pressure (HP) threshold:</span> Pressure score ≥ 65.0 computed ball-by-ball from strictly pre-delivery match state.
          </div>
        </div>
      </div>

      {/* Governance & Quality Assurance */}
      <div className="p-6 rounded-3xl bg-[#20091F]/40 border border-[#400A2D] shadow-rr-card">
        <div className="flex items-center gap-3 mb-3">
          <ShieldCheck className="text-[#D4AF37]" size={20} />
          <h3 className="text-base font-bold text-white">
            Analytical Governance & Zero-Leakage Architecture
          </h3>
        </div>
        <p className="text-xs text-[#BFA8BA] leading-relaxed mb-4">
          All pressure calculations, run rates, and tension scores are strictly computed using match state
          immediately preceding delivery release ($t^-$). Post-delivery outcome variables are completely
          isolated during state reconstruction.
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 text-xs">
          {data.data_quality_warnings.map((note, idx) => (
            <div
              key={idx}
              className="p-3.5 rounded-xl bg-[#080510]/80 border border-[#400A2D] flex items-start gap-2.5"
            >
              <CheckCircle2 size={14} className="text-[#D4AF37] shrink-0 mt-0.5" />
              <span className="text-[#BFA8BA] leading-relaxed">{note}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
