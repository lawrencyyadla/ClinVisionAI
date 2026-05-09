import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{js,ts,jsx,tsx}", "./components/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#171717",
        clinical: "#0f766e",
        signal: "#b45309"
      }
    }
  },
  plugins: []
};

export default config;

