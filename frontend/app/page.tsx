import Link from "next/link";

export default function Home() {
  return (
    <main className="landing">
      <nav className="topbar shell" aria-label="Main navigation">
        <div className="brand" aria-label="Auditly">
          <span className="brand-mark">A</span><span>auditly</span>
        </div>
        <div className="nav-links">
          <a href="#how-it-works">How it works</a>
          <Link className="nav-login" href="/login">Sign in</Link>
        </div>
      </nav>

      <section className="hero shell">
        <div className="hero-copy">
          <p className="kicker"><span className="status-dot" /> INVOICE &amp; PURCHASE ORDER REVIEW</p>
          <h1>Every invoice,<br />checked against<br />the <span className="serif-accent">right PO.</span></h1>
          <p className="hero-description">
            Auditly reads invoice and purchase order PDFs from labeled emails,
            extracts their details, and creates a clear comparison summary for your team.
          </p>
          <div className="hero-actions">
            <Link className="button button-dark" href="/login">Open dashboard <span>→</span></Link>
            <a className="text-link" href="#how-it-works">See how it works <span>↓</span></a>
          </div>
          <div className="hero-proof">
            <span className="status-dot" aria-hidden="true" />
            <span>From labeled email to review-ready comparison</span>
          </div>
        </div>

        <div className="workflow-visual" role="img" aria-label="Illustration of purchase orders and invoices being extracted and compared">
          <div className="workflow-topline"><span><i /> DOCUMENT WORKFLOW</span><small>GMAIL → REVIEW</small></div>
          <div className="workflow-content">
            <div className="workflow-step">
              <span className="workflow-icon po-icon">PO</span>
              <span className="workflow-doc-copy"><strong>Purchase order</strong><small>PDF received · details extracted</small></span>
              <span className="workflow-check">✓</span>
            </div>
            <div className="workflow-step">
              <span className="workflow-icon invoice-icon">IN</span>
              <span className="workflow-doc-copy"><strong>Invoice</strong><small>PDF received · matched by PO ID</small></span>
              <span className="workflow-check">✓</span>
            </div>
            <div className="workflow-connector"><span /></div>
            <div className="workflow-summary">
              <div className="workflow-summary-heading"><span><i /> COMPARISON SUMMARY</span><small>READY TO REVIEW</small></div>
              <strong>Invoice details checked against its PO</strong>
              <div className="workflow-fields"><span>Amounts</span><span>Line items</span><span>Identifiers</span></div>
            </div>
          </div>
          <div className="workflow-footer"><span>DOCUMENT AI EXTRACTION</span><span>COMPARISON SAVED</span></div>
        </div>
      </section>

      <section className="signal-strip shell" id="how-it-works" aria-label="How Auditly works">
        <p>THREE STEPS TO A CLEAR REVIEW</p>
        <div className="signal-item"><span>01</span>Read labeled Gmail PDFs</div>
        <div className="signal-item"><span>02</span>Extract invoice and PO details</div>
        <div className="signal-item"><span>03</span>Review the saved comparison</div>
      </section>

      <footer className="landing-footer shell">
        <span>© 2026 Auditly</span>
        <span>Invoice and purchase order review <span className="footer-star">✳</span></span>
      </footer>
    </main>
  );
}
