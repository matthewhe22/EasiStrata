/** EasiStrata Tailwind config — Task App "Cobalt" design tokens.
 *  Compiled to static/css/tailwind.build.css (self-hosted, no CDN).
 *  Preflight is omitted from the input so Tailwind coexists with
 *  Bootstrap 4 / SB-Admin-2 without resetting their base styles. */
module.exports = {
  content: ["./**/templates/**/*.html"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Montserrat", "Segoe UI", "system-ui", "sans-serif"],
      },
      colors: {
        border:     "hsl(0 0% 90%)",
        input:      "hsl(0 0% 88%)",
        ring:       "hsl(222 60% 32%)",
        background: "hsl(42 30% 92%)",
        foreground: "hsl(0 0% 4%)",
        card:    { DEFAULT: "#ffffff", foreground: "hsl(0 0% 4%)" },
        muted:   { DEFAULT: "hsl(42 18% 95%)", foreground: "hsl(0 0% 36%)" },
        primary: { DEFAULT: "hsl(222 60% 32%)", foreground: "#ffffff" },
        accent:  { DEFAULT: "hsl(222 50% 94%)", foreground: "hsl(222 60% 32%)" },
        cobalt:  { DEFAULT: "hsl(222 60% 32%)", hover: "hsl(222 60% 42%)", tint: "hsl(222 50% 94%)" },
        cream:   { DEFAULT: "hsl(42 30% 92%)", soft: "hsl(42 24% 95%)" },
        ink:     { DEFAULT: "hsl(0 0% 4%)", muted: "hsl(0 0% 36%)" },
        brand:   { navy: "hsl(213 44% 22%)", clay: "hsl(21 80% 53%)" },
      },
      borderRadius: { lg: "0.5rem", md: "0.375rem", sm: "0.25rem" },
      boxShadow: { card: "0 2px 8px rgba(0,0,0,0.06)" },
    },
  },
  plugins: [],
};
