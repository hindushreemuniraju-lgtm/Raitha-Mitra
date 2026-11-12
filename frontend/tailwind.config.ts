import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        forest: "#176B35",
        deep: "#104B29",
        leaf: "#56A832",
        cream: "#FAF9F2",
        mint: "#EDF5E9",
        ink: "#202820",
        muted: "#718071",
        warning: "#E7A72B",
        danger: "#D9534F",
      },
      fontFamily: {
        sans: [
          "Plus Jakarta Sans",
          "Noto Sans Kannada",
          "Noto Sans Devanagari",
          "Noto Sans Telugu",
          "Noto Sans Tamil",
          "system-ui",
          "sans-serif",
        ],
      },
      boxShadow: {
        soft: "0 4px 20px -2px rgba(16, 75, 41, 0.06), 0 1px 4px rgba(16, 75, 41, 0.04)",
        card: "0 2px 12px rgba(32, 40, 32, 0.05)",
      },
    },
  },
  plugins: [],
};

export default config;
