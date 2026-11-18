import React from 'react';
import rrRefImg from '../../assets/rajasthan_royals_ref.jpg';

export const RoyalCrownIcon: React.FC<{ size?: number; className?: string }> = ({
  size = 24,
  className = '',
}) => {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 48 48"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      aria-label="Rajasthan Royals Crown"
    >
      {/* Crown base band */}
      <rect x="8" y="36" width="32" height="4" rx="2" fill="#C21868" />
      <circle cx="14" cy="38" r="1" fill="#D4AF37" />
      <circle cx="24" cy="38" r="1" fill="#D4AF37" />
      <circle cx="34" cy="38" r="1" fill="#D4AF37" />

      {/* Main Crown Body with 5 Royal Peaks */}
      <path
        d="M8 34L12 18L20 28L24 10L28 28L36 18L40 34H8Z"
        fill="url(#rr-crown-grad)"
        stroke="#400A2D"
        strokeWidth="1.5"
        strokeLinejoin="round"
      />

      {/* Royal Jewels on Peaks */}
      <circle cx="12" cy="17" r="2.2" fill="#D4AF37" stroke="#400A2D" strokeWidth="1" />
      <circle cx="24" cy="9" r="2.8" fill="#D4AF37" stroke="#400A2D" strokeWidth="1" />
      <circle cx="36" cy="17" r="2.2" fill="#D4AF37" stroke="#400A2D" strokeWidth="1" />

      {/* Inner Central Fleur-de-lis / RR Diamond Accents */}
      <path
        d="M24 16L26.5 22L24 25L21.5 22L24 16Z"
        fill="#FFFFFF"
        opacity="0.9"
      />

      <defs>
        <linearGradient id="rr-crown-grad" x1="8" y1="10" x2="40" y2="34" gradientUnits="userSpaceOnUse">
          <stop stopColor="#D81B75" />
          <stop offset="0.5" stopColor="#C21868" />
          <stop offset="1" stopColor="#8F2455" />
        </linearGradient>
      </defs>
    </svg>
  );
};

export const FramedBrandCard: React.FC<{ className?: string }> = ({ className = '' }) => {
  return (
    <div
      className={`relative overflow-hidden rounded-3xl border border-[#400A2D] bg-[#120817] shadow-2xl p-4 sm:p-5 flex items-center justify-center ${className}`}
    >
      {/* Ambient lighting behind framed image */}
      <div className="absolute -top-10 -left-10 w-44 h-44 bg-[#C21868]/20 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute -bottom-10 -right-10 w-44 h-44 bg-[#400A2D]/40 rounded-full blur-3xl pointer-events-none" />

      {/* Reference Photograph Preserved as a Framed Regal Emblem */}
      <div className="relative shrink-0 w-28 h-28 sm:w-32 sm:h-32 rounded-2xl overflow-hidden border border-[#C21868]/40 shadow-rr-card group">
        <img
          src={rrRefImg}
          alt="Rajasthan Royals emblem"
          className="w-full h-full object-cover object-center transform group-hover:scale-105 transition-transform duration-500"
        />
        <div className="absolute inset-0 ring-1 ring-inset ring-white/10 rounded-2xl pointer-events-none" />
      </div>
    </div>
  );
};
