import Link from "next/link";

const capabilities = [
  "Role-aware onboarding plans",
  "Grounded answers with cited internal sources",
  "First-week tasks tied to real team context",
  "Reusable ingestion path for docs, repositories, and decisions",
];

export default function OnboardingPage() {
  return (
    <main className="mx-auto grid max-w-6xl gap-8 px-6 py-10 lg:grid-cols-[1fr_360px]">
      <section className="rounded-lg border border-slate-200 bg-white p-8 shadow-sm">
        <p className="text-sm font-semibold uppercase tracking-wide text-cyan-700">
          Technical ramp-up copilot
        </p>
        <h1 className="mt-4 max-w-3xl text-4xl font-semibold tracking-normal text-slate-950">
          Help new engineers understand the system, the team, and the next useful step.
        </h1>
        <p className="mt-5 max-w-2xl text-base leading-7 text-slate-600">
          Knovara turns scattered engineering knowledge into focused onboarding briefings
          and cited answers. This demo shows the product flow without requiring private
          company data or an API key.
        </p>
        <div className="mt-8 flex flex-wrap gap-3">
          <Link
            className="rounded-md bg-slate-950 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800"
            href="/mentor"
          >
            Build briefing
          </Link>
          <Link
            className="rounded-md border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-800 hover:bg-slate-100"
            href="/chat"
          >
            Ask a question
          </Link>
        </div>
      </section>

      <aside className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500">
          Demo capabilities
        </h2>
        <ul className="mt-5 space-y-4">
          {capabilities.map((capability) => (
            <li className="flex gap-3 text-sm leading-6 text-slate-700" key={capability}>
              <span className="mt-2 h-2 w-2 rounded-full bg-cyan-600" />
              <span>{capability}</span>
            </li>
          ))}
        </ul>
      </aside>
    </main>
  );
}
