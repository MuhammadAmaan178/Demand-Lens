/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: '#F8FAFC',
        card: '#FFFFFF',
        border: '#E2E8F0',
        primary: {
          DEFAULT: '#2563EB',
          hover: '#1D4ED8',
          light: '#EFF6FF',
          dark: '#1E40AF',
        },
        navy: {
          DEFAULT: '#0F172A',
          deep: '#1E3A8A',
        },
        text: {
          primary: '#0F172A',
          secondary: '#64748B',
          muted: '#94A3B8',
        },
        success: {
          DEFAULT: '#059669',
          light: '#ECFDF5',
          border: '#A7F3D0',
        },
        warning: {
          DEFAULT: '#D97706',
          light: '#FFFBEB',
          border: '#FDE68A',
        },
        danger: {
          DEFAULT: '#DC2626',
          light: '#FEF2F2',
          border: '#FECACA',
        },
      },
      borderRadius: {
        DEFAULT: '4px',
        card: '4px',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
