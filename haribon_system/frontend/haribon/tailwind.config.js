/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        'quicksand': ['Quicksand', 'sans-serif'],
      },
      colors: {
        'haribon-dark': '#203537',
        'haribon-green': '#2ECC71',
        'haribon-yellow': '#F1C40F',
        'haribon-orange': '#E67E22',
        'haribon-red': '#E74C3C',
        'haribon-gray': '#7A8B90',
        'haribon-light-gray': '#8A9AA0',
        'haribon-bg': '#f7f8f9',
      },
    },
  },
  plugins: [],
}