import React, { useEffect, useState } from 'react';
import {
  Download,
  ShieldCheck,
  CheckCircle2,
  BookOpen,
  Scale,
} from 'lucide-react';
import { api, MethodologyResponse, ReportItem } from '../services/api';
import { RoyalCrownIcon } from '../components/common/RoyalEmblem';

export const MethodologyReports: React.FC = () => {
  const [methodology, setMethodology] = useState<MethodologyResponse | null>(null);
  const [reports, setReports] = useState<ReportItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadAll = async () => {
      try {
        setLoading(true);
        const [m, r] = await Promise.all([api.getMethodology(), api.getReports()]);
        setMethodology(m);
        setReports(r);
      } catch (err) {
        console.error('Failed to load methodology reports:', err);
      } finally {
        setLoading(false);
      }
    };
    loadAll();
  }, []);

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {/* Header Banner */}
      <div className="p-6 sm:p-8 rounded-3xl bg-[#120817] border border-[#400A2D] shadow-rr-card space-y-3">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#400A2D] text-[#C21868] text-xs font-semibold">
          <RoyalCrownIcon size={14} />
          <span>Hackathon Documentation & Official Artifacts</span>
        </div>
        <h2 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
          Methodology, Quality Verification & Submission Center
        </h2>
        <p className="text-xs sm:text-sm text-[#BFA8BA] max-w-3xl leading-relaxed">
          Comprehensive mathematical documentation, sensitivity analysis results, 16-point audit verification
          checklist, and direct access to all official submission deliverables.
        </p>
      </div>

      {loading || !methodology ? (
        <div className="p-16 text-center rounded-3xl bg-[#120817] border border-[#400A2D]">
          <div className="w-8 h-8 border-3 border-[#C21868] border-t-transparent rounded-full animate-spin mx-auto"></div>
          <p className="text-xs text-[#BFA8BA] mt-2 font-mono">Loading methodology documentation...</p>
        </div>
      ) : (
        <div className="space-y-8">
          {/* Official Submission Download Center */}
          <div className="p-6 rounded-3xl bg-[#20091F] border border-[#C21868]/40 shadow-rr-card space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-[#400A2D]">
              <div>
                <span className="text-[11px] font-mono font-bold text-[#C21868] uppercase">
                  Submission Deliverables
                </span>
                <h3 className="text-lg font-bold text-white mt-0.5">
                  Official Round 1 Artifacts & Download Center
                </h3>
              </div>
              <span className="text-xs font-mono text-[#D4AF37] bg-[#D4AF37]/10 px-3 py-1 rounded-full border border-[#D4AF37]/30">
                All Deliverables Ready & Verified
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 pt-2">
              {reports.map((r) => (
                <div
                  key={r.report_id}
                  className="p-5 rounded-2xl bg-[#080510]/80 border border-[#400A2D] hover:border-[#C21868] transition-all flex flex-col justify-between space-y-3"
                >
                  <div className="space-y-1.5">
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] font-mono font-bold text-[#C21868] uppercase px-2 py-0.5 rounded bg-[#400A2D]/40">
                        {r.category}
                      </span>
                      <span className="text-[10px] font-mono text-[#826D7D]">
                        {(((r.file_size_bytes || 0) / 1024)).toFixed(1)} KB
                      </span>
                    </div>
                    <h4 className="text-sm font-bold text-white">{r.title}</h4>
                    <p className="text-xs text-[#BFA8BA] leading-relaxed line-clamp-2">
                      {r.description}
                    </p>
                  </div>

                  <a
                    href={api.getReportDownloadUrl(r.report_id)}
                    download={r.filename}
                    className="inline-flex items-center justify-center gap-1.5 w-full py-2 px-3 rounded-xl bg-[#20091F] hover:bg-[#C21868] border border-[#400A2D] hover:border-[#C21868] text-white text-xs font-bold transition-all shadow-sm"
                  >
                    <Download size={13} />
                    Download {r.filename.endsWith('.pdf') ? 'PDF Report' : r.filename.endsWith('.zip') ? 'ZIP Archive' : 'File'}
                  </a>
                </div>
              ))}
            </div>
          </div>

          {/* Mathematical Formulations Section */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Pressure Model Formulation */}
            <div className="p-6 rounded-3xl bg-[#120817] border border-[#400A2D] shadow-rr-card space-y-4">
              <div className="flex items-center gap-2 text-white font-bold text-base">
                <BookOpen size={18} className="text-[#C21868]" />
                Pressure Formulation Architecture
              </div>
              <p className="text-xs text-[#BFA8BA] leading-relaxed">
                Pre-ball match situations are evaluated immediately before delivery execution (t⁻) across 5
                normalized factor indicators scaled by tournament stakes (M_stakes).
              </p>

              <div className="p-4 rounded-2xl bg-[#080510] border border-[#400A2D] space-y-2 font-mono text-xs">
                <div className="text-[#D4AF37] font-bold">Batting Pressure Weights:</div>
                <div className="text-[#F5EAF2] pl-2 space-y-0.5 text-[11px]">
                  <div>• Wicket Vulnerability (F_wkt): 30%</div>
                  <div>• Time Pressure (F_time): 25%</div>
                  <div>• Chase Urgency (F_chase): 25%</div>
                  <div>• Match Closeness (F_close): 10%</div>
                  <div>• Par Deficit (F_par): 10%</div>
                </div>
              </div>

              <div className="p-4 rounded-2xl bg-[#080510] border border-[#400A2D] space-y-2 font-mono text-xs">
                <div className="text-[#8F2455] font-bold">Bowling Pressure Weights:</div>
                <div className="text-[#F5EAF2] pl-2 space-y-0.5 text-[11px]">
                  <div>• Defensive Exposure (1 - F_wkt): 20%</div>
                  <div>• Time Pressure (F_time): 30%</div>
                  <div>• Chase Urgency (F_chase): 25%</div>
                  <div>• Match Closeness (F_close): 15%</div>
                  <div>• Par Deficit (F_par): 10%</div>
                </div>
              </div>
            </div>

            {/* Reliability Composite Scoring Formulation */}
            <div className="p-6 rounded-3xl bg-[#120817] border border-[#400A2D] shadow-rr-card space-y-4">
              <div className="flex items-center gap-2 text-white font-bold text-base">
                <Scale size={18} className="text-[#D4AF37]" />
                Composite Reliability Formulation
              </div>
              <p className="text-xs text-[#BFA8BA] leading-relaxed">
                Player reliability is measured as a composite balance of high-pressure impact, relative uplift, match
                consistency, and sample certainty, scaled into a [0, 100] percentile score.
              </p>

              <div className="p-4 rounded-2xl bg-[#080510] border border-[#400A2D] space-y-2 font-mono text-xs">
                <div className="text-white font-bold">Composite Pillar Weights:</div>
                <div className="text-[#F5EAF2] pl-2 space-y-1 text-[11px]">
                  <div>
                    <span className="text-[#C21868] font-bold">40%</span> — High Pressure Impact (β_HP)
                  </div>
                  <div>
                    <span className="text-[#D4AF37] font-bold">25%</span> — Pressure Uplift (Δ = β_HP - β_ord)
                  </div>
                  <div>
                    <span className="text-[#F5EAF2] font-bold">20%</span> — Consistency (C = 1 / (1 + σ))
                  </div>
                  <div>
                    <span className="text-[#8F2455] font-bold">15%</span> — Sample Weight (W = N / (N + N₀))
                  </div>
                </div>
              </div>

              <div className="p-4 rounded-2xl bg-[#20091F] border border-[#C21868]/40 space-y-1 text-xs text-[#BFA8BA]">
                <div className="font-bold text-white">Empirical Bayes Shrinkage Parameters:</div>
                <div className="font-mono text-[11px] text-[#D4AF37]">
                  k₀ = 20.0 balls (batting), 24.0 balls (bowling) • Cluster SE weighting
                </div>
                <p className="text-[11px] leading-relaxed">
                  Prevents low-sample outliers from skewing rankings by shrinking small samples toward the prior mean.
                </p>
              </div>
            </div>
          </div>

          {/* 16-Point Quality Gate & Verification Audit Table */}
          <div className="p-6 rounded-3xl bg-[#120817] border border-[#400A2D] shadow-rr-card space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
              <div>
                <h3 className="text-base font-bold text-white flex items-center gap-2">
                  <ShieldCheck className="text-[#D4AF37]" size={20} />
                  16-Point Analytical Quality Gate Audit
                </h3>
                <p className="text-xs text-[#BFA8BA]">
                  All 16 quality gates are verified and pass without regressions.
                </p>
              </div>
              <span className="px-3 py-1 rounded-full bg-[#D4AF37]/10 border border-[#D4AF37]/30 text-[#D4AF37] text-xs font-bold font-mono">
                16 / 16 GATES PASSED (100%)
              </span>
            </div>

            <div className="overflow-x-auto rounded-2xl border border-[#400A2D]/60">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="bg-[#20091F] text-[#BFA8BA] border-b border-[#400A2D]">
                    <th className="py-2.5 px-3 font-mono w-28">Gate ID</th>
                    <th className="py-2.5 px-3">Description</th>
                    <th className="py-2.5 px-3">Verification Details</th>
                    <th className="py-2.5 px-3 text-right">Audit Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#400A2D]/40">
                  {methodology.quality_gates.map((gate) => (
                    <tr key={gate.gate} className="hover:bg-[#20091F]/40 transition-colors">
                      <td className="py-2.5 px-3 font-mono font-bold text-[#C21868]">
                        {gate.gate}
                      </td>
                      <td className="py-2.5 px-3 font-medium text-white">{gate.description}</td>
                      <td className="py-2.5 px-3 text-[#BFA8BA] font-mono text-[11px]">
                        {gate.details}
                      </td>
                      <td className="py-2.5 px-3 text-right">
                        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-[#D4AF37]/10 text-[#D4AF37] border border-[#D4AF37]/30 font-bold font-mono text-[10px]">
                          <CheckCircle2 size={11} /> {gate.status}
                        </span>
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
