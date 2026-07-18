"use client";

import { FormEvent, useEffect, useState } from "react";
import {
  clearCollection,
  getIndexStatus,
  IndexStatus,
  ingestDirectory,
  IngestResult,
} from "@/lib/api";

export default function KnowledgePage() {
  const [directory, setDirectory] = useState("../example_data");
  const [collectionName, setCollectionName] = useState("seets");
  const [status, setStatus] = useState<IndexStatus | null>(null);
  const [result, setResult] = useState<IngestResult | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    refreshStatus();
  }, []);

  async function refreshStatus() {
    try {
      setStatus(await getIndexStatus());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load index status.");
    }
  }

  async function submitIngest(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setResult(null);
    setLoading(true);

    try {
      const nextResult = await ingestDirectory({
        directory,
        collection_name: collectionName,
      });
      setResult(nextResult);
      await refreshStatus();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to ingest directory.");
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
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to clear collection.");
    } finally {
      setLoading(false);
    }
  }

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
          <h2 className="text-xl font-semibold text-slate-950">Ingest directory</h2>
          <form className="mt-5 grid gap-4" onSubmit={submitIngest}>
            <label className="grid gap-2 text-sm font-medium text-slate-700">
              Directory
              <input
                className="min-h-11 rounded-md border border-slate-300 px-3 py-2 outline-none focus:border-cyan-600 focus:ring-2 focus:ring-cyan-100"
                onChange={(event) => setDirectory(event.target.value)}
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
            <button
              className="min-h-11 rounded-md bg-slate-950 px-5 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:bg-slate-400"
              disabled={loading}
              type="submit"
            >
              {loading ? "Working..." : "Index directory"}
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
    </main>
  );
}
