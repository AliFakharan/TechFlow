import React from "react";
import { Link } from "react-router-dom";
import {
  StatRow,
  Stat,
  Card,
  Table,
  Empty,
  ProgressBar,
  PriorityBadge,
  ProjectStatusBadge,
  RiskBadge,
  Badge,
  BarRow,
  faNumber,
  faDate,
  faAgo,
  faDateTime,
} from "../components/ui.jsx";
import {
  WORK_TYPE_LABELS,
  BLOCKER_CATEGORY_LABELS,
  PRIORITY_LABELS,
  AUDIT_ACTION_LABELS,
} from "../utils/labels.js";

export default function TeamDashboardBody({ data, showEvents = false }) {
  const projects = data.projects || [];
  const atRisk = data.at_risk_projects || [];
  const blocked = data.blocked_projects || [];
  const deadline = data.deadline_soon_projects || [];
  const stale = data.stale_projects || [];
  const overdue = data.open_blockers || [];
  const aging = data.aging_blockers || [];
  const overloaded = data.overloaded_developers || [];
  const underloaded = data.underloaded_developers || [];
  const changes = data.priority_changes || [];
  const events = data.recent_events || [];

  return (
    <>
      <StatRow>
        <Stat
          value={projects.length}
          label="پروژه‌های فعال"
          tone="blue"
          to="/projects"
        />
        <Stat
          value={atRisk.length}
          label="پروژه در معرض ریسک"
          tone="orange"
          to="/projects?risk_status=at_risk"
        />
        <Stat
          value={blocked.length}
          label="پروژه مسدود"
          tone="red"
          to="/projects?risk_status=blocked"
        />
        <Stat
          value={deadline.length}
          label="نزدیک به مهلت (۱۴ روز)"
          tone="purple"
          to="/projects"
        />
        <Stat
          value={overdue.length}
          label="موانع باز"
          tone="red"
          to="/blockers?open=1"
        />
        <Stat
          value={data.support?.open_total || 0}
          label="تیکت‌های پشتیبانی باز"
          tone="purple"
          to="/support?open=1"
        />
      </StatRow>

      {/* Attention band */}
      {(atRisk.length > 0 ||
        blocked.length > 0 ||
        deadline.length > 0 ||
        stale.length > 0) && (
        <div className="card" style={{ borderRight: "3px solid var(--warn)" }}>
          <div className="card-head">
            <div className="card-title">نیاز به توجه</div>
            <div className="muted small">
              سیگنال‌های شفاف و قابل‌پایگیری؛ هرکدام دلیل مشخصی دارد.
            </div>
          </div>
          <div className="card-body">
            {atRisk.map((p) => (
              <Link
                to={`/projects/${p.id}`}
                key={`ar-${p.id}`}
                className="row-between"
                style={{
                  padding: "5px 0",
                  borderBottom: "1px solid #eef2f6",
                  textDecoration: "none",
                }}
              >
                <span>
                  <RiskBadge status={p.risk_status} /> <b>{p.name}</b>
                  <span className="muted small">
                    {" "}
                    · {PRIORITY_LABELS[p.priority]}
                  </span>
                </span>
                <span className="muted small">
                  {p.days_to_expected_completion != null &&
                    `مهلت: ${faNumber(p.days_to_expected_completion)} روز`}
                  {p.open_blocker_count > 0 &&
                    ` · ${faNumber(p.open_blocker_count)} مانع باز`}
                </span>
              </Link>
            ))}
            {blocked.map((p) => (
              <Link
                to={`/projects/${p.id}`}
                key={`bl-${p.id}`}
                className="row-between"
                style={{
                  padding: "5px 0",
                  borderBottom: "1px solid #eef2f6",
                  textDecoration: "none",
                }}
              >
                <span>
                  <RiskBadge status={p.risk_status} /> <b>{p.name}</b>
                </span>
                <span className="muted small">
                  {PRIORITY_LABELS[p.priority]}
                </span>
              </Link>
            ))}
            {deadline
              .filter((p) => p.risk_status === "on_track")
              .map((p) => (
                <Link
                  to={`/projects/${p.id}`}
                  key={`dl-${p.id}`}
                  className="row-between"
                  style={{
                    padding: "5px 0",
                    borderBottom: "1px solid #eef2f6",
                    textDecoration: "none",
                  }}
                >
                  <span>
                    <Badge color="badge-purple">مهلت نزدیک</Badge>{" "}
                    <b>{p.name}</b>
                  </span>
                  <span className="muted small">
                    {p.days_to_expected_completion != null &&
                      `${faNumber(p.days_to_expected_completion)} روز مانده · ${faNumber(p.progress_percent)}٪ پیشرفت`}
                  </span>
                </Link>
              ))}
            {stale.map((p) => (
              <div
                key={`st-${p.id}`}
                className="row-between"
                style={{ padding: "5px 0", borderBottom: "1px solid #eef2f6" }}
              >
                <span>
                  <Badge color="badge-orange">به‌روزرسانی ضعیف</Badge>{" "}
                  <b>{p.name}</b>
                </span>
                <span className="muted small">
                  {faNumber(p.idle_days)} روز بی‌تغییری
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="grid grid-2-1">
        <Card title="پروژه‌های فعال (بر اساس اولویت)" tight>
          {projects.length === 0 ? (
            <Empty>پروژه فعالی وجود ندارد.</Empty>
          ) : (
            <Table
              headers={[
                "پروژه",
                "وضعیت",
                "اولویت",
                "ریسک",
                "پیشرفت",
                "مهلت",
                "مانع باز",
                "اعضا",
              ]}
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
                  <td className="num">{faNumber(p.open_blocker_count)}</td>
                  <td className="num">{faNumber(p.member_count)}</td>
                </tr>
              ))}
            </Table>
          )}
        </Card>

        <div>
          <Card title="توزیع کار (وظایف فعال)" tight>
            <div className="card-body">
              {Object.keys(data.work_distribution || {}).length === 0 ? (
                <Empty>داده‌ای نیست.</Empty>
              ) : (
                Object.entries(data.work_distribution).map(([type, count]) => (
                  <div
                    className="row-between"
                    key={type}
                    style={{ padding: "4px 0" }}
                  >
                    <span className="muted">
                      {WORK_TYPE_LABELS[type] || type}
                    </span>
                    <b>{faNumber(count)}</b>
                  </div>
                ))
              )}
            </div>
          </Card>

          <Card title="ظرفیت تیم به تفکیک پروژه" tight>
            <div className="card-body">
              {(data.capacity_by_project || []).length === 0 ? (
                <Empty>تخصیصی ثبت نشده.</Empty>
              ) : (
                data.capacity_by_project.map((c) => (
                  <BarRow
                    key={c.project_id || "support"}
                    label={c.label}
                    value={c.total_percent}
                    max={Math.max(400, c.total_percent)}
                  />
                ))
              )}
            </div>
          </Card>
        </div>
      </div>

      <div className="grid grid-2">
        <Card title={`موانع باز (${overdue.length})`} tight>
          {overdue.length === 0 ? (
            <Empty>مانع باز نیست.</Empty>
          ) : (
            <Table headers={["مانع", "دسته", "پروژه", "صاحب", "سن"]}>
              {overdue.slice(0, 12).map((b) => (
                <tr
                  key={b.id}
                  className="clickable"
                  onClick={() => (window.location = `/blockers?open=1`)}
                >
                  <td>
                    <b>{b.title}</b>
                    {b.priority === "critical" && (
                      <Badge color="badge-red" style={{ marginLeft: 6 }}>
                        بحرانی
                      </Badge>
                    )}
                  </td>
                  <td className="muted small">
                    {BLOCKER_CATEGORY_LABELS[b.category] || b.category}
                  </td>
                  <td className="muted small">{b.project_name || "—"}</td>
                  <td className="muted small">{b.owner_name || "—"}</td>
                  <td className="num">{faAgo(b.created_at)}</td>
                </tr>
              ))}
            </Table>
          )}
        </Card>

        <Card
          title={`تغییرات اولویت (۱۴ روز) — ${changes.length}`}
          tight
          actions={
            <Link to="/priority-history" className="btn btn-sm">
              تاریخچه کامل
            </Link>
          }
        >
          {changes.length === 0 ? (
            <Empty>تغییر اولویتی ثبت نشده.</Empty>
          ) : (
            <Table headers={["پروژه", "اولویت", "تغییردهنده", "دلیل"]}>
              {changes.slice(0, 8).map((c) => (
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
                  <td className="muted small">{c.reason || "—"}</td>
                </tr>
              ))}
            </Table>
          )}
        </Card>
      </div>

      <div className="grid grid-2">
        <Card title="بار ظرفیت اعضا (توسعه‌دهنده‌ها)" tight>
          <div className="card-body">
            {data.members?.map((m) => (
              <BarRow
                key={m.member_id}
                label={m.full_name}
                value={m.allocated_percent}
                max={140}
              />
            ))}
            {overloaded.length > 0 && (
              <div className="error-box" style={{ marginTop: 10 }}>
                ⚠ بیش‌تخصیص: {overloaded.map((o) => o.full_name).join("، ")}
              </div>
            )}
            {underloaded.length > 0 && (
              <div className="muted small" style={{ marginTop: 8 }}>
                کم‌تخصیص: {underloaded.map((o) => o.full_name).join("، ")}
              </div>
            )}
          </div>
        </Card>

        <div>
          <Card
            title={`کارهای ورودی (${data.incoming?.open_count || 0} باز)`}
            tight
          >
            <div className="card-body">
              {(data.incoming?.recent || []).length === 0 ? (
                <Empty>کار ورودی باز نیست.</Empty>
              ) : (
                data.incoming.recent.map((w) => (
                  <div
                    className="row-between"
                    key={w.id}
                    style={{
                      padding: "4px 0",
                      borderBottom: "1px solid #eef2f6",
                    }}
                  >
                    <span>
                      <b>{w.title}</b>
                      <span className="muted small"> · {w.source || ""}</span>
                    </span>
                    <span className="muted small">{faAgo(w.created_at)}</span>
                  </div>
                ))
              )}
            </div>
          </Card>

          {showEvents && (
            <Card title="رویدادهای اخیر عملیاتی" tight>
              <div className="card-body">
                {events.length === 0 ? (
                  <Empty>رویدادی ثبت نشده.</Empty>
                ) : (
                  events.slice(0, 12).map((ev) => (
                    <div
                      key={ev.id}
                      style={{
                        padding: "5px 0",
                        borderBottom: "1px solid #eef2f6",
                        fontSize: 12.5,
                      }}
                    >
                      <b>{AUDIT_ACTION_LABELS[ev.action] || ev.action}</b>
                      {ev.entity_label && (
                        <span className="muted"> — {ev.entity_label}</span>
                      )}
                      <div className="muted small">
                        {ev.actor_name || "سیستم"} · {faDateTime(ev.created_at)}
                      </div>
                    </div>
                  ))
                )}
              </div>
            </Card>
          )}
        </div>
      </div>
    </>
  );
}
