/**
 * PostCSS configuration.
 *
 * This file wires TailwindCSS and Autoprefixer into the Next.js CSS build
 * pipeline so global styles and utility classes compile consistently.
 */
const config = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
};

export default config;

