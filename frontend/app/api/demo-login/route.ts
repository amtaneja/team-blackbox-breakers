import { NextResponse } from "next/server";

const DEMO_EMAIL = "demo@blackboxbreakers.com";
const DEMO_PASSWORD = "breaker2026";
const SESSION_COOKIE = "bb-demo-session";

export async function POST(request: Request) {
  let credentials: { email?: unknown; password?: unknown };
  try {
    credentials = await request.json();
  } catch {
    return NextResponse.json({ error: "Invalid request." }, { status: 400 });
  }

  if (
    typeof credentials.email !== "string" ||
    typeof credentials.password !== "string" ||
    credentials.email.trim().toLowerCase() !== DEMO_EMAIL ||
    credentials.password !== DEMO_PASSWORD
  ) {
    return NextResponse.json({ error: "Invalid demo credentials." }, { status: 401 });
  }

  const response = NextResponse.json({ success: true });
  response.cookies.set(SESSION_COOKIE, "authenticated", {
    httpOnly: true,
    sameSite: "lax",
    secure: process.env.NODE_ENV === "production",
    path: "/",
  });
  return response;
}
