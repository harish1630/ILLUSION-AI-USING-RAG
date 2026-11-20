/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        graphite: {
          50: '#F9FAFB',
          100: '#F3F4F6',
          200: '#E5E7EB',
          300: '#D1D5DB',
          400: '#9CA3AF',
          500: '#6B7280',
          600: '#4B5563',
          700: '#374151',
          800: '#1F2937',
          850: '#181E29',
          900: '#121212',
          950: '#0A0A0A',
        },
        amber: {
          50: '#FFFBEB',
          100: '#FEF3C7',
          200: '#FDE68A',
          300: '#FCD34D',
          400: '#FBBF24',
          500: '#F59E0B',
          600: '#D97706',
          700: '#B45309',
          800: '#92400E',
          900: '#78350F',
          950: '#451A03',
        },
        brand: {
          bg: '#0D0D0E',
          surface: '#151518',
          card: '#1C1C20',
          elevated: '#24242A',
          border: '#2E2E36',
          subtle: '#3E3E48',
          accent: '#F59E0B',
          accentGlow: 'rgba(245, 158, 11, 0.18)',
          text: '#EDEDED',
          muted: '#9E9EA8',
        }
      },
    },
  },
  plugins: [],
};

