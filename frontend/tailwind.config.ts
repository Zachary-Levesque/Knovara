/**
 * TailwindCSS configuration.
 *
 * This file will define content scanning paths, theme extensions, design
 * tokens, and plugins for the Knovara frontend styling system.
 */
import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./lib/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
};

export default config;

