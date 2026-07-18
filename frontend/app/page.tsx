/**
 * Onboarding entry point.
 *
 * This page will collect a user's role, background, team, and onboarding goals
 * before sending that profile to the backend mentorship workflow.
 */
"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  getIndexStatus,
  getMentorBriefing,
  getProjects,
  IndexStatus,
  ingestDirectory,
  IngestResult,
  MentorRequest,
  Project,
} from "@/lib/api";
import {
  getSelectedCollection,
  getSelectedProjectId,
  setSelectedCollection,
  setSelectedProjectId,
} from "@/lib/collection";

const initialProfile: MentorRequest = {
  name: "New teammate",
  role: "Backend Engineer",
  team: "Platform",
  background: "General backend and product engineering",
  goal: "Ship a small production change with confidence",
  collection_name: "seets",
};

export default function OnboardingPage() {
  const [profile, setProfile] = useState<MentorRequest>(initialProfile);
  const [error, setError] = useState("");
  const [ingestError, setIngestError] = useState("");
  const [ingestResult, setIngestResult] = useState<IngestResult | null>(null);
  const [indexStatus, setIndexStatus] = useState<IndexStatus | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectIdState] = useState<number | null>(null);
  const [ingesting, setIngesting] = useState(false);
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  useEffect(() => {
    setProfile((current) => ({ ...current, collection_name: getSelectedCollection() }));
    getIndexStatus()
      .then(setIndexStatus)
      .catch(() => setIndexStatus(null));
    getProjects()
      .then((nextProjects) => {
        setProjects(nextProjects);
        const savedProjectId = getSelectedProjectId();
        const selected =
          nextProjects.find((project) => project.id === savedProjectId) ?? nextProjects[0];
        if (selected) {
          selectProject(selected);
        }
      })
      .catch(() => setProjects([]));
  }, []);

  async function submitProfile(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setLoading(true);

    try {
      setSelectedCollection(profile.collection_name ?? "seets");
      const briefing = await getMentorBriefing(profile);
      window.localStorage.setItem("knovara.profile", JSON.stringify(profile));
      window.localStorage.setItem("knovara.briefing", JSON.stringify(briefing));
      router.push("/mentor");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to create briefing.");
    } finally {
      setLoading(false);
    }
  }

  function selectProject(project: Project) {
    setSelectedProjectIdState(project.id);
    setSelectedProjectId(project.id);
    setSelectedCollection(project.collection_name);
    setProfile((current) => ({
      ...current,
      collection_name: project.collection_name,
      team: current.team || project.name,
    }));
  }

  function updateField(field: keyof MentorRequest, value: string) {
    setProfile((current) => ({ ...current, [field]: value }));
    if (field === "collection_name") {
      setSelectedCollection(value);
    }
  }

  async function ingestSampleData() {
    setIngestError("");
    setIngestResult(null);
    setIngesting(true);

    try {
      setIngestResult(
        await ingestDirectory({
          directory: "../example_data",
          collection_name: profile.collection_name ?? "seets",
        })
      );
      setIndexStatus(await getIndexStatus());
    } catch (err) {
      setIngestError(
        err instanceof Error
          ? err.message
          : "Unable to ingest sample data. Check backend credentials."
      );
    } finally {
      setIngesting(false);
    }
  }

  const openaiMissing = indexStatus ? !indexStatus.openai_configured : false;

  return (
    <main className="mx-auto grid min-h-screen max-w-6xl gap-8 px-6 py-8 lg:grid-cols-[360px_1fr]">
      <aside className="self-start">
        <p className="text-sm font-semibold uppercase tracking-wide text-cyan-700">Knovara</p>
        <h1 className="mt-3 text-4xl font-semibold leading-tight text-slate-950">
          Day-one ramp-up for technical teams
        </h1>
        <p className="mt-4 leading-7 text-slate-600">
          Turn a role, team, background, and goal into a focused first-week briefing.
        </p>
        <div className="mt-8 rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500">
            Demo scope
          </h2>
          <ul className="mt-4 space-y-3 text-sm leading-6 text-slate-700">
            <li>Personalized onboarding summary</li>
            <li>First-week learning path</li>
            <li>Recommended docs and people</li>
            <li>Grounded engineering Q&A</li>
          </ul>
        </div>
        <div className="mt-4 rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500">
            Knowledge index
          </h2>
          <button
            className="mt-4 min-h-11 w-full rounded-md border border-slate-300 bg-white px-4 text-sm font-semibold text-slate-950 disabled:cursor-not-allowed disabled:bg-slate-100"
            disabled={ingesting || openaiMissing}
            onClick={ingestSampleData}
            type="button"
          >
            {ingesting ? "Indexing..." : "Index sample data"}
          </button>
          {openaiMissing ? (
            <p className="mt-3 text-sm leading-6 text-amber-800">
              Add OPENAI_API_KEY in backend/.env before indexing sample data.
            </p>
          ) : null}
          {ingestResult ? (
            <p className="mt-3 text-sm leading-6 text-slate-600">
              Indexed {ingestResult.files_processed} files into {ingestResult.collection_name}.
            </p>
          ) : null}
          {ingestError ? <p className="mt-3 text-sm leading-6 text-red-700">{ingestError}</p> : null}
        </div>
      </aside>

      <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-2xl font-semibold text-slate-950">Create onboarding profile</h2>
        <form className="mt-6 grid gap-5" onSubmit={submitProfile}>
          <label className="grid gap-2 text-sm font-medium text-slate-700">
            Name
            <input
              className="min-h-11 rounded-md border border-slate-300 px-3 py-2 outline-none focus:border-cyan-600 focus:ring-2 focus:ring-cyan-100"
              maxLength={80}
              onChange={(event) => updateField("name", event.target.value)}
              required
              value={profile.name}
            />
          </label>
          <div className="grid gap-5 md:grid-cols-2">
            <label className="grid gap-2 text-sm font-medium text-slate-700">
              Role
              <input
                className="min-h-11 rounded-md border border-slate-300 px-3 py-2 outline-none focus:border-cyan-600 focus:ring-2 focus:ring-cyan-100"
                maxLength={80}
                onChange={(event) => updateField("role", event.target.value)}
                required
                value={profile.role}
              />
            </label>
            <label className="grid gap-2 text-sm font-medium text-slate-700">
              Team
              <input
                className="min-h-11 rounded-md border border-slate-300 px-3 py-2 outline-none focus:border-cyan-600 focus:ring-2 focus:ring-cyan-100"
                maxLength={80}
                onChange={(event) => updateField("team", event.target.value)}
                required
                value={profile.team}
              />
            </label>
          </div>
          <label className="grid gap-2 text-sm font-medium text-slate-700">
            Background
            <textarea
              className="min-h-28 rounded-md border border-slate-300 px-3 py-2 outline-none focus:border-cyan-600 focus:ring-2 focus:ring-cyan-100"
              maxLength={240}
              onChange={(event) => updateField("background", event.target.value)}
              required
              value={profile.background}
            />
          </label>
          <label className="grid gap-2 text-sm font-medium text-slate-700">
            Goal
            <textarea
              className="min-h-28 rounded-md border border-slate-300 px-3 py-2 outline-none focus:border-cyan-600 focus:ring-2 focus:ring-cyan-100"
              maxLength={240}
              onChange={(event) => updateField("goal", event.target.value)}
              required
              value={profile.goal}
            />
          </label>
          <label className="grid gap-2 text-sm font-medium text-slate-700">
            Project
            {projects.length ? (
              <select
                className="min-h-11 rounded-md border border-slate-300 px-3 py-2 outline-none focus:border-cyan-600 focus:ring-2 focus:ring-cyan-100"
                onChange={(event) => {
                  const project = projects.find((item) => item.id === Number(event.target.value));
                  if (project) {
                    selectProject(project);
                  }
                }}
                value={selectedProjectId ?? ""}
              >
                {projects.map((project) => (
                  <option key={project.id} value={project.id}>
                    {project.name} / {project.collection_name}
                  </option>
                ))}
              </select>
            ) : (
              <input
                className="min-h-11 rounded-md border border-slate-300 px-3 py-2 outline-none focus:border-cyan-600 focus:ring-2 focus:ring-cyan-100"
                maxLength={80}
                onChange={(event) => updateField("collection_name", event.target.value)}
                required
                value={profile.collection_name ?? "seets"}
              />
            )}
          </label>
          {error ? <p className="text-sm text-red-700">{error}</p> : null}
          <button
            className="min-h-11 rounded-md bg-slate-950 px-5 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:bg-slate-400"
            disabled={loading}
            type="submit"
          >
            {loading ? "Creating briefing..." : "Create briefing"}
          </button>
        </form>
      </section>
    </main>
  );
}
