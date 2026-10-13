import Link from "next/link";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";

const activity = [
  { initials: "ML", name: "Model performance review", detail: "Risk analysis · Updated 12 minutes ago", tag: "In review", tone: "purple", amount: "94.2%" },
  { initials: "DS", name: "Customer signal overview", detail: "Customer insights · Updated 1 hour ago", tag: "Ready", tone: "green", amount: "+18.6%" },
  { initials: "OP", name: "Operations anomaly scan", detail: "Systems health · Updated yesterday", tag: "Monitoring", tone: "amber", amount: "3 alerts" },
];

export default async function DashboardPage() {
  const session = await cookies();
  if (session.get("bb-demo-session")?.value !== "authenticated") {
    redirect("/login");
  }

  return (
    <main className="dashboard-page">
      <aside className="sidebar">
        <Link className="brand sidebar-brand" href="/"><span className="brand-mark">b.</span><span>blackbox<span className="brand-light">breakers</span></span></Link>
        <p className="sidebar-caption">WORKSPACE</p>
        <nav className="side-nav" aria-label="Dashboard navigation"><a className="side-link selected" href="#overview"><span className="side-icon">▦</span>Overview</a><a className="side-link" href="#insights"><span className="side-icon">◈</span>Insights</a><a className="side-link" href="#activity"><span className="side-icon">◷</span>Activity</a><a className="side-link" href="#settings"><span className="side-icon">⚙</span>Settings</a></nav>
        <div className="sidebar-bottom"><div className="help-card"><span className="help-icon">✳</span><strong>Need a hand?</strong><p>We’re here to help you find your signal.</p><a href="mailto:support@blackboxbreakers.com">Visit help center ↗</a></div><div className="profile"><span className="profile-avatar">BB</span><span><strong>Breaker Team</strong><small>Demo workspace</small></span><a className="profile-menu" href="/api/demo-logout" aria-label="Sign out">↗</a></div></div>
      </aside>
      <section className="dashboard-main" id="overview">
        <header className="dash-topbar"><span className="breadcrumb">Workspace <span>/</span> Overview</span><div className="dash-top-actions"><span className="today-label"><span className="status-dot" /> All systems normal</span><button className="icon-button" aria-label="Notifications">♧<i /></button><a className="top-avatar" href="/api/demo-logout" aria-label="Sign out">BB</a></div></header>
        <div className="dash-content">
          <div className="welcome-row"><div><p className="kicker">TUESDAY, OCTOBER 13, 2026</p><h1>Good morning, Breakers <span>✳</span></h1><p className="welcome-sub">Here’s what’s happening across your workspace.</p></div><button className="button button-dark new-analysis"><span>＋</span> New analysis</button></div>
          <div className="metric-grid" id="insights">
            <article className="metric-card"><div className="metric-top"><span>Active analyses</span><span className="metric-icon lavender">◈</span></div><div className="metric-value">12 <span className="metric-change positive">↗ 3</span></div><p>Compared to last week</p><div className="mini-bars bars-purple" aria-hidden="true">{[28,45,37,58,42,68,51,78,60,92,70,100,76,88].map((h,i)=><i key={i} style={{height:`${h}%`}} />)}</div></article>
            <article className="metric-card"><div className="metric-top"><span>Signals uncovered</span><span className="metric-icon mint">⌁</span></div><div className="metric-value">248 <span className="metric-change positive">↗ 12.8%</span></div><p>Compared to last week</p><div className="mini-bars bars-mint" aria-hidden="true">{[35,52,43,68,50,63,45,78,57,70,61,93,72,100].map((h,i)=><i key={i} style={{height:`${h}%`}} />)}</div></article>
            <article className="metric-card"><div className="metric-top"><span>Team confidence</span><span className="metric-icon peach">◎</span></div><div className="metric-value">92<span className="metric-unit">/100</span><span className="metric-change positive">↗ 4.2%</span></div><p>Across your active projects</p><div className="confidence-track"><i /></div></article>
          </div>
          <section className="activity-panel" id="activity"><div className="panel-heading"><div><h2>Recent analyses</h2><p>Your team&apos;s latest discoveries</p></div><a href="#activity">View all <span>→</span></a></div><div className="activity-table"><div className="table-head"><span>ANALYSIS</span><span>STATUS</span><span>KEY SIGNAL</span><span /></div>{activity.map((item)=><article className="activity-row" key={item.name}><span className="analysis-name"><span className={`analysis-icon ${item.tone}`}>{item.initials}</span><span><strong>{item.name}</strong><small>{item.detail}</small></span></span><span className={`status-pill ${item.tone}`}><i />{item.tag}</span><strong className="signal-value">{item.amount}</strong><button className="row-menu" aria-label={`More options for ${item.name}`}>···</button></article>)}</div><Link className="mobile-view-all" href="#activity">View all analyses →</Link></section>
          <div className="dash-bottom"><section className="insight-card"><div className="insight-symbol">✳</div><div><p className="kicker">A PATTERN WORTH A LOOK</p><h2>Your strongest signal is trending up.</h2><p>Team confidence has increased for 3 weeks in a row. Take a closer look at what’s working.</p><a href="#insights">Explore this insight <span>→</span></a></div><div className="insight-spark" aria-hidden="true">{[28,43,38,56,48,70,64,96].map((height,i)=><i key={i} style={{height:`${height}%`}} />)}</div></section><section className="quick-card" id="settings"><p className="kicker">QUICK START</p><h2>Curiosity leads to clarity.</h2><p>Start a new analysis and see what your data has to say.</p><button className="button button-outline">Start exploring <span>→</span></button></section></div>
          <footer className="dash-footer"><span>Blackbox Breakers <span>·</span> Your signal, made clear.</span><Link href="/">Back to home ↗</Link></footer>
        </div>
      </section>
    </main>
  );
}
