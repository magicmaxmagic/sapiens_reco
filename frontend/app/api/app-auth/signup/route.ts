import { NextResponse } from "next/server";

type SignupPayload = {
  username?: string;
  email?: string;
  password?: string;
};

type BackendSignupResponse = {
  id: string;
  username: string;
  email: string;
  role: string;
  message?: string;
};

function extractDetail(value: unknown): string | null {
  if (!value || typeof value !== "object") {
    return null;
  }

  const detail = (value as Record<string, unknown>).detail;
  return typeof detail === "string" ? detail : null;
}

export async function POST(request: Request) {
  let payload: SignupPayload;
  try {
    payload = (await request.json()) as SignupPayload;
  } catch {
    return NextResponse.json({ detail: "Payload JSON invalide." }, { status: 400 });
  }

  const username = payload.username?.trim() ?? "";
  const email = payload.email?.trim() ?? "";
  const password = payload.password ?? "";

  if (!username || !email || !password) {
    return NextResponse.json({ detail: "Tous les champs sont requis." }, { status: 400 });
  }

  const apiBase = process.env.NEXT_PUBLIC_API_URL?.trim();
  if (!apiBase) {
    return NextResponse.json(
      {
        detail:
          "Configuration manquante: NEXT_PUBLIC_API_URL n'est pas definie sur ce deploiement.",
      },
      { status: 500 },
    );
  }

  let upstream: Response;
  try {
    upstream = await fetch(`${apiBase}/auth/signup`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        username,
        email,
        password,
      }),
      cache: "no-store",
    });
  } catch {
    return NextResponse.json(
      {
        detail:
          "Backend API inaccessible. Verifie NEXT_PUBLIC_API_URL et que le backend est bien deploye publiquement.",
      },
      { status: 502 },
    );
  }

  if (!upstream.ok) {
    let detail = "Echec de l'inscription.";
    try {
      detail = extractDetail(await upstream.json()) ?? detail;
    } catch {
      // Keep default detail when parsing fails.
    }

    // Map status codes appropriately
    const status = upstream.status === 409 ? 409 : upstream.status === 400 ? 400 : 502;
    return NextResponse.json({ detail }, { status });
  }

  const userData = (await upstream.json()) as BackendSignupResponse;
  return NextResponse.json(userData, { status: 201 });
}