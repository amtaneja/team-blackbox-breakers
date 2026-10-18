"use client";

import Link from "next/link";
import { useState } from "react";
import DocumentMatch from "./document-match";
import InferenceOverview from "./inference-overview";

export default function DashboardWorkspace() {
  const [tab, setTab] = useState<"overview" | "document-match">("overview");
  const title = tab === "overview" ? "Overview" : "Document match";
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
        <header className="dash-topbar"><span className="breadcrumb">Workspace <span>/</span> {title}</span><a className="top-avatar" href="/api/demo-logout" aria-label="Sign out">BB</a></header>
        <div className="dash-content">{tab === "overview" ? <InferenceOverview /> : <DocumentMatch />}</div>
      </section>
    </main>
  );
}
