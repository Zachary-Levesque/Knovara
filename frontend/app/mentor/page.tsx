"use client";

import { FormEvent, useState } from "react";
import { getMentorBriefing, MentorBriefing, MentorRequest } from "@/lib/api";

const defaultProfile: MentorRequest = {
  name: "Zach",
  role: "Backend Engineer",
  team: "Platform",
  background: "Python, APIs, data pipelines, and product engineering",
  goal: "Ship a meaningful first contribution during week one",
};

export default function MentorPage() {
  const [profile, setProfile] = useState(defaultProfile);
  const [briefing, setBriefing] = useState<MentorBriefing | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function submitProfile(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError("");

    try {
      setBriefing(await getMentorBriefing(profile));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to build briefing.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="mx-auto grid max-w-6xl gap-6 px-6 py-8 lg:grid-cols-[380px_1fr]">
      <form className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm" onSubmit={submitProfile}>
        <h1 className="text-xl font-semibold text-slate-950">Mentor briefing</h1>
        <div className="mt-5 space-y-4">
          {Object.entries(profile).map(([key, value]) => (
            <label className="block text-sm font-medium capitalize text-slate-700" key={key}>
              {key.replace("_", " ")}
              <textarea
                className="mt-2 min-h-11 w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900 outline-none focus:border-cyan-600 focus:ring-2 focus:ring-cyan-100"
                rows={key === "goal" || key === "background" ? 3 : 1}
                value={value}
                onChange={(event) => setProfile({ ...profile, [key]: event.target.value })}
              />
            </label>
          ))}
        </div>
        <button
          className="mt-5 w-full rounded-md bg-slate-950 px-4 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:bg-slate-400"
          disabled={loading}
          type="submit"
        >
          {loading ? "Building..." : "Build briefing"}
        </button>
        {error ? <p className="mt-3 text-sm text-red-700">{error}</p> : null}
      </form>

      <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        {briefing ? (
          <>
            <p className="text-sm font-semibold uppercase tracking-wide text-cyan-700">Personalized plan</p>
            <h2 className="mt-3 text-2xl font-semibold text-slate-950">{briefing.headline}</h2>
            <p className="mt-3 text-sm leading-6 text-slate-600">{briefing.summary}</p>
            <div className="mt-6 grid gap-4 md:grid-cols-3">
              {briefing.first_week.map((item) => (
                <article className="rounded-lg border border-slate-200 p-4" key={item.title}>
                  <h3 className="font-semibold text-slate-950">{item.title}</h3>
                  <p className="mt-2 text-sm leading-6 text-slate-600">{item.detail}</p>
                  <p className="mt-3 text-xs font-semibold uppercase tracking-wide text-slate-500">{item.owner}</p>
                </article>
              ))}
            </div>
            <div className="mt-6 grid gap-5 md:grid-cols-2">
              <List title="Recommended sources" items={briefing.recommended_sources} />
              <List title="People to meet" items={briefing.people_to_meet} />
            </div>
          </>
        ) : (
          <div className="flex h-full min-h-96 items-center justify-center rounded-lg border border-dashed border-slate-300 text-center">
            <p className="max-w-sm text-sm leading-6 text-slate-500">
              Submit the profile to generate a first-week onboarding plan.
            </p>
          </div>
        )}
      </section>
    </main>
  );
}

function List({ title, items }: { title: string; items: string[] }) {
  return (
    <div>
      <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-500">{title}</h3>
      <ul className="mt-3 space-y-2 text-sm text-slate-700">
        {items.map((item) => (
          <li className="rounded-md bg-slate-50 px-3 py-2" key={item}>
            {item}
          </li>
        ))}
      </ul>
    </div>
  );
}
