/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        dark: {
          900: '#0f1115',
          800: '#16191f',
          700: '#21252d',
          600: '#2d323c'
        },
        brand: {
          blue: '#3b82f6',
          purple: '#8b5cf6',
          green: '#10b981',
          red: '#ef4444'
        }
      }
    },
  },
  plugins: [],
}
