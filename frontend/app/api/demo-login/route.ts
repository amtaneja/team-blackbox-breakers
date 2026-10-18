import { NextResponse } from "next/server";
import {
  createSessionToken,
  secureStringEqual,
  SESSION_COOKIE,
  SESSION_DURATION_SECONDS,
} from "@/lib/demo-session";

export async function POST(request: Request) {
  let credentials: { email?: unknown; password?: unknown };
  try {
    credentials = await request.json();
  } catch {
    return NextResponse.json({ error: "Invalid request." }, { status: 400 });
  }

  const expectedEmail = process.env.AUDITLY_DEMO_EMAIL;
  const expectedPassword = process.env.AUDITLY_DEMO_PASSWORD;
  const sessionSecret = process.env.AUDITLY_SESSION_SECRET;
  if (!expectedEmail || !expectedPassword || !sessionSecret || sessionSecret.length < 32) {
    return NextResponse.json({ error: "Sign-in is not configured." }, { status: 503 });
  }

  if (
    typeof credentials.email !== "string" ||
    typeof credentials.password !== "string" ||
    !secureStringEqual(credentials.email.trim().toLowerCase(), expectedEmail.trim().toLowerCase()) ||
    !secureStringEqual(credentials.password, expectedPassword)
  ) {
    return NextResponse.json({ error: "Invalid demo credentials." }, { status: 401 });
  }

  const response = NextResponse.json({ success: true });
  response.cookies.set(SESSION_COOKIE, createSessionToken(), {
    httpOnly: true,
    sameSite: "strict",
    secure: process.env.NODE_ENV === "production",
    path: "/",
    maxAge: SESSION_DURATION_SECONDS,
  });
  return response;
}
