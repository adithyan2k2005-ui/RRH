import React, { useEffect, useState } from 'react';
import {
  Activity,
  Flame,
  HelpCircle,
} from 'lucide-react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';
import { api, MatchSummary, MatchPressureTimeline, DeliveryState } from '../services/api';
import { formatNum, formatPercent } from '../utils/format';

export const PressureLab: React.FC = () => {
  const [matches, setMatches] = useState<MatchSummary[]>([]);
  const [selectedMatchId, setSelectedMatchId] = useState<number | null>(null);
  const [selectedInnings, setSelectedInnings] = useState<number>(2);
  const [pressureCurve, setPressureCurve] = useState<MatchPressureTimeline | null>(null);
  const [deliveries, setDeliveries] = useState<DeliveryState[]>([]);
  const [selectedBallIndex, setSelectedBallIndex] = useState<number>(0);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const loadMatches = async () => {
      try {
        const data = await api.getMatches(undefined, undefined, undefined, undefined, 40);
        setMatches(data);
        if (data.length > 0) {
          setSelectedMatchId(data[0].match_id);
        }
      } catch (err) {
        console.error('Failed to load matches:', err);
      }
    };
    loadMatches();
  }, []);

  useEffect(() => {
    if (!selectedMatchId) return;
    const loadCurveAndDeliveries = async () => {
      try {
        setLoading(true);
        const [timeline, delivs] = await Promise.all([
          api.getMatchPressureCurve(selectedMatchId, selectedInnings),
          api.getMatchDeliveries(selectedMatchId, selectedInnings),
        ]);
        setPressureCurve(timeline);
        setDeliveries(delivs);
        setSelectedBallIndex(Math.floor(delivs.length / 2));
      } catch (err) {
        console.error('Failed to load pressure curve:', err);
      } finally {
        setLoading(false);
      }
    };
    loadCurveAndDeliveries();
  }, [selectedMatchId, selectedInnings]);

  const activeBall = deliveries[selectedBallIndex] || null;

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header & Controls */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-6 rounded-3xl bg-[#120817] border border-[#400A2D] shadow-rr-card">
        <div>
          <h2 className="text-xl sm:text-2xl font-extrabold text-white flex items-center gap-2">
            <Activity className="text-[#C21868]" size={24} />
            Context-Aware Cricket Pressure Engine (Pressure Lab)
          </h2>
          <p className="text-xs text-[#BFA8BA] mt-1">
            Dynamic ball-by-ball tension curves decomposed into 6 independent pre-delivery match factors.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <select
            value={selectedMatchId || ''}
            onChange={(e) => setSelectedMatchId(Number(e.target.value))}
            className="px-4 py-2 rounded-xl bg-[#20091F] border border-[#400A2D] text-white text-xs font-semibold focus:outline-none focus:border-[#C21868] max-w-xs truncate"
          >
            {matches.map((m) => (
              <option key={m.match_id} value={m.match_id}>
                Match #{m.match_id}: {m.team1_name} vs {m.team2_name}
              </option>
            ))}
          </select>

          <div className="flex items-center rounded-xl bg-[#20091F] border border-[#400A2D] p-1">
            <button
              onClick={() => setSelectedInnings(1)}
              className={`px-3 py-1 rounded-lg text-xs font-bold transition-all ${
                selectedInnings === 1
                  ? 'bg-gradient-to-r from-[#C21868] to-[#8F2455] text-white shadow-rr-glow'
                  : 'text-[#BFA8BA] hover:text-white'
              }`}
            >
              Inn 1
            </button>
            <button
              onClick={() => setSelectedInnings(2)}
              className={`px-3 py-1 rounded-lg text-xs font-bold transition-all ${
                selectedInnings === 2
                  ? 'bg-gradient-to-r from-[#C21868] to-[#8F2455] text-white shadow-rr-glow'
                  : 'text-[#BFA8BA] hover:text-white'
              }`}
            >
              Inn 2 (Chase)
            </button>
          </div>
        </div>
      </div>

      {/* Main Pressure Curve Chart */}
      <div className="p-6 rounded-3xl bg-[#120817] border border-[#400A2D] shadow-rr-card space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <Flame className="text-[#C21868]" size={18} />
              Continuous Match Pressure Timeline
            </h3>
            <p className="text-xs text-[#BFA8BA]">
              Hover to inspect delivery pressure. Click any point to decompose underlying situation factors.
            </p>
          </div>
          <div className="flex items-center gap-4 text-xs font-mono">
            <span className="flex items-center gap-1.5 text-[#C21868]">
              <span className="w-2.5 h-2.5 rounded-full bg-[#C21868]"></span> Batting Pressure
            </span>
            <span className="flex items-center gap-1.5 text-[#8F2455]">
              <span className="w-2.5 h-2.5 rounded-full bg-[#8F2455]"></span> Bowling Pressure
            </span>
            <span className="flex items-center gap-1.5 text-[#D4AF37]">
              <span className="w-2.5 h-2.5 rounded-full bg-[#D4AF37]"></span> Tension Index
            </span>
          </div>
        </div>

        {loading ? (
          <div className="h-72 flex items-center justify-center">
            <div className="w-8 h-8 border-3 border-[#C21868] border-t-transparent rounded-full animate-spin"></div>
          </div>
        ) : pressureCurve && pressureCurve.pressure_timeline.length > 0 ? (
          <div className="h-80 w-full pt-4">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart
                data={pressureCurve.pressure_timeline}
                onClick={(e) => {
                  if (e && e.activeTooltipIndex !== undefined) {
                    setSelectedBallIndex(e.activeTooltipIndex);
                  }
                }}
              >
                <XAxis
                  dataKey="over_label"
                  stroke="#826D7D"
                  fontSize={10}
                  tickLine={false}
                  interval={Math.floor(pressureCurve.pressure_timeline.length / 12)}
                />
                <YAxis domain={[0, 100]} stroke="#826D7D" fontSize={10} tickLine={false} />
                <Tooltip
                  content={({ active, payload }) => {
                    if (active && payload && payload.length) {
                      const p = payload[0].payload;
                      return (
                        <div className="p-3 bg-[#20091F] border border-[#C21868] rounded-xl text-xs space-y-1 shadow-2xl">
                          <div className="font-bold text-white font-mono">Over {p.over_label} ({p.score_before})</div>
                          <div className="text-[#C21868] font-mono">Batting Pressure: {p.batting_pressure}</div>
                          <div className="text-[#8F2455] font-mono">Bowling Pressure: {p.bowling_pressure}</div>
                          <div className="text-[#D4AF37] font-mono">Match Tension: {p.match_tension}</div>
                          <div className="pt-1 border-t border-[#400A2D] text-[#BFA8BA]">
                            {p.striker} vs {p.bowler} — <span className="text-white font-bold">{p.runs} runs</span>
                            {p.is_wicket && <span className="text-red-400 font-bold ml-1">(WICKET)</span>}
                          </div>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
                <ReferenceLine y={70} stroke="#C21868" strokeDasharray="3 3" label={{ value: 'High Pressure (HP ≥ 70)', fill: '#C21868', fontSize: 10, position: 'insideTopRight' }} />
                <Line
                  type="monotone"
                  dataKey="batting_pressure"
                  stroke="#C21868"
                  strokeWidth={2}
                  dot={false}
                  activeDot={{ r: 5, fill: '#C21868' }}
                />
                <Line
                  type="monotone"
                  dataKey="bowling_pressure"
                  stroke="#8F2455"
                  strokeWidth={1.5}
                  dot={false}
                  activeDot={{ r: 4, fill: '#8F2455' }}
                />
                <Line
                  type="monotone"
                  dataKey="match_tension"
                  stroke="#D4AF37"
                  strokeWidth={1.5}
                  strokeDasharray="4 2"
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <div className="p-12 text-center text-[#BFA8BA] text-xs">
            No pressure timeline records available for this innings.
          </div>
        )}
      </div>

      {/* Factor Decomposition Dashboard for Selected Ball */}
      {activeBall && (
        <div className="p-6 rounded-3xl bg-[#20091F] border border-[#400A2D] shadow-rr-card space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-[#400A2D]">
            <div>
              <span className="text-[11px] font-mono font-bold text-[#C21868] uppercase">
                Delivery Factor Decomposition
              </span>
              <h4 className="text-base font-bold text-white mt-0.5">
                Over {activeBall.overid}.{activeBall.over_ball_num} — {activeBall.striker_name} facing {activeBall.bowler_name}
              </h4>
            </div>
            <div className="flex items-center gap-3 text-xs font-mono">
              <span className="px-3 py-1 rounded-xl bg-[#080510] border border-[#C21868]/40 text-[#C21868]">
                Batting: {formatNum(activeBall.batting_pressure_score, 1)}
              </span>
              <span className="px-3 py-1 rounded-xl bg-[#080510] border border-[#8F2455]/50 text-[#F5EAF2]">
                Bowling: {formatNum(activeBall.bowling_pressure_score, 1)}
              </span>
            </div>
          </div>

          {/* 6 Situation Factor Cards */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 pt-2">
            {/* Wicket Vulnerability */}
            <div className="p-3.5 rounded-2xl bg-[#120817] border border-[#400A2D] space-y-1">
              <div className="text-[11px] text-[#BFA8BA]">Wicket Vulnerability (F_wkt)</div>
              <div className="text-lg font-black text-white font-mono">
                {formatPercent(activeBall.wicket_vulnerability, 1)}
              </div>
              <div className="w-full bg-[#080510] h-1.5 rounded-full overflow-hidden mt-1">
                <div
                  className="bg-[#C21868] h-full rounded-full"
                  style={{ width: `${Math.min(100, (activeBall.wicket_vulnerability || 0) * 100)}%` }}
                ></div>
              </div>
            </div>

            {/* Time Pressure */}
            <div className="p-3.5 rounded-2xl bg-[#120817] border border-[#400A2D] space-y-1">
              <div className="text-[11px] text-[#BFA8BA]">Time Pressure (F_time)</div>
              <div className="text-lg font-black text-white font-mono">
                {formatPercent(activeBall.time_pressure, 1)}
              </div>
              <div className="w-full bg-[#080510] h-1.5 rounded-full overflow-hidden mt-1">
                <div
                  className="bg-[#8F2455] h-full rounded-full"
                  style={{ width: `${Math.min(100, (activeBall.time_pressure || 0) * 100)}%` }}
                ></div>
              </div>
            </div>

            {/* Chase Urgency */}
            <div className="p-3.5 rounded-2xl bg-[#120817] border border-[#400A2D] space-y-1">
              <div className="text-[11px] text-[#BFA8BA]">Chase Urgency (F_chase)</div>
              <div className="text-lg font-black text-white font-mono">
                {formatPercent(activeBall.chase_urgency, 1)}
              </div>
              <div className="w-full bg-[#080510] h-1.5 rounded-full overflow-hidden mt-1">
                <div
                  className="bg-[#D4AF37] h-full rounded-full"
                  style={{ width: `${Math.min(100, (activeBall.chase_urgency || 0) * 100)}%` }}
                ></div>
              </div>
            </div>

            {/* Match Closeness */}
            <div className="p-3.5 rounded-2xl bg-[#120817] border border-[#400A2D] space-y-1">
              <div className="text-[11px] text-[#BFA8BA]">Match Closeness (F_close)</div>
              <div className="text-lg font-black text-white font-mono">
                {formatPercent(activeBall.match_closeness, 1)}
              </div>
              <div className="w-full bg-[#080510] h-1.5 rounded-full overflow-hidden mt-1">
                <div
                  className="bg-[#10B981] h-full rounded-full"
                  style={{ width: `${Math.min(100, (activeBall.match_closeness || 0) * 100)}%` }}
                ></div>
              </div>
            </div>

            {/* 1st Inn Par Deficit */}
            <div className="p-3.5 rounded-2xl bg-[#120817] border border-[#400A2D] space-y-1">
              <div className="text-[11px] text-[#BFA8BA]">Par Deficit (F_par)</div>
              <div className="text-lg font-black text-white font-mono">
                {formatPercent(activeBall.first_inn_par_deficit, 1)}
              </div>
              <div className="w-full bg-[#080510] h-1.5 rounded-full overflow-hidden mt-1">
                <div
                  className="bg-[#D97706] h-full rounded-full"
                  style={{ width: `${Math.min(100, (activeBall.first_inn_par_deficit || 0) * 100)}%` }}
                ></div>
              </div>
            </div>

            {/* Stakes Multiplier */}
            <div className="p-3.5 rounded-2xl bg-[#120817] border border-[#400A2D] space-y-1">
              <div className="text-[11px] text-[#BFA8BA]">Stakes (M_stakes)</div>
              <div className="text-lg font-black text-white font-mono">
                {formatNum(activeBall.match_stakes_multiplier, 2)}x
              </div>
              <div className="w-full bg-[#080510] h-1.5 rounded-full overflow-hidden mt-1">
                <div
                  className="bg-[#9F1239] h-full rounded-full"
                  style={{ width: `${Math.min(100, ((activeBall.match_stakes_multiplier || 1) / 1.5) * 100)}%` }}
                ></div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Formulation Explainer Drawer */}
      <div className="p-6 rounded-3xl bg-[#120817] border border-[#400A2D] shadow-rr-card space-y-3">
        <h4 className="text-sm font-bold text-white flex items-center gap-2">
          <HelpCircle size={16} className="text-[#C21868]" />
          Pressure Index Formulation & Mathematical Architecture
        </h4>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs text-[#BFA8BA]">
          <div className="p-4 rounded-2xl bg-[#080510]/80 border border-[#400A2D] space-y-2">
            <span className="font-bold text-white text-sm">Batting Pressure Model (P_bat)</span>
            <p className="leading-relaxed">
              Calculates the difficulty of scoring runs while preserving wickets:
            </p>
            <div className="p-2.5 rounded-xl bg-[#20091F] font-mono text-[11px] text-[#D4AF37]">
              P_bat = clip( (0.30·F_wkt + 0.25·F_time + 0.25·F_chase + 0.10·F_close + 0.10·F_par) · M_stakes, 0, 100 )
            </div>
          </div>

          <div className="p-4 rounded-2xl bg-[#080510]/80 border border-[#400A2D] space-y-2">
            <span className="font-bold text-white text-sm">Bowling Pressure Model (P_bowl)</span>
            <p className="leading-relaxed">
              Calculates defensive difficulty under tight margins and aggressive opposition:
            </p>
            <div className="p-2.5 rounded-xl bg-[#20091F] font-mono text-[11px] text-[#F5EAF2]">
              P_bowl = clip( (0.20·(1 - F_wkt) + 0.30·F_time + 0.25·F_chase + 0.15·F_close + 0.10·F_par) · M_stakes, 0, 100 )
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
