"use client";

import { FormEvent, useState } from "react";
import ReactMarkdown from "react-markdown";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

export default function DocumentMatch() {
  const [invoice, setInvoice] = useState<File | null>(null);
  const [purchaseOrder, setPurchaseOrder] = useState<File | null>(null);
  const [analysis, setAnalysis] = useState("");
  const [status, setStatus] = useState("");
  const [busy, setBusy] = useState(false);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!invoice || !purchaseOrder) {
      setStatus("Choose both PDF files to compare.");
      return;
    }
    setBusy(true);
    setAnalysis("");
    setStatus("Processing invoice and purchase order…");
    try {
      const [invoiceResponse, poResponse] = await Promise.all([
        upload("documents/invoice/process", invoice),
        upload("documents/purchase-order/process", purchaseOrder),
      ]);
      const [invoiceData, poData] = await Promise.all([
        readJson(invoiceResponse), readJson(poResponse),
      ]);
      setStatus("Documents processed. Asking the agent to compare them…");
      const response = await fetch(`${API_BASE}/documents/compare/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ invoice: invoiceData, purchase_order: poData }),
      });
      if (!response.ok) throw new Error(await responseError(response));
      if (!response.body) throw new Error("The server did not return a stream.");

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let pending = "";
      let finished = false;
      while (!finished) {
        const { value, done } = await reader.read();
        pending += decoder.decode(value, { stream: !done });
        const frames = pending.split("\n\n");
        pending = frames.pop() ?? "";
        for (const frame of frames) {
          const event = frame.match(/^event: (\w+)/m)?.[1];
          const line = frame.split("\n").find((part) => part.startsWith("data: "));
          if (event === "error" && line) throw new Error(JSON.parse(line.slice(6)).detail);
          if (event === "done") finished = true;
          if (line && event !== "error" && event !== "done") {
            const payload = JSON.parse(line.slice(6)) as { text?: string };
            if (payload.text) setAnalysis((current) => current + payload.text);
          }
        }
        if (done) finished = true;
      }
      setStatus("Comparison complete");
    } catch (error) {
      setStatus(error instanceof TypeError
        ? `Cannot reach the backend at ${API_BASE}. Start the backend API and try again.`
        : error instanceof Error ? error.message : "Comparison failed. Please try again.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="match-panel" id="document-match">
      <div className="match-heading">
        <div><p className="kicker">DOCUMENT REVIEW</p><h2>Match an invoice to a PO</h2><p>Upload both PDFs to check amounts, parties, identifiers, and line items.</p></div>
        <span className="match-mark">⇄</span>
      </div>
      <form className="match-form" onSubmit={onSubmit}>
        <label className="upload-card" htmlFor="invoice-file"><span className="upload-icon">IN</span><span><strong>Invoice</strong><small>{invoice?.name ?? "Choose an invoice PDF"}</small></span><span className="choose-file">Browse</span><input id="invoice-file" type="file" accept="application/pdf,.pdf" onChange={(e) => setInvoice(e.target.files?.[0] ?? null)} /></label>
        <label className="upload-card" htmlFor="po-file"><span className="upload-icon po">PO</span><span><strong>Purchase order</strong><small>{purchaseOrder?.name ?? "Choose a purchase order PDF"}</small></span><span className="choose-file">Browse</span><input id="po-file" type="file" accept="application/pdf,.pdf" onChange={(e) => setPurchaseOrder(e.target.files?.[0] ?? null)} /></label>
        <div className="match-submit-row"><span className="match-status" aria-live="polite">{status}</span><button className="button button-dark" disabled={busy}>{busy ? "Working…" : "Compare documents"}<span>→</span></button></div>
      </form>
      {(analysis || (busy && status.startsWith("Documents processed"))) && <div className="agent-result" aria-live="polite"><div className="result-label"><span className="live-dot" /> AGENT ANALYSIS</div><div className="result-copy">{analysis ? <ReactMarkdown>{analysis}</ReactMarkdown> : <span className="typing-indicator">Preparing comparison…</span>}</div></div>}
    </section>
  );
}

async function upload(path: string, file: File) {
  const data = new FormData();
  data.append("file", file);
  const response = await fetch(`${API_BASE}/${path}`, { method: "POST", body: data });
  if (!response.ok) throw new Error(await responseError(response));
  return response;
}

async function readJson(response: Response) { return response.json() as Promise<Record<string, unknown>>; }
async function responseError(response: Response) {
  const body = await response.json().catch(() => null) as { detail?: string } | null;
  return body?.detail ?? `Request failed (${response.status})`;
}
