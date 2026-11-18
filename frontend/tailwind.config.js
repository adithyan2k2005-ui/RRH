/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        rr: {
          bg: "#080510",
          bg2: "#120817",
          surface: "#20091F",
          surfaceHover: "#2A1028",
          border: "#400A2D",
          borderLight: "#5A1342",
          pink: "#C21868",
          pinkHover: "#D81B75",
          berry: "#8F2455",
          gold: "#D4AF37",
          goldLight: "#F3D068",
          silver: "#E2E8F0",
          bronze: "#CD7F32",
          text: "#F5EAF2",
          muted: "#BFA8BA",
          dim: "#826D7D",
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      boxShadow: {
        'rr-glow': '0 0 25px -5px rgba(194, 24, 104, 0.4)',
        'rr-card': '0 8px 30px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.05)',
        'rr-elevated': '0 12px 40px rgba(0, 0, 0, 0.7), 0 0 15px rgba(194, 24, 104, 0.25)',
      }
    },
  },
  plugins: [],
}
