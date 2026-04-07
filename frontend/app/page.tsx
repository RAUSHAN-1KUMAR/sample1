"use client";

import { FormEvent, useState } from "react";

type StoryboardPanel = {
  original_text: string;
  enhanced_prompt: string;
  image_url: string;
};

const STYLE_OPTIONS = [
  "Photorealistic",
  "Digital Art",
  "Watercolor",
  "Cyberpunk",
];
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8001";

export default function Home() {
  const [text, setText] = useState("");
  const [style, setStyle] = useState(STYLE_OPTIONS[0]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [panels, setPanels] = useState<StoryboardPanel[]>([]);
  const [openPrompts, setOpenPrompts] = useState<Record<number, boolean>>({});

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setPanels([]);
    setOpenPrompts({});

    if (!text.trim()) {
      setError("Please paste a short narrative first.");
      return;
    }

    setIsLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/generate-storyboard`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, style }),
      });
      if (!response.ok) {
        const fallback = `Request failed with status ${response.status}`;
        try {
          const errorBody = (await response.json()) as { detail?: string };
          throw new Error(errorBody.detail || fallback);
        } catch {
          throw new Error(fallback);
        }
      }
      const data: { storyboard: StoryboardPanel[] } = await response.json();
      setPanels(data.storyboard ?? []);
    } catch (submitError) {
      const message =
        submitError instanceof Error
          ? submitError.message
          : "Something went wrong while generating the storyboard.";
      setError(message);
    } finally {
      setIsLoading(false);
    }
  }

  function togglePrompt(index: number) {
    setOpenPrompts((previous) => ({ ...previous, [index]: !previous[index] }));
  }

  return (
    <main className="min-h-screen bg-slate-950 px-6 py-10 text-slate-100 md:px-10">
      <div className="mx-auto flex w-full max-w-6xl flex-col gap-10">
        <section className="rounded-2xl border border-slate-700/60 bg-slate-900/70 p-6 shadow-xl md:p-8">
          <h1 className="text-3xl font-bold md:text-4xl">The Pitch Visualizer</h1>
          <p className="mt-3 max-w-2xl text-slate-300">
            Turn your narrative into a cinematic storyboard. Paste 3 to 5 sentences,
            pick a visual style, and generate scene panels instantly.
          </p>

          <form className="mt-6 space-y-5" onSubmit={handleSubmit}>
            <div>
              <label className="mb-2 block text-sm font-medium">Narrative</label>
              <textarea
                value={text}
                onChange={(event) => setText(event.target.value)}
                rows={7}
                placeholder="A lone founder walks onto a dimly lit stage, takes a breath, and begins..."
                className="w-full rounded-xl border border-slate-700 bg-slate-950/80 p-4 text-slate-100 outline-none ring-cyan-400 transition focus:ring-2"
              />
            </div>

            <div className="flex flex-col gap-4 sm:flex-row sm:items-end">
              <div className="sm:w-72">
                <label className="mb-2 block text-sm font-medium">Visual Style</label>
                <select
                  value={style}
                  onChange={(event) => setStyle(event.target.value)}
                  className="w-full rounded-xl border border-slate-700 bg-slate-950/80 p-3 outline-none ring-cyan-400 transition focus:ring-2"
                >
                  {STYLE_OPTIONS.map((option) => (
                    <option key={option} value={option}>
                      {option}
                    </option>
                  ))}
                </select>
              </div>
              <button
                type="submit"
                disabled={isLoading}
                className="rounded-xl bg-cyan-500 px-5 py-3 font-semibold text-slate-950 transition hover:bg-cyan-400 disabled:cursor-not-allowed disabled:bg-cyan-700"
              >
                {isLoading ? "Generating..." : "Generate Storyboard"}
              </button>
            </div>
          </form>

          {error && <p className="mt-4 text-sm text-red-400">{error}</p>}
        </section>

        {isLoading && (
          <section className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">
            {[0, 1, 2].map((item) => (
              <div
                key={item}
                className="animate-pulse rounded-2xl border border-slate-700 bg-slate-900 p-4"
              >
                <div className="h-52 rounded-xl bg-slate-800" />
                <div className="mt-4 h-4 w-3/4 rounded bg-slate-800" />
                <div className="mt-2 h-4 w-1/2 rounded bg-slate-800" />
              </div>
            ))}
          </section>
        )}

        {!isLoading && panels.length > 0 && (
          <section className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">
            {panels.map((panel, index) => (
              <article
                key={`${panel.original_text}-${index}`}
                className="overflow-hidden rounded-2xl border border-slate-700 bg-slate-900 shadow-lg"
              >
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={panel.image_url}
                  alt={`Storyboard scene ${index + 1}`}
                  className="h-56 w-full object-cover"
                />
                <div className="space-y-3 p-4">
                  <p className="text-sm text-slate-200">{panel.original_text}</p>
                  <button
                    type="button"
                    onClick={() => togglePrompt(index)}
                    className="text-sm font-medium text-cyan-400 hover:text-cyan-300"
                  >
                    {openPrompts[index] ? "Hide enhanced prompt" : "View enhanced prompt"}
                  </button>
                  {openPrompts[index] && (
                    <p className="rounded-lg bg-slate-950 p-3 text-xs leading-5 text-slate-300">
                      {panel.enhanced_prompt}
                    </p>
                  )}
                </div>
              </article>
            ))}
          </section>
        )}
      </div>
    </main>
  );
}
