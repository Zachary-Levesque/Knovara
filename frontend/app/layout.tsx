/**
 * Root application layout.
 *
 * This file will define shared HTML structure, metadata, global styling, and
 * persistent layout elements used across all Knovara frontend routes.
 */
import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Knovara",
  description: "AI-powered technical ramp-up copilot.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}

