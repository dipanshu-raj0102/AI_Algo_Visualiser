/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: { sans: ["Inter", "system-ui", "sans-serif"], mono: ["JetBrains Mono", "monospace"] },
      colors: { ink: "#111827", canvas: "#f7f8fb", signal: "#0f766e", coral: "#f97316" },
    },
  },
  plugins: [],
};
