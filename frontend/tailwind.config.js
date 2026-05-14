/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        derek: {
          blue: '#1e40af',
          gold: '#b45309',
        },
      },
    },
  },
  plugins: [],
}
