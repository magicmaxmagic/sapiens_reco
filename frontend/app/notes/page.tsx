import { createClient } from "@/utils/supabase/server";

export const dynamic = "force-dynamic";

async function fetchNotes(): Promise<{ notes: unknown; error: string | null }> {
  try {
    const supabase = await createClient();
    const { data: notes, error } = await supabase.from("notes").select();

    if (error) {
      return { notes: null, error: error.message };
    }

    return { notes, error: null };
  } catch (error) {
    const message = error instanceof Error ? error.message : "Supabase configuration missing";
    return { notes: null, error: message };
  }
}

export default async function Notes() {
  const { notes, error } = await fetchNotes();
  const payload = error ? { error } : notes;

  return <pre>{JSON.stringify(payload, null, 2)}</pre>;
}