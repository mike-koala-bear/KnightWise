import type { Config } from 'tailwindcss';

const config: Config = {
  content: ['./app/**/*.{ts,tsx,mdx}', './components/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        galaxy: {
          bg: '#0b1020',
          node: '#1a2340',
          accent: '#6ae0ff',
        },
        kw: {
          green: '#58CC02',
          'green-dark': '#46A302',
          'green-light': '#89E219',
          blue: '#1CB0F6',
          'blue-dark': '#0E8FC0',
          purple: '#CE82FF',
          'purple-dark': '#A560D8',
          yellow: '#FFD900',
          'yellow-dark': '#E6C300',
          red: '#FF4B4B',
          'red-dark': '#CC3D3D',
          bg: '#0f1923',
          surface: '#1a2636',
          'surface-2': '#243347',
          border: 'rgba(255,255,255,0.08)',
          muted: '#64748b',
        },
      },
      keyframes: {
        'bounce-in': {
          '0%': { transform: 'scale(0.8)', opacity: '0' },
          '60%': { transform: 'scale(1.08)' },
          '100%': { transform: 'scale(1)', opacity: '1' },
        },
        'slide-up': {
          '0%': { transform: 'translateY(16px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        'pulse-green': {
          '0%, 100%': { boxShadow: '0 0 0 0 rgba(88,204,2,0.4)' },
          '50%': { boxShadow: '0 0 0 8px rgba(88,204,2,0)' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
      },
      animation: {
        'bounce-in': 'bounce-in 0.4s ease-out',
        'slide-up': 'slide-up 0.3s ease-out',
        'pulse-green': 'pulse-green 2s infinite',
        shimmer: 'shimmer 2s linear infinite',
      },
    },
  },
  plugins: [],
};

export default config;
