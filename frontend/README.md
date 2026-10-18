# Auditly frontend deployment and sign-in

The dashboard uses environment-configured credentials and a signed, eight-hour
session cookie. Keep these values in Secret Manager; do not commit real values
to `.env.local` or `.env.example`:

- `auditly-demo-email`: the allowed sign-in email
- `auditly-demo-password`: a long, unique password
- `auditly-session-secret`: at least 32 random characters

Create each secret and add a version in Secret Manager. The Cloud Run frontend
runtime service account needs `roles/secretmanager.secretAccessor` on these
secrets. The deploy script mounts the latest secret versions as runtime
environment variables.

Set `BACKEND_URL` to the backend API URL. Keep the backend private; the frontend
server proxy calls it with a Cloud Run identity token. Grant the frontend Cloud
Run runtime service account `roles/run.invoker` on the backend service. The
backend deploy script defaults to private invocation.

For local development, set `BACKEND_URL`, `AUDITLY_DEMO_EMAIL`,
`AUDITLY_DEMO_PASSWORD`, and `AUDITLY_SESSION_SECRET` in
`frontend/.env.local`. Generate a session secret locally with
`openssl rand -hex 32`.
