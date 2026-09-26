import React, { useEffect } from "react";
import { faNumber, faDate, faDateTime, faAgo } from "../utils/fa.js";
import {
  PRIORITY_COLORS,
  STATUS_COLORS,
  PRIORITY_LABELS,
  PROJECT_STATUS_LABELS,
} from "../utils/labels.js";

/* ---------------- Status / value badges ---------------- */

export function Badge({ color = "badge-gray", children, ...rest }) {
  return (
    <span className={`badge ${color}`} {...rest}>
      {children}
    </span>
  );
}

/** Project risk badge (on_track / at_risk / blocked). */
export function RiskBadge({ status }) {
  const map = {
    on_track: ["badge-green", "در مسیر"],
    at_risk: ["badge-orange", "در معرض ریسک"],
    blocked: ["badge-red", "مسدود"],
  };
  const [c, label] = map[status] || ["badge-gray", status || "—"];
  return <Badge color={c}>{label}</Badge>;
}

/** Project status badge. */
export function ProjectStatusBadge({ status }) {
  return (
    <Badge color={STATUS_COLORS[status] || "badge-gray"}>
      {PROJECT_STATUS_LABELS[status] || status || "—"}
    </Badge>
  );
}

/** Task status badge. */
export function TaskStatusBadge({ status }) {
  const map = {
    todo: ["badge-gray", "انجام‌نشده"],
    in_progress: ["badge-blue", "در حال انجام"],
    blocked: ["badge-red", "مسدود"],
    done: ["badge-green", "انجام‌شده"],
  };
  const [c, label] = map[status] || ["badge-gray", status || "—"];
  return <Badge color={c}>{label}</Badge>;
}

export function PriorityBadge({ value }) {
  return (
    <Badge color={PRIORITY_COLORS[value] || "badge-gray"}>
      {PRIORITY_LABELS[value] || value || "—"}
    </Badge>
  );
}

export function ProgressBar({ value, warnAt = 60, className = "" }) {
  const v = Math.max(0, Math.min(100, value || 0));
  const cls = v < 30 ? "danger" : v < warnAt ? "warn" : "ok";
  return (
    <div className="progress" title={`${faNumber(v)}٪`}>
      <div className={`progress-fill ${cls}`} style={{ width: `${v}%` }} />
    </div>
  );
}

/** Horizontal bar row: label + bar + value (percent). */
export function BarRow({
  label,
  value,
  max = 200,
  dangerAt = 110,
  warnAt = 90,
}) {
  const pct = max ? Math.min(100, Math.round((value / max) * 100)) : 0;
  const cls = value > dangerAt ? "danger" : value >= warnAt ? "warn" : "";
  return (
    <div className="bar-row">
      <div className="muted">{label}</div>
      <div className="bar-track">
        <div className={`bar-fill ${cls}`} style={{ width: `${pct}%` }} />
      </div>
      <div className="bar-val">
        {faNumber(value)}٪{value > 100 ? " ⚠" : ""}
      </div>
    </div>
  );
}

/* ---------------- Page scaffolding ---------------- */

export function PageHead({ title, subtitle, actions }) {
  return (
    <div className="page-head">
      <div>
        <h1>{title}</h1>
        {subtitle && <div className="small muted mt-0">{subtitle}</div>}
      </div>
      {actions && <div className="row wrap">{actions}</div>}
    </div>
  );
}

export function Card({ title, actions, children, tight = false, body = true }) {
  return (
    <div className="card">
      {(title || actions) && (
        <div className="card-head">
          <div className="card-title">{title}</div>
          {actions && <div className="row">{actions}</div>}
        </div>
      )}
      {body && (
        <div className={`card-body ${tight ? "tight" : ""}`}>{children}</div>
      )}
    </div>
  );
}

export function Stat({ value, label, sub, tone = "", to }) {
  const inner = (
    <>
      <div className="stat-value">
        {value === undefined || value === null ? "—" : faNumber(value)}
      </div>
      <div className="stat-label">{label}</div>
      {sub && <div className="stat-sub">{sub}</div>}
    </>
  );
  if (to) {
    return (
      <a
        className={`stat ${tone}`}
        style={{ textDecoration: "none", color: "inherit" }}
        href={to}
      >
        {inner}
      </a>
    );
  }
  return <div className={`stat ${tone}`}>{inner}</div>;
}

export function StatRow({ children }) {
  return <div className="stat-row">{children}</div>;
}

/* ---------------- Data display ---------------- */

