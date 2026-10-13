import Link from "next/link";

export default function Home() {
  return (
    <main className="landing">
      <nav className="topbar shell" aria-label="Main navigation">
        <Link className="brand" href="/" aria-label="Blackbox home"><span className="brand-mark">b.</span><span>blackbox<span className="brand-light">breakers</span></span></Link>
        <div className="nav-links"><a href="#how-it-works">How it works</a><Link className="nav-login" href="/login">Log in</Link><Link className="button button-small button-dark" href="/login">Get started <span>↗</span></Link></div>
      </nav>
      <section className="hero shell">
        <div className="hero-copy">
          <p className="kicker"><span className="status-dot" /> A clearer view starts here</p>
          <h1>Break through<br />the <span className="serif-accent">black box.</span></h1>
          <p className="hero-description">Turn complexity into clarity. Blackbox Breakers helps your team uncover what matters and make the next move with confidence.</p>
          <div className="hero-actions"><Link className="button button-dark" href="/login">Get started <span>→</span></Link><Link className="text-link" href="/login">Sign in to your account <span>↗</span></Link></div>
          <div className="hero-proof"><div className="avatar-stack" aria-hidden="true"><span>J</span><span>M</span><span>A</span><span>+</span></div><span>Built for teams that ask better questions</span></div>
        </div>
        <div className="hero-visual" aria-label="Illustration of a signal emerging from a dark grid">
          <div className="visual-label"><span className="live-dot" /> SIGNAL DETECTED <span className="visual-time">JUST NOW</span></div>
          <div className="signal-orbit orbit-one" /><div className="signal-orbit orbit-two" /><div className="signal-orbit orbit-three" />
          <div className="signal-core"><span>◎</span></div><div className="signal-line line-one"><i /> 0.92 <small>HIGH CONFIDENCE</small></div><div className="signal-line line-two"><i /> PATTERN FOUND</div>
          <div className="visual-footer"><span>ANALYSIS IN PROGRESS</span><span>▰▰▰▰▱ 82%</span></div>
        </div>
      </section>
      <section className="signal-strip shell" id="how-it-works"><p>CLARITY, BY DESIGN</p><div className="signal-item"><span>01</span>See the full picture</div><div className="signal-item"><span>02</span>Move with confidence</div><div className="signal-item"><span>03</span>Break through the noise</div></section>
      <footer className="landing-footer shell"><span>© 2026 Blackbox Breakers</span><span>Made for curious minds <span className="footer-star">✳</span></span></footer>
    </main>
  );
}
