"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

export default function LoginPage() {
  const router = useRouter();
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setIsSubmitting(true);

    const formData = new FormData(event.currentTarget);
    try {
      const response = await fetch("/api/demo-login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: formData.get("email"),
          password: formData.get("password"),
        }),
      });

      if (!response.ok) {
        setError("That email and password don’t match the demo account.");
        return;
      }

      router.replace("/dashboard");
      router.refresh();
    } catch {
      setError("We couldn’t sign you in. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="auth-page">
      <Link className="brand auth-brand" href="/" aria-label="Auditly home"><span className="brand-mark">A</span><span>auditly</span></Link>
      <section className="auth-card">
        <div className="auth-heading"><p className="kicker">PUBLIC DEMO ACCOUNT</p><h1>Explore<br />Auditly.</h1><p>Use the shared demo sign-in below. These credentials are public.</p></div>
        <div className="demo-credentials" aria-label="Public demo credentials">
          <p><strong>Email</strong><span>demo@auditly.app</span></p>
          <p><strong>Password</strong><span>AuditlyDemo2026!</span></p>
        </div>
        <form className="login-form" onSubmit={handleSubmit}>
          <label htmlFor="email">Email address</label><input id="email" name="email" type="email" placeholder="you@company.com" autoComplete="username" required />
          <div className="password-label"><label htmlFor="password">Password</label></div>
          <input id="password" name="password" type="password" placeholder="Enter your password" autoComplete="current-password" required />
          {error && <p className="login-error" role="alert">{error}</p>}
          <button className="button button-dark login-submit" type="submit" disabled={isSubmitting}>{isSubmitting ? <><span className="circular-loader" aria-hidden="true" /><span>Signing in…</span></> : <>Sign in <span aria-hidden="true">→</span></>}</button>
        </form>
      </section>
      <p className="auth-footer"><Link href="/">← Back to home</Link><span>© 2026 Auditly</span></p>
    </main>
  );
}
