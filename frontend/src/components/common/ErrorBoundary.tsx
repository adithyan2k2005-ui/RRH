import React, { Component, ErrorInfo, ReactNode } from 'react';
import { AlertTriangle, RefreshCw, Home, ShieldAlert } from 'lucide-react';

interface Props {
  children: ReactNode;
  fallbackTitle?: string;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
    errorInfo: null,
  };

  public static getDerivedStateFromError(error: Error): Partial<State> {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught an unhandled page exception:', error, errorInfo);
    this.setState({ errorInfo });
  }

  private handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
  };

  private handleGoHome = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
    window.location.href = '/';
  };

  public render() {
    if (this.state.hasError) {
      return (
        <div className="p-6 max-w-4xl mx-auto my-8">
          <div className="relative overflow-hidden rounded-3xl bg-[#120817] border-2 border-[#C21868] shadow-2xl p-6 sm:p-8 space-y-6">
            {/* Ambient burgundy background glow */}
            <div className="absolute -top-12 -right-12 w-48 h-48 bg-[#C21868]/20 rounded-full blur-3xl pointer-events-none" />
            <div className="absolute -bottom-12 -left-12 w-48 h-48 bg-[#400A2D]/40 rounded-full blur-3xl pointer-events-none" />

            {/* Error Header */}
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 rounded-2xl bg-[#C21868]/20 border border-[#C21868] flex items-center justify-center shrink-0 text-[#C21868]">
                <ShieldAlert size={28} />
              </div>
              <div className="space-y-1">
                <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-[#20091F] border border-[#C21868]/40 text-[#C21868] text-[11px] font-bold tracking-wider uppercase font-mono">
                  Fault Tolerant Boundary Active
                </div>
                <h3 className="text-xl sm:text-2xl font-black text-white tracking-tight">
                  {this.props.fallbackTitle || 'Analytical Module Display Interrupted'}
                </h3>
                <p className="text-xs text-[#BFA8BA] leading-relaxed max-w-2xl">
                  An isolated rendering exception occurred in this module. The global navigation shell and all other 6 platform routes remain operational.
                </p>
              </div>
            </div>

            {/* Error Diagnostics Box */}
            <div className="p-4 rounded-2xl bg-[#080510] border border-[#400A2D] font-mono text-xs space-y-2">
              <div className="flex items-center justify-between text-[#826D7D] text-[11px] border-b border-[#400A2D]/60 pb-1.5">
                <span>ERROR EXCEPTION</span>
                <span>{new Date().toLocaleTimeString()}</span>
              </div>
              <p className="text-[#C21868] font-bold break-all">
                {this.state.error?.name}: {this.state.error?.message || 'Unknown runtime error'}
              </p>
              {this.state.errorInfo?.componentStack && (
                <details className="text-[10px] text-[#826D7D] pt-1">
                  <summary className="cursor-pointer text-[#BFA8BA] hover:text-white transition-colors">
                    View Component Stack
                  </summary>
                  <pre className="mt-2 p-2 bg-[#120817] rounded-lg overflow-x-auto max-h-40 text-[#BFA8BA]">
                    {this.state.errorInfo.componentStack}
                  </pre>
                </details>
              )}
            </div>

            {/* Actions */}
            <div className="flex flex-wrap items-center gap-3 pt-2 border-t border-[#400A2D]">
              <button
                onClick={this.handleReset}
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-[#C21868] to-[#8F2455] text-white text-xs font-bold hover:shadow-rr-glow transition-all"
              >
                <RefreshCw size={14} /> Retry This Module
              </button>
              <button
                onClick={this.handleGoHome}
                className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-[#20091F] border border-[#400A2D] text-[#BFA8BA] hover:text-white hover:border-[#C21868]/50 text-xs font-semibold transition-colors"
              >
                <Home size={14} /> Return to Overview
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
