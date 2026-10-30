import type { Config } from "tailwindcss";

const hsl = (v: string) => `hsl(var(--${v}) / <alpha-value>)`;

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        background: hsl("background"),
        foreground: hsl("foreground"),
        card: hsl("card"),
        border: hsl("border"),
        muted: hsl("muted"),
        "muted-foreground": hsl("muted-foreground"),
        primary: hsl("primary"),
        "primary-foreground": hsl("primary-foreground"),
        ring: hsl("ring"),
        danger: hsl("danger"),
        ok: hsl("ok"),
        warn: hsl("warn"),
      },
      fontFamily: {
        sans: ['"Segoe UI Variable Text"', '"Segoe UI"', "system-ui", "-apple-system", "sans-serif"],
        mono: ['"Cascadia Code"', '"SF Mono"', "ui-monospace", "Menlo", "Consolas", "monospace"],
      },
      borderRadius: { lg: "0.5rem", md: "0.375rem", sm: "0.25rem" },
    },
  },
  plugins: [],
};
export default config;
