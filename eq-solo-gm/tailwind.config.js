/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js,ts}'],
  theme: {
    extend: {
      colors: {
        eq: {
          gold: '#d4af37',
          dark: '#0d1117',
          panel: '#161b22',
          border: '#30363d',
        },
      },
    },
  },
  plugins: [],
}
