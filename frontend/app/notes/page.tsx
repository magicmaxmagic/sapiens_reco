export const dynamic = "force-dynamic";

async function fetchNotes(): Promise<{ notes: unknown; error: string | null }> {
  try {
    const apiBase = process.env.NEXT_PUBLIC_API_URL?.trim() ?? "";
    const base = apiBase.replace(/\/$/, "");
    const url = base ? `${base}/notes` : "/api/notes";

    const res = await fetch(url, { cache: "no-store" });
    if (!res.ok) {
      const text = await res.text();
      return { notes: null, error: `Backend error: ${res.status} ${text}` };
    }

    const notes = await res.json();
    return { notes, error: null };
  } catch (error) {
    const message = error instanceof Error ? error.message : "Request failed";
    return { notes: null, error: message };
  }
}

export default async function Notes() {
  const { notes, error } = await fetchNotes();
  const payload = error ? { error } : notes;

  return <pre>{JSON.stringify(payload, null, 2)}</pre>;
}