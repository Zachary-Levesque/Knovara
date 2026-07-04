import type { Metadata } from "next";
import Link from "next/link";
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
      <body>
        <header className="border-b border-slate-200 bg-white">
          <nav className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
            <Link className="text-lg font-semibold text-slate-950" href="/">
              Knovara
            </Link>
            <div className="flex items-center gap-2 text-sm font-medium text-slate-600">
              <Link className="rounded-md px-3 py-2 hover:bg-slate-100" href="/mentor">
                Mentor
              </Link>
              <Link className="rounded-md px-3 py-2 hover:bg-slate-100" href="/chat">
                Chat
              </Link>
            </div>
          </nav>
        </header>
        {children}
      </body>
    </html>
  );
}
