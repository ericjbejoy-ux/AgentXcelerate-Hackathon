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
        brand: { 50:'#e8edfb', 100:'#d1dbf7', 200:'#a3b7ef', 400:'#5580e0', 500:'#315cda', 600:'#2648b0', 700:'#1d378a' },
        surface: { DEFAULT:'#ffffff', hover:'#fafaf9', muted:'#f5f5f3' },
        muted: '#999999',
      },
    },
  },
  plugins: [],
}

