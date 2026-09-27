import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/features/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "var(--md-sys-color-background)",
        foreground: "var(--md-sys-color-on-background)",
        surface: {
          DEFAULT: "var(--md-sys-color-surface)",
          dim: "var(--md-sys-color-surface-dim)",
          bright: "var(--md-sys-color-surface-bright)",
          container: {
            lowest: "var(--md-sys-color-surface-container-lowest)",
            low: "var(--md-sys-color-surface-container-low)",
            DEFAULT: "var(--md-sys-color-surface-container)",
            high: "var(--md-sys-color-surface-container-high)",
            highest: "var(--md-sys-color-surface-container-highest)",
          },
        },
        primary: {
          DEFAULT: "var(--md-sys-color-primary)",
          foreground: "var(--md-sys-color-on-primary)",
          container: "var(--md-sys-color-primary-container)",
          onContainer: "var(--md-sys-color-on-primary-container)",
        },
        secondary: {
          DEFAULT: "var(--md-sys-color-secondary)",
          foreground: "var(--md-sys-color-on-secondary)",
          container: "var(--md-sys-color-secondary-container)",
          onContainer: "var(--md-sys-color-on-secondary-container)",
        },
        tertiary: {
          DEFAULT: "var(--md-sys-color-tertiary)",
          foreground: "var(--md-sys-color-on-tertiary)",
          container: "var(--md-sys-color-tertiary-container)",
          onContainer: "var(--md-sys-color-on-tertiary-container)",
        },
        error: {
          DEFAULT: "var(--md-sys-color-error)",
          foreground: "var(--md-sys-color-on-error)",
          container: "var(--md-sys-color-error-container)",
          onContainer: "var(--md-sys-color-on-error-container)",
        },
        outline: {
          DEFAULT: "var(--md-sys-color-outline)",
          variant: "var(--md-sys-color-outline-variant)",
        },
      },
      borderRadius: {
        xs: "4px",
        sm: "8px",
        md: "12px",
        lg: "16px",
        xl: "28px",
        full: "9999px",
      },
      boxShadow: {
        "elevation-1": "0px 1px 3px 1px rgba(0, 0, 0, 0.15), 0px 1px 2px 0px rgba(0, 0, 0, 0.30)",
        "elevation-2": "0px 2px 6px 2px rgba(0, 0, 0, 0.15), 0px 1px 2px 0px rgba(0, 0, 0, 0.30)",
        "elevation-3": "0px 1px 3px 0px rgba(0, 0, 0, 0.30), 0px 4px 8px 3px rgba(0, 0, 0, 0.15)",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
};

export default config;
