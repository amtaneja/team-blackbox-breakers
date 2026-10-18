"use client";

import { useCallback, useEffect, useState } from "react";
import InferenceDetail, { type InferenceRecord } from "./inference-detail";

const API_BASE = "/api/backend";

export default function InferenceOverview() {
  const [records, setRecords] = useState<InferenceRecord[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadRecords = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const response = await fetch(`${API_BASE}/inference`, { cache: "no-store" });
      if (!response.ok) {
        const body = await response.json().catch(() => null) as { detail?: string } | null;
        throw new Error(body?.detail ?? `Request failed (${response.status})`);
      }
      const body = await response.json() as { items?: InferenceRecord[] };
      setRecords(body.items ?? []);
    } catch (loadError) {
      setError(loadError instanceof TypeError
        ? "Cannot reach the backend. Please try again."
        : loadError instanceof Error ? loadError.message : "Could not load inference records.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void loadRecords(); }, [loadRecords]);

  const selectedRecord = records.find((record) => record.id === selectedId);
  if (selectedRecord) {
    return <InferenceDetail record={selectedRecord} onBack={() => setSelectedId(null)} />;
  }

  return (
    <section className="inference-panel" aria-labelledby="inference-title">
      <div className="inference-heading">
        <div>
          <p className="kicker">DOCUMENT REVIEW</p>
          <h1 id="inference-title">Invoice comparisons</h1>
          <p>Summaries from invoices matched against their purchase orders.</p>
        </div>
        <button className="button button-dark inference-refresh" onClick={() => void loadRecords()} disabled={loading}>
          {loading ? <><span className="circular-loader" aria-hidden="true" /><span>Loading…</span></> : "Refresh"}
        </button>
      </div>

      {loading && records.length === 0 && <p className="inference-state inference-loading" role="status"><span className="circular-loader" aria-hidden="true" />Loading comparison summaries…</p>}
      {!loading && error && <div className="inference-state inference-error" role="alert"><span>{error}</span><button onClick={() => void loadRecords()}>Try again</button></div>}
      {!loading && !error && records.length === 0 && <p className="inference-state">No comparison summaries yet. They will appear here after an invoice is matched with a purchase order.</p>}

      {records.length > 0 && (
        <div className="inference-results">
          <div className="inference-table-wrap">
            <table className="inference-table">
              <thead>
                <tr><th>Invoice</th><th>Purchase order</th><th>Compared</th></tr>
              </thead>
              <tbody>
                {records.map((record) => (
                  <tr
                    key={record.id}
                    className={selectedId === record.id ? "selected" : ""}
                    onClick={() => setSelectedId(record.id)}
                    onKeyDown={(event) => {
                      if (event.key === "Enter" || event.key === " ") {
                        event.preventDefault();
                        setSelectedId(record.id);
                      }
                    }}
                    tabIndex={0}
                    aria-selected={selectedId === record.id}
                  >
                    <td>{record.invoice_id || "ID unavailable"}</td>
                    <td>{record.po_id || "ID unavailable"}</td>
                    <td>{formatTimestamp(record.timestamp)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </section>
  );
}

function formatTimestamp(value: string | null) {
  if (!value) return "Time unavailable";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "Time unavailable" : date.toLocaleString();
}
