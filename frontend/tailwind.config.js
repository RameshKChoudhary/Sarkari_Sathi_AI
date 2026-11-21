/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        ink: { 900: '#14213d', 800: '#1d2e52', 700: '#2b3f6b', 100: '#e6eaf3', 50: '#f1f3f9' },
        saffron: { 600: '#d4710a', 500: '#e8821a', 100: '#fdebd3', 50: '#fff6ea' },
        india: { 700: '#166a41', 600: '#1b7f4f', 100: '#dcf1e5', 50: '#eef8f2' },
        paper: '#faf8f3',
      },
      fontFamily: { sans: ['Mukta', 'Noto Sans Devanagari', 'system-ui', 'sans-serif'] },
      boxShadow: { card: '0 1px 2px rgba(20,33,61,.06), 0 4px 14px rgba(20,33,61,.06)' },
    },
  },
  plugins: [],
}
