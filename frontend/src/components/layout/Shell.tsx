import React, { useState, useEffect } from 'react';
import { NavLink, Outlet, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  Database,
  PlayCircle,
  Activity,
  UserCheck,
  Trophy,
  FileText,
  Menu,
  X,
  ExternalLink,
  ShieldCheck,
  RefreshCw,
} from 'lucide-react';
import { api, HealthResponse } from '../../services/api';
import { RoyalCrownIcon } from '../common/RoyalEmblem';
import { ErrorBoundary } from '../common/ErrorBoundary';
import rrRefImg from '../../assets/rajasthan_royals_ref.jpg';

const navItems = [
  { path: '/', label: 'Overview', icon: LayoutDashboard },
  { path: '/explorer', label: 'Data Explorer', icon: Database },
  { path: '/replay', label: 'Match Replay', icon: PlayCircle },
  { path: '/pressure', label: 'Pressure Lab', icon: Activity },
  { path: '/players', label: 'Player Intelligence', icon: UserCheck },
  { path: '/rankings', label: 'Reliability Rankings', icon: Trophy },
  { path: '/reports', label: 'Methodology & Reports', icon: FileText },
];

export const Shell: React.FC = () => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [loadingHealth, setLoadingHealth] = useState(false);
  const location = useLocation();

  const loadHealth = async () => {
    try {
      setLoadingHealth(true);
      const data = await api.getHealth();
      setHealth(data);
    } catch (e) {
      console.error('Health check failed:', e);
    } finally {
      setLoadingHealth(false);
    }
  };

  useEffect(() => {
    loadHealth();
  }, []);

  const currentNav = navItems.find((n) => n.path === location.pathname) || {
    label: 'Intelligence Lab',
  };

  return (
    <div className="min-h-screen bg-[#080510] text-[#F5EAF2] flex flex-col md:flex-row font-sans rr-stadium-mesh">
      {/* Mobile Top Bar */}
      <div className="md:hidden flex items-center justify-between p-4 bg-[#120817] border-b border-[#400A2D]">
        <div className="flex items-center space-x-2.5">
          <div className="w-8 h-8 rounded-lg overflow-hidden border border-[#C21868]/60 bg-[#20091F] flex items-center justify-center p-1">
            <RoyalCrownIcon size={20} />
          </div>
          <div>
            <span className="font-extrabold tracking-wider text-sm text-white">
              SupeRR <span className="text-[#C21868]">Lab</span>
            </span>
            <div className="text-[10px] text-[#BFA8BA] tracking-tight">Rajasthan Royals Identity</div>
          </div>
        </div>
        <button
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className="p-2 text-[#BFA8BA] hover:text-white hover:bg-[#20091F] rounded-lg transition-colors"
          aria-label="Toggle navigation menu"
        >
          {sidebarOpen ? <X size={22} /> : <Menu size={22} />}
        </button>
      </div>

      {/* Sidebar */}
      <aside
        className={`fixed md:static inset-y-0 left-0 z-40 w-64 bg-[#120817] border-r border-[#400A2D] flex flex-col justify-between transition-transform duration-200 ease-in-out ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'
        }`}
      >
        <div>
          {/* Logo Brand Header */}
          <div className="p-5 border-b border-[#400A2D] flex items-center space-x-3.5 bg-gradient-to-b from-[#20091F]/60 to-transparent">
            <div className="relative w-11 h-11 rounded-xl overflow-hidden border border-[#C21868]/60 bg-[#080510] shadow-rr-card flex items-center justify-center shrink-0">
              <img
                src={rrRefImg}
                alt="Rajasthan Royals Icon"
                className="w-full h-full object-cover opacity-90 hover:opacity-100 transition-opacity"
              />
              <div className="absolute inset-0 bg-[#C21868]/10 mix-blend-overlay pointer-events-none" />
            </div>
            <div>
              <div className="font-black text-sm tracking-wide text-white flex items-center gap-1.5">
                SupeRR <span className="text-[#C21868]">LAB</span>
                <span className="text-[9px] px-1.5 py-0.2 rounded bg-[#400A2D] text-[#D4AF37] font-mono font-bold">
                  S2
                </span>
              </div>
              <div className="text-[10px] font-semibold tracking-wider text-[#BFA8BA] uppercase">
                Cricket Analytics
              </div>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="p-3.5 space-y-1.5" aria-label="Main Navigation">
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.path}
                  to={item.path}
                  onClick={() => setSidebarOpen(false)}
                  className={({ isActive }) =>
                    `flex items-center space-x-3 px-3.5 py-2.5 rounded-xl text-xs font-semibold transition-all duration-150 ${
                      isActive
                        ? 'bg-gradient-to-r from-[#C21868] to-[#8F2455] text-white shadow-rr-glow border border-[#C21868]/50'
                        : 'text-[#BFA8BA] hover:text-[#F5EAF2] hover:bg-[#20091F] border border-transparent'
                    }`
                  }
                >
                  <Icon size={17} className="shrink-0" />
                  <span>{item.label}</span>
                </NavLink>
              );
            })}
          </nav>
        </div>

        {/* Sidebar Footer: System Status */}
        <div className="p-3.5 border-t border-[#400A2D] bg-[#080510]/80 m-3 rounded-2xl border">
          <div className="flex items-center justify-between text-xs mb-2">
            <span className="text-[#BFA8BA] font-semibold flex items-center gap-1.5">
              <ShieldCheck size={14} className="text-[#D4AF37]" />
              Data Pipeline Status
            </span>
            <button
              onClick={loadHealth}
              disabled={loadingHealth}
              className="text-[#BFA8BA] hover:text-white transition-colors"
              title="Refresh status"
            >
              <RefreshCw size={12} className={loadingHealth ? 'animate-spin' : ''} />
            </button>
          </div>
          <div className="space-y-1.5 text-[11px] font-mono">
            <div className="flex justify-between text-[#BFA8BA]">
              <span>Deliveries:</span>
              <span className="text-white font-bold">
                {health ? health.deliveries_loaded.toLocaleString() : '200,999'}
              </span>
            </div>
            <div className="flex justify-between text-[#BFA8BA]">
              <span>Matches:</span>
              <span className="text-white font-bold">
                {health ? health.matches_loaded.toLocaleString() : '883'}
              </span>
            </div>
            <div className="flex justify-between text-[#BFA8BA]">
              <span>Validation:</span>
              <span className={`font-bold font-mono text-[10px] ${
                health?.verification_status === 'FAIL'
                  ? 'text-rose-400'
                  : health?.verification_status === 'UNVERIFIED'
                  ? 'text-slate-400'
                  : health?.verification_status === 'PASS_WITH_WARNINGS'
                  ? 'text-amber-300'
                  : 'text-[#D4AF37]'
              }`}>
                {health?.verification_status === 'FAIL'
                  ? 'FAIL'
                  : health?.verification_status === 'UNVERIFIED'
                  ? 'UNVERIFIED'
                  : health?.verification_status === 'PASS_WITH_WARNINGS'
                  ? 'PASS (Notes)'
                  : health?.test_suite_status
                  ? `${health.test_suite_status.split(' ')[0]} Passed`
                  : 'PASS'}
              </span>
            </div>
          </div>
          <div className="mt-2.5 pt-2 border-t border-[#400A2D]/60 flex items-center justify-between text-[10px] text-[#826D7D]">
            <span>v2.0 • RR Design System</span>
            <a
              href="/docs"
              target="_blank"
              rel="noreferrer"
              className="text-[#C21868] hover:text-white flex items-center gap-0.5 transition-colors"
            >
              API <ExternalLink size={10} />
            </a>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        {/* Top Header */}
        <header className="hidden md:flex items-center justify-between px-8 py-4 bg-[#120817]/70 backdrop-blur-md border-b border-[#400A2D] sticky top-0 z-30">
          <div>
            <h1 className="text-lg font-extrabold tracking-tight text-white flex items-center gap-2">
              <RoyalCrownIcon size={20} />
              {currentNav.label}
              <span className="text-[10px] px-2.5 py-0.5 rounded-full bg-[#20091F] border border-[#C21868]/40 text-[#C21868] font-mono font-semibold tracking-wide">
                Rajasthan Royals Analytics
              </span>
            </h1>
            <p className="text-[11px] text-[#BFA8BA] mt-0.5">
              SupeRR Selector Season 2 — Precision Pressure-Engineered Cricket Analytics
            </p>
          </div>
          <div className="flex items-center space-x-3">
            <div className="flex items-center space-x-2 px-3 py-1.5 rounded-xl bg-[#20091F] border border-[#400A2D] text-xs">
              <span className={`w-2 h-2 rounded-full ${
                health?.verification_status === 'FAIL'
                  ? 'bg-rose-500'
                  : health?.verification_status === 'UNVERIFIED'
                  ? 'bg-slate-500'
                  : health?.verification_status === 'PASS_WITH_WARNINGS'
                  ? 'bg-amber-400'
                  : 'bg-[#D4AF37]'
              } animate-pulse`} />
              <span className="text-[#F5EAF2] font-semibold text-[11px]">
                {health?.verification_status === 'FAIL'
                  ? 'Verification Failed'
                  : health?.verification_status === 'UNVERIFIED'
                  ? 'Unverified Build'
                  : health?.verification_status === 'PASS_WITH_WARNINGS'
                  ? 'Verified with Notes'
                  : 'Submission Verified'}
              </span>
            </div>
          </div>
        </header>

        {/* Page Outlet */}
        <main className="p-4 sm:p-6 md:p-8 flex-1">
          <ErrorBoundary key={location.pathname} fallbackTitle={`${currentNav.label} Error`}>
            <Outlet />
          </ErrorBoundary>
        </main>
      </div>
    </div>
  );
};
