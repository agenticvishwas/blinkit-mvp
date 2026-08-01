import type { Config } from "tailwindcss";

// Tokens ported verbatim from design/mockup.html's :root CSS variables --
// treat that file as the source of truth if these ever drift.
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  darkMode: ["class", '[data-theme="dark"]'],
  theme: {
    extend: {
      colors: {
        canvas: { DEFAULT: "#F3EEE2", line: "#E4DCC8" },
        app: { bg: "#FFFDF8", raised: "#FFFFFF" },
        yellow: { 100: "#FFF3D0", 500: "#FFC629", 600: "#F0A800" },
        ink: { 900: "#18161A", 700: "#3A3733", 500: "#6E6A62", 300: "#A8A296" },
        sand: { 100: "#F6F1E4", 200: "#EEE6D2", 300: "#E2D8BE" },
        green: { 600: "#1E9E5A", 100: "#E1F4E9" },
        coral: { 500: "#FF5C4D", 600: "#E84A3C", 100: "#FFE7E2" },
        star: "#F5A623",
      },
      fontFamily: {
        sans: [
          "-apple-system",
          "BlinkMacSystemFont",
          '"Segoe UI"',
          "Roboto",
          '"Helvetica Neue"',
          "Arial",
          "sans-serif",
        ],
      },
      borderRadius: { phone: "46px" },
      boxShadow: {
        phone: "0 40px 80px -32px rgba(24,22,26,.45), 0 8px 24px -12px rgba(24,22,26,.25)",
      },
    },
  },
  plugins: [],
} satisfies Config;
