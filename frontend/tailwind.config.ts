import type { Config } from "tailwindcss";

export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Graphite-navy surfaces (Linear/Notion-style dark UI), not pure black.
        surface: {
          950: "#0B0E14",
          900: "#11151D",
          850: "#161B26",
          800: "#1D2330",
          700: "#2A3141",
          600: "#3B4459",
          400: "#7B869C",
          200: "#C4CBD9",
          100: "#E7EAF0",
        },
        // Signal accent: indigo-violet, used sparingly (primary actions, active states).
        signal: {
          400: "#8B7CF6",
          500: "#6E56CF",
          600: "#5940B3",
        },
        // Data accent: teal, reserved for charts/forecast lines so it never competes with signal.
        data: {
          teal: "#2DD4BF",
          amber: "#F5A623",
          rose: "#F4657A",
          sky: "#5EA1F2",
        },
        success: "#3ECF8E",
        warning: "#F5A623",
        danger: "#F4657A",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "ui-monospace", "monospace"],
      },
      borderRadius: {
        card: "10px",
      },
      boxShadow: {
        card: "0 1px 2px rgba(0,0,0,0.4), 0 0 0 1px rgba(255,255,255,0.03)",
      },
    },
  },
  plugins: [],
} satisfies Config;
