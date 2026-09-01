/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        slate: {
          950: '#0B0F17',
          900: '#111827',
          800: '#1F2937',
        },
        status: {
          active: '#10B981', // Emerald green
          warning: '#F59E0B', // Amber
          danger: '#E11D48', // Crimson red
          fluid: '#06B6D4' // Cyan for trajectories/water
        }
      }
    },
  },
  plugins: [],
}
