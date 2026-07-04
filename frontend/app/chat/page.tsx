"use client";

import { FormEvent, useState } from "react";
import { askQuestion, ChatResponse } from "@/lib/api";

export default function ChatPage() {
  const [question, setQuestion] = useState("What should I read before making my first backend change?");
  const [response, setResponse] = useState<ChatResponse | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function submitQuestion(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError("");

    try {
      setResponse(await askQuestion({ question, role: "Backend Engineer", team: "Platform" }));
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
        <form className="mt-5 flex flex-col gap-3 md:flex-row" onSubmit={submitQuestion}>
          <input
            className="min-h-11 flex-1 rounded-md border border-slate-300 px-3 py-2 text-sm outline-none focus:border-cyan-600 focus:ring-2 focus:ring-cyan-100"
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
          />
          <button
            className="rounded-md bg-slate-950 px-5 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:bg-slate-400"
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
            <h2 className="text-sm font-semibold uppercase tracking-wide text-cyan-700">Answer</h2>
            <p className="mt-3 leading-7 text-slate-700">{response.answer}</p>
          </article>
          <aside className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
            <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500">Citations</h2>
            <div className="mt-4 space-y-4">
              {response.citations.map((citation) => (
                <div className="rounded-md bg-slate-50 p-3" key={citation.source}>
                  <p className="font-semibold text-slate-950">{citation.title}</p>
                  <p className="text-xs text-slate-500">{citation.source}</p>
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
