"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { DEMO_EMAIL } from "@/lib/demo-credentials";
import DocumentMatch from "./document-match";
import InferenceOverview from "./inference-overview";

export default function DashboardWorkspace() {
  const [tab, setTab] = useState<"overview" | "document-match">("overview");
  const [accountMenuOpen, setAccountMenuOpen] = useState(false);
  const accountMenuRef = useRef<HTMLDivElement>(null);
  const title = tab === "overview" ? "Overview" : "Document match";
  const loginName = DEMO_EMAIL.split("@")[0] ?? DEMO_EMAIL;
  const avatarInitial = loginName.charAt(0).toUpperCase();

  useEffect(() => {
    function handlePointerDown(event: MouseEvent) {
      if (!accountMenuRef.current?.contains(event.target as Node)) {
        setAccountMenuOpen(false);
      }
    }

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") setAccountMenuOpen(false);
    }

    document.addEventListener("mousedown", handlePointerDown);
    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("mousedown", handlePointerDown);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, []);

  return (
    <main className="dashboard-page">
      <aside className="sidebar">
        <Link className="brand sidebar-brand" href="/" aria-label="Auditly home"><span className="brand-mark">A</span><span>auditly</span></Link>
        <p className="sidebar-caption">WORKSPACE</p>
        <nav className="side-nav" aria-label="Dashboard navigation">
          <button className={`side-link ${tab === "overview" ? "selected" : ""}`} onClick={() => setTab("overview")}><span className="side-icon">▦</span>Overview</button>
          <button className={`side-link ${tab === "document-match" ? "selected" : ""}`} onClick={() => setTab("document-match")}><span className="side-icon">⇄</span>Document match</button>
        </nav>
      </aside>
      <section className="dashboard-main">
        <header className="dash-topbar">
          <span className="breadcrumb">Workspace <span>/</span> {title}</span>
          <div className="account-control" ref={accountMenuRef}>
            <button
              className="top-avatar"
              type="button"
              aria-label={`Account menu for ${loginName}`}
              aria-expanded={accountMenuOpen}
              aria-controls="account-menu"
              title={loginName}
              onClick={() => setAccountMenuOpen((open) => !open)}
            >
              {avatarInitial}
            </button>
            {accountMenuOpen && (
              <div className="account-menu" id="account-menu" aria-label="Account menu">
                <span className="account-menu-username">{loginName}</span>
                <a className="account-menu-logout" href="/api/demo-logout">Log out</a>
              </div>
            )}
          </div>
        </header>
        <div className="dash-content">{tab === "overview" ? <InferenceOverview /> : <DocumentMatch />}</div>
      </section>
    </main>
  );
}
