/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      boxShadow: {
        soft: "0 10px 30px rgba(15, 23, 42, 0.10)",
      },
      keyframes: {
        fadeInUp: {
          "0%": { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
      },
      animation: {
        fadeInUp: "fadeInUp 260ms ease-out",
      },
    },
  },
  plugins: [require("daisyui")],
  daisyui: {
    themes: [
      {
        clinical: {
          primary: "#0ea5e9",
          secondary: "#14b8a6",
          accent: "#f59e0b",
          neutral: "#0f172a",
          "base-100": "#f8fbff",
          "base-200": "#edf4fb",
          "base-300": "#dce7f3",
          info: "#2563eb",
          success: "#16a34a",
          warning: "#f59e0b",
          error: "#dc2626",
        },
      },
    ],
  },
};
