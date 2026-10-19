import { NextRequest, NextResponse } from "next/server";
import { isValidSessionToken, SESSION_COOKIE } from "@/lib/demo-session";

export const runtime = "nodejs";

const MAX_REQUEST_BYTES = 24 * 1024 * 1024;
const ALLOWED_ROUTES = new Set([
  "inference",
  "documents/invoice/process",
  "documents/purchase-order/process",
  "documents/compare",
  "documents/compare/stream",
]);

type RouteContext = { params: Promise<{ path: string[] }> };

async function proxy(request: NextRequest, context: RouteContext) {
  if (!isValidSessionToken(request.cookies.get(SESSION_COOKIE)?.value)) {
    return NextResponse.json({ detail: "Sign in is required." }, { status: 401 });
  }

  const { path } = await context.params;
  if (!path?.length || path.some((part) => !/^[a-z0-9-]+$/.test(part))) {
    return NextResponse.json({ detail: "Unknown API route." }, { status: 404 });
  }
  const route = path.join("/");
  if (!ALLOWED_ROUTES.has(route)) {
    return NextResponse.json({ detail: "Unknown API route." }, { status: 404 });
  }
  if ((route === "inference" && request.method !== "GET") ||
      (route !== "inference" && request.method !== "POST")) {
    return NextResponse.json({ detail: "Method not allowed." }, { status: 405 });
  }

  const configuredBackendUrl = process.env.BACKEND_URL;
  if (!configuredBackendUrl) {
    return NextResponse.json({ detail: "Backend URL is not configured." }, { status: 503 });
  }
  const backendBase = configuredBackendUrl.replace(/\/$/, "");
  const target = `${backendBase}/${route}`;
  const headers = new Headers();
  const contentType = request.headers.get("content-type");
  if (contentType) headers.set("content-type", contentType);

  let body: ArrayBuffer | undefined;
  if (request.method === "POST") {
    const contentLength = Number(request.headers.get("content-length") ?? 0);
    if (contentLength > MAX_REQUEST_BYTES) {
      return NextResponse.json({ detail: "Request is too large." }, { status: 413 });
    }
    body = await request.arrayBuffer();
    if (body.byteLength > MAX_REQUEST_BYTES) {
      return NextResponse.json({ detail: "Request is too large." }, { status: 413 });
    }
  }

  if (process.env.NODE_ENV === "production") {
    try {
      const audience = new URL(backendBase).origin;
      const tokenUrl = new URL("http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/identity");
      tokenUrl.searchParams.set("audience", audience);
      tokenUrl.searchParams.set("format", "full");
      const tokenResponse = await fetch(tokenUrl, {
        headers: { "Metadata-Flavor": "Google" },
        cache: "no-store",
      });
      if (!tokenResponse.ok) throw new Error("Metadata token request failed");
      headers.set("authorization", `Bearer ${(await tokenResponse.text()).trim()}`);
    } catch {
      return NextResponse.json({ detail: "Backend authentication is unavailable." }, { status: 502 });
    }
  }

  try {
    const upstream = await fetch(target, {
      method: request.method,
      headers,
      body,
      cache: "no-store",
      signal: AbortSignal.timeout(900_000),
    });
    const responseHeaders = new Headers({
      "cache-control": "no-store",
      "content-type": upstream.headers.get("content-type") ?? "application/json",
    });
    return new Response(upstream.body, {
      status: upstream.status,
      headers: responseHeaders,
    });
  } catch {
    return NextResponse.json({ detail: "The backend could not be reached." }, { status: 502 });
  }
}

export const GET = proxy;
export const POST = proxy;