export function Table({ headers, children, dense = false }) {
  return (
    <div style={{ overflowX: "auto" }}>
      <table className="table">
        <thead>
          <tr>
            {headers.map((h, i) => (
              <th key={i}>{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>{children}</tbody>
      </table>
    </div>
  );
}

export function Empty({ children = "موردی یافت نشد." }) {
  return <div className="empty">{children}</div>;
}

export function ErrorBox({ children }) {
  if (!children) return null;
  return <div className="error-box">{children}</div>;
}

export function Spinner({ label = "در حال بارگذاری..." }) {
  return <div className="spinner">{label}</div>;
}

export function KV({ rows }) {
  return (
    <dl className="kv">
      {rows.map(([k, v], i) => (
        <React.Fragment key={i}>
          <dt>{k}</dt>
          <dd>{v === null || v === undefined || v === "" ? "—" : v}</dd>
        </React.Fragment>
      ))}
    </dl>
  );
}

/* ---------------- Forms ---------------- */

export function Field({ label, hint, children, full = false, error }) {
  return (
    <div className="field" style={full ? { gridColumn: "1 / -1" } : undefined}>
      {label && <label>{label}</label>}
      {children}
      {error && (
        <div className="hint" style={{ color: "var(--danger)" }}>
          {error}
        </div>
      )}
      {hint && !error && <div className="hint">{hint}</div>}
    </div>
  );
}

export function TextInput(props) {
  return <input className="input" {...props} />;
}

export function TextArea(props) {
  return <textarea className="input" rows={3} {...props} />;
}

export function Select({
  options,
  value,
  onChange,
  placeholder = "انتخاب کنید...",
  ...rest
}) {
  return (
    <select className="input" value={value ?? ""} onChange={onChange} {...rest}>
      <option value="" disabled>
        {placeholder}
      </option>
      {options.map(([v, l]) => (
        <option key={v} value={v}>
          {l}
        </option>
      ))}
    </select>
  );
}

/** Options list builder: [[value, label], ...] */
export function choices(map) {
  return Object.entries(map);
}

/* ---------------- Modal ---------------- */

export function Modal({ title, onClose, children, wide = false, actions }) {
  useEffect(() => {
    const onKey = (e) => e.key === "Escape" && onClose?.();
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [onClose]);
  return (
    <div
      className="modal-backdrop"
      onMouseDown={(e) => e.target === e.currentTarget && onClose?.()}
    >
      <div className={`modal ${wide ? "modal-wide" : ""}`}>
        <div className="modal-head">
          <h3>{title}</h3>
          <button className="modal-x" onClick={onClose} type="button">
            ✕ بستن
          </button>
        </div>
        <div className="modal-body">{children}</div>
        {actions && (
          <div className="modal-body" style={{ paddingTop: 0 }}>
            {actions}
          </div>
        )}
      </div>
    </div>
  );
}

/* ---------------- Timeline (project status history) ---------------- */

const FIELD_LABELS = {
  status: "وضعیت",
  priority: "اولویت",
  expected_completion: "تاریخ اتمام",
  start_date: "تاریخ شروع",
  progress: "پیشرفت",
};

export function Timeline({ items }) {
  if (!items?.length) return <Empty>تاریخچه‌ای ثبت نشده است.</Empty>;
  return (
    <ul className="timeline">
      {items.map((it) => (
        <li key={it.id}>
          <span className="dot" />
          <div className="what">
            <b>{FIELD_LABELS[it.field] || it.field}</b>:
            <span className="muted"> {valueLabel(it.old_value)} → </span>
            {valueLabel(it.new_value)}
            {it.note && <span className="muted small"> — {it.note}</span>}
          </div>
          <div className="when">
            {it.changed_by_name && <b>{it.changed_by_name}</b>} ·{" "}
            {faDateTime(it.created_at)}
          </div>
        </li>
      ))}
    </ul>
  );
}

function valueLabel(v) {
  if (!v) return "—";
  const maps = {
    planned: "برنامه‌ریزی‌شده",
    active: "فعال",
    blocked: "مسدود",
    testing: "تست",
    bug_fixing: "رفع باگ",
    done: "انجام‌شده",
    paused: "توقف‌خورده",
    cancelled: "لغو‌شده",
    low: "کم",
    medium: "متوسط",
    high: "زیاد",
    critical: "بحرانی",
  };
  return maps[v] ?? v;
}

/* ---------------- Date helpers re-export ---------------- */

export { faNumber, faDate, faDateTime, faAgo };
