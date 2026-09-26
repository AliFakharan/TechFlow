import React, { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client.js";
import {
  PageHead,
  Card,
  Table,
  Empty,
  ErrorBox,
  Spinner,
  StatRow,
  Stat,
  ProgressBar,
  PriorityBadge,
  ProjectStatusBadge,
  RiskBadge,
  BarRow,
  faNumber,
  faAgo,
} from "../components/ui.jsx";
import { PRIORITY_LABELS, BLOCKER_CATEGORY_LABELS } from "../utils/labels.js";

export default function DeputyDashboard() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  const load = useCallback(() => {
    api
      .get("/api/dashboard/?view=deputy")
      .then(setData)
      .catch((e) => setError(e.message));
  }, []);
  useEffect(load, [load]);

  if (error) return <ErrorBox>{error}</ErrorBox>;
  if (!data) return <Spinner />;

  const projects = data.active_projects || [];
  const atRisk = data.projects_at_risk || [];
  const blockers = data.important_blockers || [];
  const changes = data.priority_changes || [];
  const support = data.support_load || {};

  return (
    <>
      <PageHead
        title={`نمای مدیریتی — ${data.team_name}`}
        subtitle="دید کلان: پروژه‌ها، ریسک‌ها، بار پشتیبانی و تصمیمات اولویت‌بندی."
        actions={
          <>
            <Link to="/report" className="btn btn-primary">
              📈 گزارش هفتگی
            </Link>
            <Link to="/priority-history" className="btn">
              تاریخچه اولویت‌ها
            </Link>
          </>
        }
      />

      <StatRow>
        <Stat value={projects.length} label="پروژه‌های فعال" tone="blue" />
        <Stat value={atRisk.length} label="پروژه‌های پرریسک" tone="orange" />
        <Stat value={blockers.length} label="موانع مهم" tone="red" />
        <Stat
          value={support.open_total || 0}
          label="تیکت‌های پشتیبانی باز"
          tone="purple"
          sub={`+${faNumber(support.created_last_7_days || 0)} در ۷ روز اخیر`}
        />
        <Stat
          value={changes.length}
          label="تغییر اولویت (۱۴ روز)"
          tone="blue"
        />
      </StatRow>

      <div className="grid grid-2-1">
        <Card title="پروژه‌های فعال (بر اساس اولویت)" tight>
          {projects.length === 0 ? (
            <Empty>پروژه فعالی نیست.</Empty>
          ) : (
            <Table
              headers={["پروژه", "وضعیت", "اولویت", "ریسک", "پیشرفت", "مهلت"]}
            >
              {projects.map((p) => (
                <tr
                  key={p.id}
                  className="clickable"
                  onClick={() => (window.location = `/projects/${p.id}`)}
                >
                  <td>
                    <b>{p.name}</b>
                  </td>
                  <td>
                    <ProjectStatusBadge status={p.status} />
                  </td>
                  <td>
                    <PriorityBadge value={p.priority} />
                  </td>
                  <td>
                    <RiskBadge status={p.risk_status} />
                  </td>
                  <td style={{ minWidth: 90 }}>
                    <div className="row">
                      <ProgressBar value={p.progress_percent} />
                      <span className="small num">
                        {faNumber(p.progress_percent)}٪
                      </span>
                    </div>
                  </td>
                  <td className="muted small">
                    {p.days_to_expected_completion != null
                      ? `${faNumber(p.days_to_expected_completion)} روز`
                      : "—"}
                  </td>
                </tr>
              ))}
            </Table>
          )}
        </Card>

        <div>
          <Card title="پروژه‌های پرریسک" tight>
            <div className="card-body">
              {atRisk.length === 0 ? (
                <Empty>همه پروژه‌ها در مسیر هستند. ✓</Empty>
              ) : (
                atRisk.map((p) => (
                  <Link
                    key={p.id}
                    to={`/projects/${p.id}`}
                    className="row-between"
                    style={{
                      padding: "6px 0",
                      borderBottom: "1px solid #eef2f6",
                      textDecoration: "none",
                    }}
                  >
                    <span>
                      <RiskBadge status={p.risk_status} /> <b>{p.name}</b>
                    </span>
                    <span className="muted small">
                      {PRIORITY_LABELS[p.priority]} ·{" "}
                      {faNumber(p.progress_percent)}٪
                    </span>
                  </Link>
                ))
              )}
            </div>
          </Card>

          <Card title="ظرفیت تیم به تفکیک پروژه" tight>
            <div className="card-body">
              {(data.capacity_by_project || []).map((c) => (
                <BarRow
                  key={c.project_id || "support"}
                  label={c.label}
                  value={c.total_percent}
                  max={Math.max(400, c.total_percent)}
                />
              ))}
            </div>
          </Card>
        </div>
      </div>

      <div className="grid grid-2">
        <Card title={`موانع مهم (${blockers.length})`} tight>
          {blockers.length === 0 ? (
            <Empty>مانع مهمی باز نیست.</Empty>
          ) : (
            <Table headers={["مانع", "پروژه", "دسته", "صاحب", "سن"]}>
              {blockers.map((b) => (
                <tr
                  key={b.id}
                  className="clickable"
                  onClick={() => (window.location = "/blockers?open=1")}
                >
                  <td>
                    <b>{b.title}</b>
                  </td>
                  <td className="muted small">{b.project_name || "—"}</td>
                  <td className="muted small">
                    {BLOCKER_CATEGORY_LABELS[b.category] || b.category}
                  </td>
                  <td className="muted small">{b.owner_name || "—"}</td>
                  <td className="num">{faAgo(b.created_at)}</td>
                </tr>
              ))}
            </Table>
          )}
        </Card>

        <Card
          title={`تغییرات اولویت اخیر — ${changes.length}`}
          tight
          actions={
            <Link to="/priority-history" className="btn btn-sm">
              همه
            </Link>
          }
        >
          {changes.length === 0 ? (
            <Empty>تغییر اولویتی ثبت نشده.</Empty>
          ) : (
            <Table headers={["پروژه", "اولویت", "تغییردهنده", "دلیل / اثر"]}>
              {changes.map((c) => (
                <tr
                  key={c.id}
                  className="clickable"
                  onClick={() =>
                    (window.location = `/projects/${c.project_id}`)
                  }
                >
                  <td>
                    <b>{c.project_name}</b>
                  </td>
                  <td>
                    <PriorityBadge value={c.old_priority} />
                    <span className="muted small"> ← </span>
                    <PriorityBadge value={c.new_priority} />
                  </td>
                  <td className="muted small">{c.changed_by || "—"}</td>
                  <td className="muted small">
                    {c.reason || "—"}
                    {c.impact && <div className="tiny">اثر: {c.impact}</div>}
                  </td>
                </tr>
              ))}
            </Table>
          )}
        </Card>
      </div>
    </>
  );
}
