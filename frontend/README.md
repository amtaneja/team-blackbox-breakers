# Auditly frontend sign-in

The sign-in page displays a shared public demo account:

- Email: `demo@auditly.app`
- Password: `AuditlyDemo2026!`

These credentials are intentionally included in the frontend and are not
private. Anyone can sign in and access the records available to the demo
account. Use only with demo or sanitized invoice and purchase order data.

The session cookie is signed with `AUDITLY_SESSION_SECRET`. Configure a random
value of at least 32 characters in Secret Manager for Cloud Run, or in
`frontend/.env.local` for local development. Generate one locally with
`openssl rand -hex 32`.

Set `BACKEND_URL` to the backend API URL. Keep the backend private; the frontend
server proxy calls it with a Cloud Run identity token. Grant the frontend Cloud
Run runtime service account `roles/run.invoker` on the backend service. The
deploy script mounts only the session signing secret.
