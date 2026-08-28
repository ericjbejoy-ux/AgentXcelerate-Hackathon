/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: { sans: ['Inter', 'system-ui', 'sans-serif'] },
      colors: {
        brand: { 50:'#eff6f5', 100:'#d7ece9', 200:'#aed9d4', 400:'#2bb5a3', 500:'#0d9488', 600:'#0b7f75', 700:'#09665e' },
        surface: { DEFAULT:'#ffffff', hover:'#fafaf8', muted:'#f4f3ef' },
        muted: '#8a8f98',
        ink: { DEFAULT:'#12161f', soft:'#3c4250', faint:'#697080' },
      },
      boxShadow: {
        card: '0 1px 2px rgba(18,22,31,0.04), 0 8px 24px rgba(18,22,31,0.06)',
        lift: '0 2px 4px rgba(18,22,31,0.06), 0 16px 40px rgba(18,22,31,0.12)',
      },
      borderRadius: { xl: '16px', '2xl': '20px' },
    },
  },
  plugins: [],
}

