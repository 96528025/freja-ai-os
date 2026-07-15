import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#20201e",
        paper: "#f7f6f1",
        coral: "#ef694f",
        moss: "#657d52",
        sky: "#4d83a7",
        gold: "#d5a53f"
      },
      boxShadow: {
        float: "0 12px 40px rgba(32, 32, 30, 0.08)"
      }
    }
  },
  plugins: []
};

export default config;

