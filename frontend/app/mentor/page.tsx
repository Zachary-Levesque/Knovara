/**
 * Personalized mentor briefing page.
 *
 * This page will display the user's day-one briefing, prioritized learning
 * path, suggested documents, recommended experts, and next onboarding actions.
 */
"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { getMentorBriefing, MentorBriefing, MentorRequest } from "@/lib/api";

export default function MentorPage() {
  const [briefing, setBriefing] = useState<MentorBriefing | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    const savedBriefing = window.localStorage.getItem("knovara.briefing");
    if (savedBriefing) {
      try {
        setBriefing(JSON.parse(savedBriefing) as MentorBriefing);
        return;
      } catch {
        window.localStorage.removeItem("knovara.briefing");
      }
    }

    const savedProfile = window.localStorage.getItem("knovara.profile");
    if (!savedProfile) {
      return;
    }

    let profile: MentorRequest;
    try {
      profile = JSON.parse(savedProfile) as MentorRequest;
    } catch {
      window.localStorage.removeItem("knovara.profile");
      return;
    }

    getMentorBriefing(profile)
      .then((nextBriefing) => {
        window.localStorage.setItem("knovara.briefing", JSON.stringify(nextBriefing));
        setBriefing(nextBriefing);
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : "Unable to load briefing.");
      });
  }, []);

  if (!briefing) {
    return (
      <main className="mx-auto max-w-4xl px-6 py-8">
        <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
          <h1 className="text-2xl font-semibold text-slate-950">Mentor briefing</h1>
          <p className="mt-3 text-slate-600">
            {error || "Create an onboarding profile to generate a mentor briefing."}
          </p>
          <Link
            className="mt-5 inline-flex min-h-11 items-center rounded-md bg-slate-950 px-5 text-sm font-semibold text-white"
            href="/"
          >
            Create profile
          </Link>
        </section>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-6xl px-6 py-8">
      <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
        <div>
          <p className="text-sm font-semibold uppercase tracking-wide text-cyan-700">Mentor</p>
          <h1 className="mt-2 text-3xl font-semibold text-slate-950">{briefing.headline}</h1>
          <p className="mt-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
            {briefing.mode} / {briefing.collection_name}
          </p>
          <p className="mt-3 max-w-3xl leading-7 text-slate-600">{briefing.summary}</p>
        </div>
        <Link
          className="inline-flex min-h-11 items-center justify-center rounded-md border border-slate-300 bg-white px-5 text-sm font-semibold text-slate-950"
          href="/chat"
        >
          Ask a question
        </Link>
      </div>

      <section className="mt-8 grid gap-6 lg:grid-cols-[1fr_320px]">
        <article className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500">
            First week
          </h2>
          <div className="mt-5 grid gap-4">
            {briefing.first_week.map((item) => (
              <div className="rounded-md bg-slate-50 p-4" key={item.title}>
                <div className="flex flex-col gap-1 md:flex-row md:items-baseline md:justify-between">
                  <h3 className="font-semibold text-slate-950">{item.title}</h3>
                  <p className="text-sm text-cyan-700">{item.owner}</p>
                </div>
                <p className="mt-2 leading-6 text-slate-600">{item.detail}</p>
              </div>
            ))}
          </div>
        </article>

        <aside className="grid gap-6">
          <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
            <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500">
              Sources
            </h2>
            <ul className="mt-4 space-y-3 text-sm text-slate-700">
              {briefing.recommended_sources.map((source) => (
                <li key={source}>{source}</li>
              ))}
            </ul>
          </section>
          <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
            <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500">
              People
            </h2>
            <ul className="mt-4 space-y-3 text-sm text-slate-700">
              {briefing.people_to_meet.map((person) => (
                <li key={person}>{person}</li>
              ))}
            </ul>
          </section>
        </aside>
      </section>
    </main>
  );
}
