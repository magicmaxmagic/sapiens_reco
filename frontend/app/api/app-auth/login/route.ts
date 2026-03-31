import { NextResponse } from "next/server";

import {
  APP_SESSION_COOKIE_NAME,
  createSignedSessionToken,
  getSessionMaxAgeSeconds,
  getSessionSecret,
} from "@/lib/app-session";

type LoginPayload = {
  username?: string;
  password?: string;
};

type BackendLoginResponse = {
  access_token: string;
  token_type: string;
  expires_in: number;
};

function extractDetail(value: unknown): string | null {
  if (!value || typeof value !== "object") {
    return null;
  }

  const detail = (value as Record<string, unknown>).detail;
  return typeof detail === "string" ? detail : null;
}

export async function POST(request: Request) {
  const sessionSecret = getSessionSecret();
  if (!sessionSecret) {
    return NextResponse.json(
      { detail: "Session frontend non configuree (APP_LOGIN_SESSION_SECRET manquant)." },
      { status: 500 },
    );
  }

  let payload: LoginPayload;
  try {
    payload = (await request.json()) as LoginPayload;
  } catch {
    return NextResponse.json({ detail: "Payload JSON invalide." }, { status: 400 });
  }

  const username = payload.username?.trim() ?? "";
  const password = payload.password ?? "";

  if (!username || !password) {
    return NextResponse.json({ detail: "Identifiant et mot de passe requis." }, { status: 400 });
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
    upstream = await fetch(`${apiBase}/auth/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ username, password }),
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
    let detail = "Echec d'authentification.";
    try {
      detail = extractDetail(await upstream.json()) ?? detail;
    } catch {
      // Keep default detail when parsing fails.
    }

    return NextResponse.json(
      { detail },
      { status: upstream.status === 401 ? 401 : 502 },
    );
  }

  const tokenData = (await upstream.json()) as BackendLoginResponse;
  if (!tokenData.access_token || typeof tokenData.access_token !== "string") {
    return NextResponse.json(
      { detail: "Reponse auth backend invalide." },
      { status: 502 },
    );
  }

  const configuredMaxAge = getSessionMaxAgeSeconds();
  const backendMaxAge = Number.isFinite(tokenData.expires_in) && tokenData.expires_in > 0
    ? Math.floor(tokenData.expires_in)
    : configuredMaxAge;
  const maxAgeSeconds = Math.max(60, Math.min(configuredMaxAge, backendMaxAge));

  const sessionToken = await createSignedSessionToken(username, sessionSecret, maxAgeSeconds);

  const response = NextResponse.json(tokenData, { status: 200 });
  response.cookies.set({
    name: APP_SESSION_COOKIE_NAME,
    value: sessionToken,
    httpOnly: true,
    sameSite: "lax",
    secure: process.env.NODE_ENV === "production",
    path: "/",
    maxAge: maxAgeSeconds,
  });

  return response;
}