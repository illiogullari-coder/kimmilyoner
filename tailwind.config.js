/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'Segoe UI', 'system-ui', '-apple-system', 'sans-serif'],
        display: ['Sora', 'Inter', 'system-ui', 'sans-serif'],
      },
      colors: {
        night: {
          700: '#111936',
          800: '#0a0f24',
          900: '#050816',
          950: '#03040c',
        },
        cloud: {
          400: '#6ba3ff',
          500: '#4f8cff',
        },
        gold: {
          300: '#fde68a',
          400: '#fbbf24',
          500: '#f59e0b',
          600: '#d97706',
        },
        snow: '#f8fafc',
        dmoz: {
          green: '#27e0c8',
        },
      },
      boxShadow: {
        'gold-glow': '0 0 20px rgba(251,191,36,0.4), 0 0 40px rgba(251,191,36,0.2)',
        'emerald-glow': '0 0 16px rgba(52,211,153,0.5)',
        'red-glow': '0 0 16px rgba(239,68,68,0.5)',
        premium: '0 20px 60px -12px rgba(0,0,0,0.55), 0 0 0 1px rgba(255,255,255,0.06) inset',
      },
      animation: {
        shake: 'shake 0.4s ease-in-out',
        pop: 'pop 0.4s cubic-bezier(0.34,1.56,0.64,1)',
        'slide-in': 'slideIn 0.4s ease-out',
        'pulse-slow': 'pulseSlow 3s ease-in-out infinite',
        'bounce-slow': 'bounceSlow 2s ease-in-out infinite',
        'float-slow': 'floatSlow 8s ease-in-out infinite',
        'float-slower': 'floatSlow 12s ease-in-out infinite',
        shimmer: 'shimmer 3.5s linear infinite',
        'spin-slow': 'spin 14s linear infinite',
        twinkle: 'twinkle 4s ease-in-out infinite',
      },
    },
  },
  plugins: [],
};
