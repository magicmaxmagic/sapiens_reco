import { NextResponse } from "next/server";

import { APP_SESSION_COOKIE_NAME } from "@/lib/app-session";

export async function POST() {
  const response = NextResponse.json({ ok: true });
  response.cookies.set({
    name: APP_SESSION_COOKIE_NAME,
    value: "",
    httpOnly: true,
    sameSite: "lax",
    secure: process.env.NODE_ENV === "production",
    path: "/",
    maxAge: 0,
  });
  return response;
}