"use client";

import { FormEvent, useEffect, useState } from "react";
import { askQuestion, ChatResponse, getIndexStatus, IndexStatus } from "@/lib/api";

export default function ChatPage() {
  const [question, setQuestion] = useState("What should I read before making my first backend change?");
  const [collectionName, setCollectionName] = useState("seets");
  const [status, setStatus] = useState<IndexStatus | null>(null);
  const [response, setResponse] = useState<ChatResponse | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    getIndexStatus()
      .then((nextStatus) => {
        setStatus(nextStatus);
        setCollectionName(nextStatus.default_collection);
      })
      .catch(() => {
        setStatus(null);
      });
  }, []);

  async function submitQuestion(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError("");

    try {
      setResponse(
        await askQuestion({
          question,
          role: "Backend Engineer",
          team: "Platform",
          collection_name: collectionName,
        })
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to answer question.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="mx-auto max-w-5xl px-6 py-8">
      <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <h1 className="text-2xl font-semibold text-slate-950">Grounded engineering Q&A</h1>
        <form className="mt-5 grid gap-3" onSubmit={submitQuestion}>
          <div className="grid gap-3 md:grid-cols-[1fr_220px]">
          <input
            className="min-h-11 flex-1 rounded-md border border-slate-300 px-3 py-2 text-sm outline-none focus:border-cyan-600 focus:ring-2 focus:ring-cyan-100"
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
          />
            {status?.collections.length ? (
              <select
                className="min-h-11 rounded-md border border-slate-300 px-3 py-2 text-sm outline-none focus:border-cyan-600 focus:ring-2 focus:ring-cyan-100"
                onChange={(event) => setCollectionName(event.target.value)}
                value={collectionName}
              >
                {status.collections.map((collection) => (
                  <option key={collection.name} value={collection.name}>
                    {collection.name}
                  </option>
                ))}
              </select>
            ) : (
              <input
                className="min-h-11 rounded-md border border-slate-300 px-3 py-2 text-sm outline-none focus:border-cyan-600 focus:ring-2 focus:ring-cyan-100"
                onChange={(event) => setCollectionName(event.target.value)}
                value={collectionName}
              />
            )}
          </div>
          <button
            className="min-h-11 rounded-md bg-slate-950 px-5 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:bg-slate-400"
            disabled={loading}
            type="submit"
          >
            {loading ? "Asking..." : "Ask"}
          </button>
        </form>
        {error ? <p className="mt-3 text-sm text-red-700">{error}</p> : null}
      </section>

      {response ? (
        <section className="mt-6 grid gap-6 lg:grid-cols-[1fr_320px]">
          <article className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
            <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
              <h2 className="text-sm font-semibold uppercase tracking-wide text-cyan-700">Answer</h2>
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                {response.mode} / {response.collection_name}
              </p>
            </div>
            <p className="mt-3 leading-7 text-slate-700">{response.answer}</p>
          </article>
          <aside className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
            <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500">Citations</h2>
            <div className="mt-4 space-y-4">
              {response.citations.map((citation) => (
                <div className="rounded-md bg-slate-50 p-3" key={citation.source}>
                  <p className="font-semibold text-slate-950">{citation.title}</p>
                  <p className="text-xs text-slate-500">{citation.source}</p>
                  {citation.score !== null && citation.score !== undefined ? (
                    <p className="mt-1 text-xs text-slate-500">
                      Distance score: {citation.score.toFixed(4)}
                    </p>
                  ) : null}
                  <p className="mt-2 text-sm leading-5 text-slate-600">{citation.relevance}</p>
                </div>
              ))}
            </div>
          </aside>
        </section>
      ) : null}
    </main>
  );
}
