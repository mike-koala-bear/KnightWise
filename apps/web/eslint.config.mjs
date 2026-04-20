import nextConfig from 'eslint-config-next';
import nextTypescript from 'eslint-config-next/typescript';
import nextCoreWebVitals from 'eslint-config-next/core-web-vitals';

const config = [
  {
    ignores: ['.next/**', 'node_modules/**', 'next-env.d.ts'],
  },
  ...nextConfig,
  ...nextTypescript,
  ...nextCoreWebVitals,
];

export default config;
