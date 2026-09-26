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
  faDate,
  faDateTime,
} from "../components/ui.jsx";
import {
  WORK_TYPE_LABELS,
  BLOCKER_CATEGORY_LABELS,
  PRIORITY_LABELS,
} from "../utils/labels.js";

export default function WeeklyReportPage() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  const load = useCallback(() => {
    api
      .get("/api/reports/weekly/")
      .then(setData)
      .catch((e) => setError(e.message));
  }, []);
  useEffect(load, [load]);

  if (error) return <ErrorBox>{error}</ErrorBox>;
  if (!data) return <Spinner />;

  const s = data.summary || {};

  return (
    <>
      <PageHead
        title="گزارش هفتگی تیم"
        subtitle={`دوره‌ی گزارش: ${faDate(data.period?.from)} تا ${faDate(data.period?.to)} — برای مدیران و معاونت`}
        actions={
          <button className="btn" onClick={() => window.print()}>
            🖨 چاپ / PDF
          </button>
        }
      />

      <StatRow>
        <Stat
          value={s.active_projects || 0}
          label="پروژه‌های فعال"
          tone="blue"
        />
        <Stat
          value={s.at_risk_projects || 0}
          label="پروژه‌های در معرض ریسک"
          tone="orange"
        />
        <Stat
          value={s.blocked_projects || 0}
          label="پروژه‌های مسدود"
          tone="red"
        />
        <Stat
          value={data.work_completed?.total || 0}
          label="کارهای تکمیل‌شده این هفته"
          tone="green"
        />
        <Stat value={s.open_blockers || 0} label="موانع باز" tone="red" />
        <Stat
          value={s.open_support_tickets || 0}
          label="تیکت‌های پشتیبانی باز"
          tone="purple"
        />
      </StatRow>

      <div className="grid grid-2-1">
        <Card title="وضعیت پروژه‌های فعال" tight>
          {data.active_projects?.length === 0 ? (
            <Empty>پروژه فعالی نیست.</Empty>
          ) : (
            <Table
              headers={["پروژه", "وضعیت", "اولویت", "ریسک", "پیشرفت", "مهلت"]}
            >
              {data.active_projects.map((p) => (
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
                  <td style={{ minWidth: 100 }}>
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
          <Card title="کارهای تکمیل‌شده این هفته به تفکیک نوع">
            <div>
              {Object.entries(data.work_completed?.by_type || {}).map(
                ([type, count]) => (
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
                ),
              )}
              {Object.keys(data.work_completed?.by_type || {}).length === 0 && (
                <Empty>کار تکمیل‌شده‌ای ثبت نشده.</Empty>
              )}
            </div>
          </Card>
          <Card title="تغییرات اولویت این هفته">
            {data.priority_changes?.length === 0 ? (
              <Empty>تغییر اولویتی ثبت نشده.</Empty>
            ) : (
              data.priority_changes.map((c) => (
                <div
                  key={c.id}
                  style={{
                    padding: "6px 0",
                    borderBottom: "1px solid #eef2f6",
                    fontSize: 12.5,
                  }}
                >
                  <b>{c.project_name}</b>: {PRIORITY_LABELS[c.old_priority]} ←{" "}
                  {PRIORITY_LABELS[c.new_priority]}
                  <div className="muted small">
                    {c.changed_by || "—"}
                    {c.reason && ` — ${c.reason}`}
                  </div>
                </div>
              ))
            )}
          </Card>
        </div>
      </div>

      <div className="grid grid-2">
        <Card title={`موانع باز (${data.current_blockers?.length || 0})`} tight>
          {data.current_blockers?.length === 0 ? (
            <Empty>مانع باز نیست.</Empty>
          ) : (
            <Table headers={["مانع", "پروژه", "دسته", "صاحب"]}>
              {data.current_blockers.map((b) => (
                <tr key={b.id}>
                  <td>
                    <b>{b.title}</b>
                  </td>
                  <td className="muted small">{b.project_name || "—"}</td>
                  <td className="muted small">
                    {BLOCKER_CATEGORY_LABELS[b.category] || b.category}
                  </td>
                  <td className="muted small">{b.owner_name || "—"}</td>
                </tr>
              ))}
            </Table>
          )}
        </Card>

        <div>
          <Card title="بار پشتیبانی">
            <KVInline
              rows={[
                ["تیکت‌های باز", data.support?.open_total],
                ["تیکت‌های جدید (۷ روز)", data.support?.created_last_7_days],
                ["تیکت‌های حل‌شده (۷ روز)", data.support?.resolved_last_7_days],
              ]}
            />
            <div style={{ marginTop: 10 }}>
              {(data.support?.by_project || []).map((p) => (
                <div
                  className="row-between"
                  key={p.project_id}
                  style={{ padding: "3px 0", fontSize: 12.5 }}
                >
                  <span className="muted">{p.project_name}</span>
                  <b>{faNumber(p.open_count)} باز</b>
                </div>
              ))}
            </div>
          </Card>
          <Card title="توزیع ظرفیت به تفکیک پروژه">
            {(data.capacity_distribution || []).length === 0 ? (
              <Empty>تخصیصی ثبت نشده.</Empty>
            ) : (
              data.capacity_distribution.map((c) => (
                <BarRow
                  key={c.project_id || "support"}
                  label={c.label}
                  value={c.total_percent}
                  max={Math.max(400, c.total_percent)}
                />
              ))
            )}
          </Card>
        </div>
      </div>

      <Card
        title={`تفصیل کارهای تکمیل‌شده (${data.work_completed?.total || 0})`}
        tight
      >
        {data.work_completed?.items?.length === 0 ? (
          <Empty>موردی نیست.</Empty>
        ) : (
          <Table headers={["کار", "نوع", "پروژه", "مسئول", "تاریخ تکمیل"]}>
            {data.work_completed.items.map((t) => (
              <tr key={t.id}>
                <td>
                  <b>{t.title}</b>
                </td>
                <td className="muted small">
                  {WORK_TYPE_LABELS[t.work_type] || t.work_type}
                </td>
                <td className="muted small">{t.project_name}</td>
                <td className="muted small">{t.assignee_name || "—"}</td>
                <td className="muted small">{faDateTime(t.completed_at)}</td>
              </tr>
            ))}
          </Table>
        )}
      </Card>
    </>
  );
}

function KVInline({ rows }) {
  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "1fr auto",
        rowGap: 6,
        fontSize: 12.5,
      }}
    >
      {rows.map(([k, v], i) => (
        <React.Fragment key={i}>
          <span className="muted">{k}</span>
          <b>{v == null ? "—" : faNumber(v)}</b>
        </React.Fragment>
      ))}
    </div>
  );
}
