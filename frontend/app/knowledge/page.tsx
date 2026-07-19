"use client";

import { FormEvent, useEffect, useState } from "react";
import {
  clearCollection,
  CollectionDetail,
  createProject,
  deleteProject,
  getIndexStatus,
  getCollectionDetail,
  getProjectOverview,
  getProjects,
  IndexStatus,
  ingestProject,
  IngestResult,
  Project,
  ProjectOverview,
  updateProject,
} from "@/lib/api";
import {
  getSelectedCollection,
  getSelectedProjectId,
  setSelectedCollection,
  setSelectedProjectId,
} from "@/lib/collection";

export default function KnowledgePage() {
  const [projectName, setProjectName] = useState("Seets Sensor Mesh");
  const [directory, setDirectory] = useState("../example_data");
  const [sourceType, setSourceType] = useState<"local" | "github">("local");
  const [collectionName, setCollectionName] = useState("seets");
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  const [status, setStatus] = useState<IndexStatus | null>(null);
  const [detail, setDetail] = useState<CollectionDetail | null>(null);
  const [overview, setOverview] = useState<ProjectOverview | null>(null);
  const [result, setResult] = useState<IngestResult | null>(null);
  const [editingProjectId, setEditingProjectId] = useState<number | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setCollectionName(getSelectedCollection());
    refreshAll();
  }, []);

  async function refreshAll() {
    await Promise.all([refreshStatus(), refreshProjects()]);
  }

  async function refreshProjects() {
    try {
      const nextProjects = await getProjects();
      setProjects(nextProjects);
      const savedProjectId = getSelectedProjectId();
      const nextSelected =
        nextProjects.find((project) => project.id === savedProjectId) ?? nextProjects[0] ?? null;
      setSelectedProject(nextSelected);
      if (nextSelected) {
        applyProject(nextSelected);
        await loadOverview(nextSelected.id);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load projects.");
    }
  }

  async function refreshStatus() {
    try {
      const nextStatus = await getIndexStatus();
      setStatus(nextStatus);
      const selected = getSelectedCollection();
      if (nextStatus.collections.some((collection) => collection.name === selected)) {
        setCollectionName(selected);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load index status.");
    }
  }

  async function submitProject(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setResult(null);
    setLoading(true);

    try {
      const payload = {
        name: projectName,
        source_path: directory,
        source_type: sourceType,
        repository_url: sourceType === "github" ? directory : null,
        collection_name: collectionName,
      };
      const project =
        editingProjectId === null
          ? await createProject(payload)
          : await updateProject(editingProjectId, payload);

      selectProject(project);
      setEditingProjectId(null);
      setDetail((current) => (current?.name === project.collection_name ? current : null));
      await refreshProjects();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to save project.");
    } finally {
      setLoading(false);
    }
  }

  async function ingestSelectedProject(project: Project) {
    setError("");
    setResult(null);
    setLoading(true);

    try {
      const nextResult = await ingestProject(project.id);
      setResult(nextResult);
      selectProject(project);
      await refreshAll();
      await preview(project.collection_name);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to ingest project.");
      await refreshProjects();
    } finally {
      setLoading(false);
    }
  }

  async function clear(name: string) {
    setError("");
    setLoading(true);

    try {
      setStatus(await clearCollection(name));
      setResult(null);
      setDetail((current) => (current?.name === name ? null : current));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to clear collection.");
    } finally {
      setLoading(false);
    }
  }

  async function preview(name: string) {
    setError("");
    setSelectedCollection(name);
    setCollectionName(name);

    try {
      setDetail(await getCollectionDetail(name));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load collection preview.");
    }
  }

  async function removeProject(project: Project) {
    setError("");
    setLoading(true);

    try {
      await deleteProject(project.id);
      if (selectedProject?.id === project.id) {
        setSelectedProjectId(null);
        setSelectedProject(null);
        setOverview(null);
      }
      if (editingProjectId === project.id) {
        clearProjectForm();
      }
      await refreshProjects();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to delete project.");
    } finally {
      setLoading(false);
    }
  }

  function selectProject(project: Project) {
    setSelectedProject(project);
    setSelectedProjectId(project.id);
    applyProject(project);
    loadOverview(project.id);
  }

  function editProject(project: Project) {
    setEditingProjectId(project.id);
    selectProject(project);
    setError("");
    setResult(null);
  }

  function clearProjectForm() {
    setEditingProjectId(null);
    if (selectedProject) {
      applyProject(selectedProject);
      return;
    }

    setProjectName("Seets Sensor Mesh");
    setDirectory("../example_data");
    setSourceType("local");
    setCollectionName(getSelectedCollection());
  }

  function applyProject(project: Project) {
    setProjectName(project.name);
    setDirectory(project.source_path);
    setSourceType(project.source_type);
    setCollectionName(project.collection_name);
    setSelectedCollection(project.collection_name);
  }

  async function loadOverview(projectId: number) {
    setError("");

    try {
      setOverview(await getProjectOverview(projectId));
    } catch (err) {
      setOverview(null);
      setError(err instanceof Error ? err.message : "Unable to load project overview.");
    }
  }

  const openaiMissing = status ? !status.openai_configured : false;

  return (
    <main className="mx-auto max-w-6xl px-6 py-8">
      <div className="grid gap-6 lg:grid-cols-[380px_1fr]">
        <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
          <p className="text-sm font-semibold uppercase tracking-wide text-cyan-700">Index</p>
          <h1 className="mt-2 text-3xl font-semibold text-slate-950">Knowledge collections</h1>
          <p className="mt-3 leading-7 text-slate-600">
            Ingest local project material into Chroma, then use a named collection in mentor
            briefings and chat answers.
          </p>
          <div className="mt-5 rounded-md bg-slate-50 p-4 text-sm leading-6 text-slate-700">
            <p>OpenAI configured: {status?.openai_configured ? "yes" : "no"}</p>
            <p>Default collection: {status?.default_collection ?? "seets"}</p>
            <p>Persist dir: {status?.persist_dir ?? "./.chroma"}</p>
          </div>
        </section>

        <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <h2 className="text-xl font-semibold text-slate-950">
              {editingProjectId === null ? "Create project" : "Edit project"}
            </h2>
            {editingProjectId !== null ? (
              <button
                className="min-h-10 rounded-md border border-slate-300 bg-white px-4 text-sm font-semibold text-slate-950"
                disabled={loading}
                onClick={clearProjectForm}
                type="button"
              >
                Cancel
              </button>
            ) : null}
          </div>
          <form className="mt-5 grid gap-4" onSubmit={submitProject}>
            <label className="grid gap-2 text-sm font-medium text-slate-700">
              Project name
              <input
                className="min-h-11 rounded-md border border-slate-300 px-3 py-2 outline-none focus:border-cyan-600 focus:ring-2 focus:ring-cyan-100"
                onChange={(event) => setProjectName(event.target.value)}
                value={projectName}
              />
            </label>
            <label className="grid gap-2 text-sm font-medium text-slate-700">
              Source
              <select
                className="min-h-11 rounded-md border border-slate-300 px-3 py-2 outline-none focus:border-cyan-600 focus:ring-2 focus:ring-cyan-100"
                onChange={(event) => {
                  const nextType = event.target.value as "local" | "github";
                  setSourceType(nextType);
                  setDirectory(nextType === "local" ? "../example_data" : "https://github.com/");
                }}
                value={sourceType}
              >
                <option value="local">Local directory</option>
                <option value="github">GitHub repository</option>
              </select>
            </label>
            <label className="grid gap-2 text-sm font-medium text-slate-700">
              {sourceType === "github" ? "GitHub repository URL" : "Directory"}
              <input
                className="min-h-11 rounded-md border border-slate-300 px-3 py-2 outline-none focus:border-cyan-600 focus:ring-2 focus:ring-cyan-100"
                onChange={(event) => setDirectory(event.target.value)}
                placeholder={sourceType === "github" ? "https://github.com/owner/repo" : "../example_data"}
                value={directory}
              />
            </label>
            <label className="grid gap-2 text-sm font-medium text-slate-700">
              Collection
              <input
                className="min-h-11 rounded-md border border-slate-300 px-3 py-2 outline-none focus:border-cyan-600 focus:ring-2 focus:ring-cyan-100"
                onChange={(event) => setCollectionName(event.target.value)}
                value={collectionName}
              />
            </label>
            {openaiMissing ? (
              <p className="rounded-md bg-amber-50 p-3 text-sm leading-6 text-amber-800">
                Add OPENAI_API_KEY to backend/.env and restart the backend before indexing.
              </p>
            ) : null}
            <button
              className="min-h-11 rounded-md bg-slate-950 px-5 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:bg-slate-400"
              disabled={loading}
              type="submit"
            >
              {loading
                ? "Working..."
                : editingProjectId === null
                  ? "Create project"
                  : "Save project"}
            </button>
          </form>
          {result ? (
            <p className="mt-4 text-sm leading-6 text-slate-700">
              Indexed {result.files_processed} files and {result.chunks_created} chunks into{" "}
              {result.collection_name}.
            </p>
          ) : null}
          {error ? <p className="mt-4 text-sm leading-6 text-red-700">{error}</p> : null}
        </section>
      </div>

      <section className="mt-6 rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <h2 className="text-xl font-semibold text-slate-950">Projects</h2>
          <button
            className="min-h-10 rounded-md border border-slate-300 bg-white px-4 text-sm font-semibold text-slate-950"
            onClick={refreshAll}
            type="button"
          >
            Refresh
          </button>
        </div>
        <div className="mt-5 grid gap-4">
          {projects.length ? (
            projects.map((project) => (
              <article
                className={`rounded-md p-4 ${
                  selectedProject?.id === project.id ? "bg-cyan-50" : "bg-slate-50"
                }`}
                key={project.id}
              >
                <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                  <div>
                    <h3 className="font-semibold text-slate-950">{project.name}</h3>
                    <p className="mt-1 break-all text-sm text-slate-600">{project.source_path}</p>
                    <p className="mt-1 text-sm text-slate-600">
                      {project.source_type} / {project.collection_name} / {project.ingest_status}
                    </p>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <button
                      className="min-h-10 rounded-md border border-slate-300 bg-white px-4 text-sm font-semibold text-slate-950"
                      onClick={() => selectProject(project)}
                      type="button"
                    >
                      Select
                    </button>
                    <button
                      className="min-h-10 rounded-md border border-slate-300 bg-white px-4 text-sm font-semibold text-slate-950"
                      onClick={() => selectProject(project)}
                      type="button"
                    >
                      Overview
                    </button>
                    <button
                      className="min-h-10 rounded-md border border-slate-300 bg-white px-4 text-sm font-semibold text-slate-950 disabled:cursor-not-allowed disabled:bg-slate-100"
                      disabled={loading || openaiMissing}
                      onClick={() => ingestSelectedProject(project)}
                      type="button"
                    >
                      Ingest
                    </button>
                    <button
                      className="min-h-10 rounded-md border border-slate-300 bg-white px-4 text-sm font-semibold text-slate-950"
                      onClick={() => editProject(project)}
                      type="button"
                    >
                      Edit
                    </button>
                    <button
                      className="min-h-10 rounded-md border border-slate-300 bg-white px-4 text-sm font-semibold text-slate-950"
                      onClick={() => preview(project.collection_name)}
                      type="button"
                    >
                      Preview
                    </button>
                    <button
                      className="min-h-10 rounded-md border border-red-200 bg-white px-4 text-sm font-semibold text-red-700 disabled:cursor-not-allowed disabled:bg-slate-100"
                      disabled={loading}
                      onClick={() => removeProject(project)}
                      type="button"
                    >
                      Delete
                    </button>
                  </div>
                </div>
              </article>
            ))
          ) : (
            <p className="text-sm text-slate-600">No projects found yet.</p>
          )}
        </div>
      </section>

      {overview ? (
        <section className="mt-6 rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex flex-col gap-2 md:flex-row md:items-baseline md:justify-between">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-cyan-700">
                Project overview
              </p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">
                {overview.project_name}
              </h2>
            </div>
            <p className="text-sm text-slate-500">{overview.source_count} source files analyzed</p>
          </div>
          <p className="mt-4 max-w-4xl leading-7 text-slate-700">{overview.summary}</p>

          <div className="mt-6 grid gap-5 lg:grid-cols-3">
            <OverviewList title="Technologies" items={overview.technologies} />
            <OverviewList title="Topics" items={overview.topics} />
            <OverviewList title="Components" items={overview.components} />
          </div>

          <div className="mt-5 grid gap-5 lg:grid-cols-2">
            <OverviewList
              title="Repository structure"
              items={overview.repository_structure.top_level_directories}
            />
            <OverviewList title="Entry points" items={overview.repository_structure.entry_points} />
            <OverviewList title="Key files" items={overview.repository_structure.key_files} />
            <OverviewList title="Tests" items={overview.repository_structure.test_files} />
            <OverviewList title="Ownership and experts" items={overview.ownership} />
            <OverviewList title="Decision context" items={overview.decisions} />
            <OverviewList title="Learning path" items={overview.learning_path} />
            <OverviewList title="Starter questions" items={overview.starter_questions} />
          </div>
        </section>
      ) : null}

      <section className="mt-6 rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <h2 className="text-xl font-semibold text-slate-950">Collections</h2>
          <button
            className="min-h-10 rounded-md border border-slate-300 bg-white px-4 text-sm font-semibold text-slate-950"
            onClick={refreshStatus}
            type="button"
          >
            Refresh
          </button>
        </div>
        <div className="mt-5 grid gap-4">
          {status?.collections.length ? (
            status.collections.map((collection) => (
              <article className="rounded-md bg-slate-50 p-4" key={collection.name}>
                <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                  <div>
                    <h3 className="font-semibold text-slate-950">{collection.name}</h3>
                    <p className="mt-1 text-sm text-slate-600">{collection.count} chunks indexed</p>
                  </div>
                  <button
                    className="min-h-10 rounded-md border border-slate-300 bg-white px-4 text-sm font-semibold text-slate-950"
                    disabled={loading}
                    onClick={() => preview(collection.name)}
                    type="button"
                  >
                    Preview
                  </button>
                  <button
                    className="min-h-10 rounded-md border border-red-200 bg-white px-4 text-sm font-semibold text-red-700 disabled:cursor-not-allowed disabled:bg-slate-100"
                    disabled={loading}
                    onClick={() => clear(collection.name)}
                    type="button"
                  >
                    Clear
                  </button>
                </div>
                {collection.sample_sources.length ? (
                  <ul className="mt-4 space-y-2 text-sm text-slate-600">
                    {collection.sample_sources.map((source) => (
                      <li className="break-all" key={source}>
                        {source}
                      </li>
                    ))}
                  </ul>
                ) : null}
              </article>
            ))
          ) : (
            <p className="text-sm text-slate-600">No Chroma collections found yet.</p>
          )}
        </div>
      </section>

      {detail ? (
        <section className="mt-6 rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex flex-col gap-2 md:flex-row md:items-baseline md:justify-between">
            <h2 className="text-xl font-semibold text-slate-950">{detail.name} preview</h2>
            <p className="text-sm text-slate-500">{detail.count} chunks indexed</p>
          </div>
          <div className="mt-5 grid gap-4">
            {detail.chunks.length ? (
              detail.chunks.map((chunk) => (
                <article className="rounded-md bg-slate-50 p-4" key={`${chunk.source}-${chunk.chunk_index}`}>
                  <div className="flex flex-col gap-1 md:flex-row md:items-baseline md:justify-between">
                    <h3 className="font-semibold text-slate-950">{chunk.title}</h3>
                    <p className="text-xs text-slate-500">Chunk {chunk.chunk_index ?? "n/a"}</p>
                  </div>
                  <p className="mt-1 break-all text-xs text-slate-500">{chunk.source}</p>
                  <p className="mt-3 text-sm leading-6 text-slate-700">{chunk.content}</p>
                </article>
              ))
            ) : (
              <p className="text-sm text-slate-600">No preview chunks are available.</p>
            )}
          </div>
        </section>
      ) : null}
    </main>
  );
}

function OverviewList({ title, items }: { title: string; items: string[] }) {
  return (
    <section className="rounded-md bg-slate-50 p-4">
      <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-500">{title}</h3>
      <ul className="mt-3 space-y-2 text-sm leading-6 text-slate-700">
        {items.length ? (
          items.map((item) => <li key={item}>{item}</li>)
        ) : (
          <li>None detected yet.</li>
        )}
      </ul>
    </section>
  );
}
