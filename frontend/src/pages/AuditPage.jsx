import React, { useCallback, useEffect, useState } from "react";
import { api } from "../api/client.js";
import {
  PageHead,
  Card,
  Table,
  Empty,
  ErrorBox,
  Spinner,
  Badge,
  faNumber,
  faDateTime,
} from "../components/ui.jsx";
import { AUDIT_ACTION_LABELS } from "../utils/labels.js";

const ACTION_OPTIONS = Object.entries(AUDIT_ACTION_LABELS).map(([v, l]) => [
  v,
  l,
]);

export default function AuditPage() {
  const [rows, setRows] = useState(null);
  const [error, setError] = useState("");
  const [action, setAction] = useState("");
  const [entityType, setEntityType] = useState("");
  const [search, setSearch] = useState("");

  const load = useCallback(() => {
    const p = new URLSearchParams();
    if (action) p.set("action", action);
    if (entityType) p.set("entity_type", entityType);
    if (search) p.set("search", search);
    api
      .list(`/api/audit/?${p.toString()}`)
      .then(setRows)
      .catch((e) => setError(e.message));
  }, [action, entityType, search]);
  useEffect(load, [load]);

  return (
    <>
      <PageHead
        title="گزارش وقایع (Audit)"
        subtitle="رکورد کامل وقایع عملیاتی مهم: چه کسی، چه چیزی را، چه زمانی تغییر داد."
      />

      <Card tight>
        <div className="filter-bar">
          <select
            className="input"
            value={action}
            onChange={(e) => setAction(e.target.value)}
            style={{ minWidth: 180 }}
          >
            <option value="">همه رویدادها</option>
            {ACTION_OPTIONS.map(([v, l]) => (
              <option key={v} value={v}>
                {l}
              </option>
            ))}
          </select>
          <select
            className="input"
            value={entityType}
            onChange={(e) => setEntityType(e.target.value)}
            style={{ minWidth: 150 }}
          >
            <option value="">همه اشیاء</option>
            <option value="project">پروژه</option>
            <option value="task">وظیفه</option>
            <option value="blocker">مانع</option>
            <option value="support">پشتیبانی</option>
            <option value="capacity">ظرفیت</option>
            <option value="incoming_work">کار ورودی</option>
          </select>
          <input
            className="input grow"
            placeholder="جستجو در عنوان یا یادداشت..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        {error && (
          <div className="card-body">
            <ErrorBox>{error}</ErrorBox>
          </div>
        )}
        {!rows && !error && <Spinner />}
        {rows &&
          (rows.length === 0 ? (
            <Empty>رویدادی مطابق فیلتر یافت نشد.</Empty>
          ) : (
            <Table
              headers={[
                "رویداد",
                "شیء",
                "کننده",
                "از",
                "به",
                "یادداشت",
                "زمان",
              ]}
            >
              {rows.map((a) => (
                <tr key={a.id}>
                  <td>
                    <Badge color="badge-blue">
                      {AUDIT_ACTION_LABELS[a.action] || a.action}
                    </Badge>
                  </td>
                  <td className="small">
                    <b>{a.entity_label || "—"}</b>
                    <div className="muted tiny">{a.entity_type}</div>
                  </td>
                  <td className="muted small">{a.actor_name || "سیستم"}</td>
                  <td className="muted small">{formatVal(a.old_value)}</td>
                  <td className="muted small">{formatVal(a.new_value)}</td>
                  <td className="muted small">{a.note || "—"}</td>
                  <td className="muted small">{faDateTime(a.created_at)}</td>
                </tr>
              ))}
            </Table>
          ))}
      </Card>
    </>
  );
}

function formatVal(v) {
  if (v == null || v === "") return "—";
  if (typeof v === "string") return v;
  try {
    return Object.entries(v)
      .map(([k, val]) => `${k}: ${val}`)
      .join("، ");
  } catch {
    return String(v);
  }
}
