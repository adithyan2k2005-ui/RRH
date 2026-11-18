import React, { useEffect, useState } from 'react';
import {
  PlayCircle,
  ShieldCheck,
  ChevronLeft,
  ChevronRight,
  Flame,
  Calendar,
  MapPin,
  Trophy,
  Users,
} from 'lucide-react';
import { api, MatchSummary, DeliveryState } from '../services/api';
import { RoyalCrownIcon } from '../components/common/RoyalEmblem';
import { formatNum } from '../utils/format';

export const MatchReplay: React.FC = () => {
  const [matches, setMatches] = useState<MatchSummary[]>([]);
  const [selectedMatchId, setSelectedMatchId] = useState<number | null>(null);
  const [matchDetail, setMatchDetail] = useState<MatchSummary | null>(null);
  const [selectedInnings, setSelectedInnings] = useState<number>(1);
  const [deliveries, setDeliveries] = useState<DeliveryState[]>([]);
  const [currentDeliveryIndex, setCurrentDeliveryIndex] = useState<number>(0);
  const [loadingMatches, setLoadingMatches] = useState(true);
  const [loadingDeliveries, setLoadingDeliveries] = useState(false);

  // Load matches list
  useEffect(() => {
    const loadMatches = async () => {
      try {
        setLoadingMatches(true);
        const data = await api.getMatches(undefined, undefined, undefined, undefined, 50);
        setMatches(data);
        if (data.length > 0 && selectedMatchId === null) {
          setSelectedMatchId(data[0].match_id);
        }
      } catch (err) {
        console.error('Failed to load matches:', err);
      } finally {
        setLoadingMatches(false);
      }
    };
    loadMatches();
  }, []);

  // Load match detail and deliveries when match or innings changes
  useEffect(() => {
    if (selectedMatchId === null) return;
    const loadData = async () => {
      try {
        setLoadingDeliveries(true);
        const [detail, delivs] = await Promise.all([
          api.getMatchDetail(selectedMatchId),
          api.getMatchDeliveries(selectedMatchId, selectedInnings),
        ]);
        setMatchDetail(detail);
        setDeliveries(delivs);
        setCurrentDeliveryIndex(0);
      } catch (err) {
        console.error('Failed to load match detail or deliveries:', err);
      } finally {
        setLoadingDeliveries(false);
      }
    };
    loadData();
  }, [selectedMatchId, selectedInnings]);

  const currentBall = deliveries[currentDeliveryIndex] || null;

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header & Match Selector Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-6 rounded-3xl bg-[#120817] border border-[#400A2D] shadow-rr-card">
        <div>
          <h2 className="text-xl sm:text-2xl font-extrabold text-white flex items-center gap-2">
            <PlayCircle className="text-[#C21868]" size={24} />
            Ball-by-Ball Match-State Replay
          </h2>
          <p className="text-xs text-[#BFA8BA] mt-1">
            Zero-leakage chronological simulation. Inspect exact match situation immediately before every ball release.
          </p>
        </div>

        {/* Match Selector */}
        <div className="flex items-center gap-3">
          <select
            value={selectedMatchId || ''}
            onChange={(e) => setSelectedMatchId(Number(e.target.value))}
            disabled={loadingMatches}
            className="px-4 py-2 rounded-xl bg-[#20091F] border border-[#400A2D] text-white text-xs font-semibold focus:outline-none focus:border-[#C21868] max-w-xs truncate"
          >
            {matches.map((m) => (
              <option key={m.match_id} value={m.match_id}>
                Match #{m.match_id}: {m.team1_name} vs {m.team2_name} ({m.comp_name})
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Match Context Scoreboard Banner */}
      {matchDetail && (
        <div className="p-6 rounded-3xl bg-gradient-to-r from-[#20091F] via-[#120817] to-[#080510] border border-[#400A2D] shadow-rr-card space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <div className="flex items-center gap-2 text-xs font-mono text-[#C21868]">
                <span>{matchDetail.comp_name}</span>
                <span>•</span>
                <span>{matchDetail.stage}</span>
              </div>
              <h3 className="text-xl sm:text-2xl font-black text-white mt-1">
                {matchDetail.team1_name} <span className="text-[#8F2455] font-light">vs</span> {matchDetail.team2_name}
              </h3>
            </div>

            <div className="flex items-center gap-3 text-xs text-[#BFA8BA]">
              <span className="flex items-center gap-1.5">
                <Calendar size={13} className="text-[#8F2455]" /> {matchDetail.match_date}
              </span>
              <span>•</span>
              <span className="flex items-center gap-1.5">
                <MapPin size={13} className="text-[#8F2455]" /> {matchDetail.venue}
              </span>
            </div>
          </div>

          <div className="flex flex-wrap items-center justify-between gap-3 pt-3 border-t border-[#400A2D]/60 text-xs">
            <div className="flex items-center gap-2">
              <Trophy size={14} className="text-[#D4AF37]" />
              <span className="text-white font-semibold">{matchDetail.result_margin || 'Result recorded'}</span>
            </div>

            {/* Innings Selector Buttons */}
            <div className="flex items-center gap-2">
              <span className="text-[#BFA8BA] text-xs">Innings:</span>
              {matchDetail.innings_available.map((inn) => (
                <button
                  key={inn}
                  onClick={() => setSelectedInnings(inn)}
                  className={`px-3.5 py-1 rounded-xl text-xs font-bold transition-all ${selectedInnings === inn
                      ? 'bg-gradient-to-r from-[#C21868] to-[#8F2455] text-white shadow-rr-glow border border-[#C21868]/50'
                      : 'bg-[#080510] text-[#BFA8BA] border border-[#400A2D] hover:text-white'
                    }`}
                >
                  Innings {inn}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Replay Scrubber and Situation Board */}
      {loadingDeliveries ? (
        <div className="p-12 text-center space-y-2 rounded-3xl bg-[#120817] border border-[#400A2D]">
          <div className="w-8 h-8 border-3 border-[#C21868] border-t-transparent rounded-full animate-spin mx-auto"></div>
          <p className="text-xs text-[#BFA8BA]">Reconstructing ball-by-ball delivery states...</p>
        </div>
      ) : deliveries.length === 0 ? (
        <div className="p-12 text-center rounded-3xl bg-[#120817] border border-[#400A2D] text-[#BFA8BA]">
          No delivery records available for this innings.
        </div>
      ) : currentBall ? (
        <div className="space-y-6">
          {/* Timeline Scrubber */}
          <div className="p-5 rounded-3xl bg-[#120817] border border-[#400A2D] shadow-rr-card space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setCurrentDeliveryIndex((i) => Math.max(0, i - 1))}
                  disabled={currentDeliveryIndex === 0}
                  className="p-2 rounded-xl bg-[#20091F] border border-[#400A2D] text-white disabled:opacity-30 disabled:cursor-not-allowed hover:bg-[#C21868] transition-colors"
                >
                  <ChevronLeft size={16} />
                </button>
                <button
                  onClick={() => setCurrentDeliveryIndex((i) => Math.min(deliveries.length - 1, i + 1))}
                  disabled={currentDeliveryIndex >= deliveries.length - 1}
                  className="p-2 rounded-xl bg-[#20091F] border border-[#400A2D] text-white disabled:opacity-30 disabled:cursor-not-allowed hover:bg-[#C21868] transition-colors"
                >
                  <ChevronRight size={16} />
                </button>
                <div className="text-xs font-mono text-white">
                  Ball <span className="font-bold text-[#D4AF37]">{currentDeliveryIndex + 1}</span> of {deliveries.length}
                </div>
              </div>

              <div className="text-xs font-mono px-3 py-1 rounded-full bg-[#20091F] border border-[#400A2D] text-[#F5EAF2]">
                Over {currentBall.overid}.{currentBall.over_ball_num}
              </div>
            </div>

            {/* Range Scrubber Bar */}
            <input
              type="range"
              min={0}
              max={deliveries.length - 1}
              value={currentDeliveryIndex}
              onChange={(e) => setCurrentDeliveryIndex(Number(e.target.value))}
              className="w-full accent-[#C21868] cursor-pointer bg-[#20091F] h-2 rounded-lg"
            />
          </div>

          {/* Pre-Ball Situation Board */}
          <div className="p-6 rounded-3xl bg-[#20091F] border border-[#400A2D] shadow-rr-card space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-[#400A2D]">
              <div className="flex items-center gap-2">
                <ShieldCheck className="text-[#D4AF37]" size={18} />
                <h4 className="text-xs sm:text-sm font-bold text-white uppercase tracking-wider">
                  Pre-Ball Match State (Immediately Preceding Delivery Release)
                </h4>
              </div>
              <span className="text-[10px] font-mono font-bold text-[#D4AF37] bg-[#D4AF37]/10 px-2.5 py-0.5 rounded-full border border-[#D4AF37]/30">
                ZERO FUTURE LEAKAGE GUARANTEED
              </span>
            </div>

            {/* Scoreboard Display */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <div className="p-4 rounded-2xl bg-[#080510]/80 border border-[#400A2D]">
                <div className="text-[11px] text-[#BFA8BA]">Score Before</div>
                <div className="text-2xl sm:text-3xl font-black text-white font-mono mt-1">
                  {currentBall.innings_score_before} / {currentBall.wickets_lost_before}
                </div>
                <div className="text-[10px] text-[#826D7D] mt-0.5">
                  {currentBall.legal_balls_bowled_before} legal balls bowled
                </div>
              </div>

              <div className="p-4 rounded-2xl bg-[#080510]/80 border border-[#400A2D]">
                <div className="text-[11px] text-[#BFA8BA]">Balls Remaining</div>
                <div className="text-2xl sm:text-3xl font-black text-[#F5EAF2] font-mono mt-1">
                  {currentBall.scheduled_balls_remaining_before}
                </div>
                <div className="text-[10px] text-[#826D7D] mt-0.5">
                  {formatNum(currentBall.scheduled_balls_remaining_before / 6, 1)} overs left
                </div>
              </div>

              <div className="p-4 rounded-2xl bg-[#080510]/80 border border-[#400A2D]">
                <div className="text-[11px] text-[#BFA8BA]">Current Run Rate (CRR)</div>
                <div className="text-2xl sm:text-3xl font-black text-white font-mono mt-1">
                  {formatNum(currentBall.current_run_rate, 2)}
                </div>
                <div className="text-[10px] text-[#826D7D] mt-0.5">Runs per over</div>
              </div>

              <div className="p-4 rounded-2xl bg-[#080510]/80 border border-[#400A2D]">
                <div className="text-[11px] text-[#BFA8BA]">
                  {currentBall.runs_required_before !== null ? 'Required Run Rate (RRR)' : 'Target Context'}
                </div>
                <div className="text-2xl sm:text-3xl font-black text-[#D4AF37] font-mono mt-1">
                  {currentBall.required_run_rate != null
                    ? formatNum(currentBall.required_run_rate, 2)
                    : '1st Innings Par'}
                </div>
                <div className="text-[10px] text-[#826D7D] mt-0.5">
                  {currentBall.runs_required_before !== null
                    ? `${currentBall.runs_required_before} runs needed`
                    : 'Setting target'}
                </div>
              </div>
            </div>

            {/* Pressure Indices Snapshot */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-2">
              <div className="p-4 rounded-2xl bg-[#120817] border border-[#C21868]/50">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-[#BFA8BA]">Batting Pressure</span>
                  <Flame size={14} className="text-[#C21868]" />
                </div>
                <div className="text-2xl font-black text-[#C21868] font-mono mt-1">
                  {formatNum(currentBall.batting_pressure_score, 1)} / 100
                </div>
                <div className="text-[11px] text-white mt-1 font-semibold">
                  Class: {currentBall.batting_pressure_class || 'Standard'}
                </div>
              </div>

              <div className="p-4 rounded-2xl bg-[#120817] border border-[#8F2455]/60">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-[#BFA8BA]">Bowling Pressure</span>
                  <Flame size={14} className="text-[#8F2455]" />
                </div>
                <div className="text-2xl font-black text-[#F5EAF2] font-mono mt-1">
                  {formatNum(currentBall.bowling_pressure_score, 1)} / 100
                </div>
                <div className="text-[11px] text-white mt-1 font-semibold">
                  Class: {currentBall.bowling_pressure_class || 'Standard'}
                </div>
              </div>

              <div className="p-4 rounded-2xl bg-[#120817] border border-[#D4AF37]/50">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-[#BFA8BA]">Match Tension Score</span>
                  <Flame size={14} className="text-[#D4AF37]" />
                </div>
                <div className="text-2xl font-black text-[#D4AF37] font-mono mt-1">
                  {formatNum(currentBall.match_tension_score, 1)} / 100
                </div>
                <div className="text-[11px] text-white mt-1 font-semibold">
                  Stakes Multiplier: {formatNum(currentBall.match_stakes_multiplier, 2)}x
                </div>
              </div>
            </div>
          </div>

          {/* Delivery Release & Outcome Card */}
          <div className="p-6 rounded-3xl bg-[#120817] border border-[#400A2D] shadow-rr-card space-y-4">
            <h4 className="text-sm font-bold text-white flex items-center gap-2">
              <Users size={16} className="text-[#C21868]" />
              Delivery Action & Verified Outcome
            </h4>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="p-4 rounded-2xl bg-[#080510]/80 border border-[#400A2D]">
                <div className="text-xs text-[#BFA8BA]">Striker (Batter)</div>
                <div className="text-base font-bold text-white mt-1">{currentBall.striker_name}</div>
                <div className="text-[11px] text-[#826D7D] font-mono">ID: {currentBall.striker_id}</div>
                <div className="text-xs text-[#826D7D] mt-2">
                  Non-striker: {currentBall.non_striker_name || '—'}
                </div>
              </div>

              <div className="p-4 rounded-2xl bg-[#080510]/80 border border-[#400A2D]">
                <div className="text-xs text-[#BFA8BA]">Bowler</div>
                <div className="text-base font-bold text-white mt-1">{currentBall.bowler_name}</div>
                <div className="text-[11px] text-[#826D7D] font-mono">ID: {currentBall.bowler_id}</div>
                <div className="text-xs text-[#826D7D] mt-2">
                  Legal Delivery: {currentBall.is_legal_ball ? 'Yes' : 'No (Extra)'}
                </div>
              </div>

              <div className="p-4 rounded-2xl bg-[#20091F] border border-[#400A2D]">
                <div className="text-xs text-[#BFA8BA]">Outcome on this Ball</div>
                <div className="text-2xl font-black text-white font-mono mt-1">
                  {currentBall.runs_scored_on_ball} Runs
                  {currentBall.extras_on_ball > 0 && (
                    <span className="text-xs text-[#D4AF37] font-normal ml-2">
                      (+{currentBall.extras_on_ball} extras)
                    </span>
                  )}
                </div>
                {currentBall.is_team_wicket ? (
                  <div className="mt-2 inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-red-500/20 text-red-400 border border-red-500/40 text-xs font-bold">
                    <span>WICKET!</span>
                    <span className="text-[10px] text-white">({currentBall.dismissal_type || 'Dismissed'})</span>
                  </div>
                ) : (
                  <div className="text-xs text-[#10B981] mt-2 font-medium">No wicket lost</div>
                )}
              </div>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
};
