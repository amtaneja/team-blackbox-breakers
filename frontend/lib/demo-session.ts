import { createHmac, timingSafeEqual } from "node:crypto";

export const SESSION_COOKIE = "bb-demo-session";
export const SESSION_DURATION_SECONDS = 8 * 60 * 60;

function sessionSecret() {
  const secret = process.env.AUDITLY_SESSION_SECRET;
  if (!secret || secret.length < 32) {
    throw new Error("AUDITLY_SESSION_SECRET must be configured with at least 32 characters.");
  }
  return secret;
}

function signature(expiresAt: number) {
  return createHmac("sha256", sessionSecret())
    .update(`auditly-session:${expiresAt}`)
    .digest("base64url");
}

export function createSessionToken(now = Date.now()) {
  const expiresAt = Math.floor(now / 1000) + SESSION_DURATION_SECONDS;
  return `${expiresAt}.${signature(expiresAt)}`;
}

export function isValidSessionToken(token?: string) {
  if (!token) return false;
  const [expiresAtText, suppliedSignature, extra] = token.split(".");
  if (!expiresAtText || !suppliedSignature || extra !== undefined) return false;
  const expiresAt = Number(expiresAtText);
  if (!Number.isSafeInteger(expiresAt) || expiresAt <= Math.floor(Date.now() / 1000)) {
    return false;
  }

  try {
    const expected = Buffer.from(signature(expiresAt));
    const supplied = Buffer.from(suppliedSignature);
    return supplied.length === expected.length && timingSafeEqual(supplied, expected);
  } catch {
    return false;
  }
}

export function secureStringEqual(left: string, right: string) {
  const leftDigest = createHmac("sha256", "auditly-credential-compare").update(left).digest();
  const rightDigest = createHmac("sha256", "auditly-credential-compare").update(right).digest();
  return timingSafeEqual(leftDigest, rightDigest);
}
