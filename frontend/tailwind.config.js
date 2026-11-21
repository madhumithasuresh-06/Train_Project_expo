/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        rail: {
          50: "#eef8f9",
          100: "#d5eef0",
          200: "#a8dce1",
          300: "#6ec2cb",
          400: "#3fa3b0",
          500: "#268795",
          600: "#1f6d7a",
          700: "#1d5863",
          800: "#1c4952",
          900: "#1b3e46",
          950: "#0a252c",
        },
        navy: {
          800: "#0f2a44",
          900: "#0a1f33",
          950: "#061525",
        },
      },
      fontFamily: {
        sans: ["DM Sans", "system-ui", "sans-serif"],
        display: ["Outfit", "system-ui", "sans-serif"],
      },
      animation: {
        "fade-up": "fadeUp 0.5s ease-out forwards",
        "pulse-soft": "pulseSoft 2s ease-in-out infinite",
      },
      keyframes: {
        fadeUp: {
          "0%": { opacity: "0", transform: "translateY(12px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        pulseSoft: {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.7" },
        },
      },
    },
  },
  plugins: [],
};
