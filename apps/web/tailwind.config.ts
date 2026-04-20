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
      },
    },
  },
  plugins: [],
};

export default config;
