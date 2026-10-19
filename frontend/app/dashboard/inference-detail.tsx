"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

export type InferenceRecord = {
  id: string;
  invoice_id: string | null;
  po_id: string | null;
  summary: string;
  timestamp: string | null;
  email_from?: string | null;
  email_subject?: string | null;
  invoice_file_link?: string | null;
  po_file_link?: string | null;
};

type Props = {
  record: InferenceRecord;
  onBack: () => void;
};

export default function InferenceDetail({ record, onBack }: Props) {
  return (
    <section className="inference-detail-page" aria-labelledby="inference-detail-title">
      <button className="inference-back-button" type="button" onClick={onBack}>
        <span aria-hidden="true">←</span> Back to comparisons
      </button>

      <header className="inference-detail-heading">
        <div>
          <p className="kicker">COMPARISON SUMMARY</p>
          <h1 id="inference-detail-title">Invoice {record.invoice_id || "ID unavailable"}</h1>
          <p>Purchase order {record.po_id || "ID unavailable"}</p>
        </div>
        <time dateTime={record.timestamp ?? undefined}>{formatTimestamp(record.timestamp)}</time>
      </header>

      <dl className="inference-detail-metadata">
        <div><dt>Email from</dt><dd>{record.email_from || "Not available"}</dd></div>
        <div><dt>Email subject</dt><dd>{record.email_subject || "Not available"}</dd></div>
        <div><dt>Invoice PDF</dt><dd><StoragePdfLink uri={record.invoice_file_link} label="Open invoice PDF" /></dd></div>
        <div><dt>Purchase order PDF</dt><dd><StoragePdfLink uri={record.po_file_link} label="Purchase order PDF" /></dd></div>
      </dl>

      <article className="inference-detail-summary">
        <ReactMarkdown remarkPlugins={[remarkGfm]}>
          {formatSummary(record.summary || "No summary available.")}
        </ReactMarkdown>
      </article>
    </section>
  );
}

function StoragePdfLink({ uri, label }: { uri?: string | null; label: string }) {
  const href = toAuthenticatedStorageUrl(uri);
  if (!href) return <>Not available</>;

  return (
    <a className="inference-pdf-link" href={href} target="_blank" rel="noopener noreferrer">
      {label} <span aria-hidden="true">↗</span>
    </a>
  );
}

function toAuthenticatedStorageUrl(uri?: string | null) {
  if (!uri) return null;
  const match = /^gs:\/\/([^/]+)\/(.+)$/.exec(uri);
  if (!match) return null;

  const [, bucket, objectPath] = match;
  const encodedObjectPath = objectPath.split("/").map(encodeURIComponent).join("/");
  return `https://storage.cloud.google.com/${encodeURIComponent(bucket)}/${encodedObjectPath}`;
}

function formatTimestamp(value: string | null) {
  if (!value) return "Time unavailable";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "Time unavailable" : date.toLocaleString();
}

function formatSummary(value: string) {
  // Convert HTML break tags used in generated table cells into safe text separators.
  // Some stored agent summaries put every Markdown table row on one line. Split
  // the adjacent closing/opening pipes so GFM can recognize the table rows.
  return value
    .replace(/\\?<br\s*\/?\s*>/gi, " · ")
    .replace(/\|\s+\|/g, "|\n|");
}
