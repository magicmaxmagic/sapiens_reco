const textEncoder = new TextEncoder();
const textDecoder = new TextDecoder();

export const APP_SESSION_COOKIE_NAME = "optimus_app_session";

const DEFAULT_SESSION_MAX_AGE_SECONDS = 60 * 60;

type SessionPayload = {
  sub: string;
  exp: number;
};

function toBase64Url(bytes: Uint8Array): string {
  let binary = "";
  for (const byte of bytes) {
    binary += String.fromCharCode(byte);
  }

  return btoa(binary)
    .replace(/\+/g, "-")
    .replace(/\//g, "_")
    .replace(/=+$/g, "");
}

function fromBase64Url(value: string): Uint8Array | null {
  try {
    const base64 = value.replace(/-/g, "+").replace(/_/g, "/");
    const padded = base64.padEnd(base64.length + ((4 - (base64.length % 4)) % 4), "=");
    const binary = atob(padded);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i += 1) {
      bytes[i] = binary.charCodeAt(i);
    }
    return bytes;
  } catch {
    return null;
  }
}

function safeStringEquals(left: string, right: string): boolean {
  if (left.length !== right.length) {
    return false;
  }

  let mismatch = 0;
  for (let i = 0; i < left.length; i += 1) {
    mismatch |= left.charCodeAt(i) ^ right.charCodeAt(i);
  }
  return mismatch === 0;
}

async function signPayload(payload: string, secret: string): Promise<string> {
  const key = await crypto.subtle.importKey(
    "raw",
    textEncoder.encode(secret),
    {
      name: "HMAC",
      hash: "SHA-256",
    },
    false,
    ["sign"],
  );

  const signatureBuffer = await crypto.subtle.sign("HMAC", key, textEncoder.encode(payload));
  return toBase64Url(new Uint8Array(signatureBuffer));
}

export function getSessionSecret(): string | null {
  const configured = process.env.APP_LOGIN_SESSION_SECRET?.trim() ?? "";
  return configured.length > 0 ? configured : null;
}

export function getSessionMaxAgeSeconds(): number {
  const configured = Number.parseInt(
    process.env.APP_LOGIN_SESSION_MAX_AGE_SECONDS ?? `${DEFAULT_SESSION_MAX_AGE_SECONDS}`,
    10,
  );

  if (!Number.isFinite(configured) || configured <= 0) {
    return DEFAULT_SESSION_MAX_AGE_SECONDS;
  }

  return configured;
}

export async function createSignedSessionToken(
  subject: string,
  secret: string,
  maxAgeSeconds: number,
): Promise<string> {
  const now = Math.floor(Date.now() / 1000);
  const payload: SessionPayload = {
    sub: subject,
    exp: now + maxAgeSeconds,
  };

  const encodedPayload = toBase64Url(textEncoder.encode(JSON.stringify(payload)));
  const signature = await signPayload(encodedPayload, secret);

  return `${encodedPayload}.${signature}`;
}

export async function verifySignedSessionToken(
  token: string,
  secret: string,
): Promise<SessionPayload | null> {
  const [encodedPayload, signature] = token.split(".");
  if (!encodedPayload || !signature) {
    return null;
  }

  const expectedSignature = await signPayload(encodedPayload, secret);
  if (!safeStringEquals(signature, expectedSignature)) {
    return null;
  }

  const payloadBytes = fromBase64Url(encodedPayload);
  if (!payloadBytes) {
    return null;
  }

  let parsed: unknown;
  try {
    parsed = JSON.parse(textDecoder.decode(payloadBytes));
  } catch {
    return null;
  }

  if (!parsed || typeof parsed !== "object") {
    return null;
  }

  const payload = parsed as Record<string, unknown>;
  if (typeof payload.sub !== "string" || typeof payload.exp !== "number") {
    return null;
  }

  const now = Math.floor(Date.now() / 1000);
  if (payload.exp <= now) {
    return null;
  }

  return {
    sub: payload.sub,
    exp: payload.exp,
  };
}

export function getSafeRedirectPath(pathname: string | null): string {
  if (!pathname) {
    return "/dashboard";
  }

  if (!pathname.startsWith("/") || pathname.startsWith("//")) {
    return "/dashboard";
  }

  return pathname;
}