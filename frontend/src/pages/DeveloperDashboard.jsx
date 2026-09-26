import React, { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client.js";
import { useAuth } from "../context/AuthContext.jsx";
import {
  PageHead,
  Card,
  Stat,
  StatRow,
  Table,
  Empty,
  ErrorBox,
  Spinner,
  TaskStatusBadge,
  PriorityBadge,
  Badge,
  BarRow,
  faDate,
  faAgo,
  faNumber,
} from "../components/ui.jsx";
import {
  WORK_TYPE_LABELS,
  BLOCKER_CATEGORY_LABELS,
  STATUS_COLORS,
} from "../utils/labels.js";

export default function DeveloperDashboard() {
  const { user } = useAuth();
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState("");

  const load = useCallback(() => {
    api
      .get("/api/dashboard/?view=developer")
      .then(setData)
      .catch((e) => setError(e.message));
  }, []);
  useEffect(load, [load]);

  const quickStatus = async (id, status) => {
    setBusy(`${id}:${status}`);
    try {
      await api.post(`/api/tasks/${id}/status/`, { status });
      load();
    } finally {
      setBusy("");
    }
  };

  const resolveBlocker = async (id) => {
    setBusy(`b${id}`);
    try {
      await api.post(`/api/blockers/${id}/resolve/`, { note: "" });
      load();
    } finally {
      setBusy("");
    }
  };

  const closeSupport = async (id) => {
    setBusy(`s${id}`);
    try {
      await api.post(`/api/support/${id}/status/`, { status: "resolved" });
      load();
    } finally {
      setBusy("");
    }
  };

  if (error) return <ErrorBox>{error}</ErrorBox>;
  if (!data) return <Spinner />;

  const byStatus = data.my_tasks_by_status || {};

  return (
    <>
      <PageHead
        title={`سلام، ${data.member.full_name} 👋`}
        subtitle="این کارهایی است که همین حالا روی دوش شماست."
        actions={
          <>
            <Link to="/blockers" className="btn btn-primary">
              🚧 ثبت مانع
            </Link>
            <Link to="/tasks?mine=1" className="btn">
              تمام وظایف من
            </Link>
          </>
        }
      />

      <StatRow>
        <Stat
          value={byStatus.in_progress || 0}
          label="در حال انجام"
          tone="blue"
          to="/tasks?mine=1&status=in_progress"
        />
        <Stat
          value={(byStatus.todo || 0) + (byStatus.blocked || 0)}
          label="در انتظار / مسدود"
          tone="orange"
          to="/tasks?mine=1"
        />
        <Stat
          value={data.my_blockers.length}
          label="موانع باز من"
          tone="red"
          to="/blockers?mine=1&open=1"
        />
        <Stat
          value={data.my_support.length}
          label="تیکت‌های باز من"
          tone="purple"
          to="/support?mine=1&open=1"
        />
        <Stat
          value={`${faNumber(data.my_workload.total_percent)}٪`}
          label="تخصیص ظرفیت من"
          tone={data.my_workload.total_percent > 100 ? "red" : "green"}
          to="/capacity?focus=self"
        />
      </StatRow>

      <div className="grid grid-2-1">
        <Card title="وظایف من" tight>
          {data.my_tasks.length === 0 ? (
            <Empty>وظیفه باز ندارید. 🎉</Empty>
          ) : (
            <Table
              headers={[
                "وظیفه",
                "پروژه",
                "نوع",
                "اولویت",
                "وضعیت",
                "مهلت",
                "عمل سریع",
              ]}
            >
              {data.my_tasks.map((t) => (
                <tr
                  key={t.id}
                  className="clickable"
                  onClick={() => (window.location = `/tasks?mine=1`)}
                >
                  <td>
                    <b>{t.title}</b>
                  </td>
                  <td className="muted">{t.project_name}</td>
                  <td className="muted small">
                    {WORK_TYPE_LABELS[t.work_type] || t.work_type}
                  </td>
                  <td>
                    <PriorityBadge value={t.priority} />
                  </td>
                  <td>
                    <TaskStatusBadge status={t.status} />
                  </td>
                  <td className="muted small">
                    {t.due_date ? faDate(t.due_date) : "—"}
                  </td>
                  <td>
                    <div className="row">
                      {t.status === "todo" && (
                        <button
                          className="btn btn-sm"
                          onClick={(e) => {
                            e.stopPropagation();
                            quickStatus(t.id, "in_progress");
                          }}
                          disabled={busy === `${t.id}:in_progress`}
                        >
                          شروع
                        </button>
                      )}
                      {t.status !== "done" && (
                        <button
                          className="btn btn-sm"
                          style={{
                            borderColor: "var(--ok)",
                            color: "var(--ok)",
                          }}
                          onClick={(e) => {
                            e.stopPropagation();
                            quickStatus(t.id, "done");
                          }}
                          disabled={busy === `${t.id}:done`}
                        >
                          ✓ انجام شد
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </Table>
          )}
        </Card>

        <div>
          <Card title="ظرفیت من" tight>
            <div className="card-body">
              {data.my_workload.allocations.length === 0 ? (
                <Empty>تخصیصی ثبت نشده است.</Empty>
              ) : (
                data.my_workload.allocations.map((a) => (
                  <BarRow
                    key={`${a.project_id || "support"}`}
                    label={a.project_name}
                    value={a.percent}
                  />
                ))
              )}
              <div className="row-between mt">
                <span className="muted small">مجموع تخصیص</span>
                <b
                  style={{
                    color:
                      data.my_workload.total_percent > 100
                        ? "var(--danger)"
                        : "var(--text)",
                  }}
                >
                  {faNumber(data.my_workload.total_percent)}٪
                  {data.my_workload.total_percent > 100 && " ⚠ بیش از ظرفیت"}
                </b>
              </div>
              <Link
                to="/capacity?focus=self"
                className="btn btn-sm"
                style={{ marginTop: 10 }}
              >
                ویرایش تخصیص‌ها
              </Link>
            </div>
          </Card>

          <Card title="پروژه‌هایی که در آنم">
            {data.my_projects.length === 0 ? (
              <Empty>به پروژه‌ای متصل نیستید.</Empty>
            ) : (
              data.my_projects.map((p) => (
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
                    <b>{p.name}</b>
                    <span className="muted small">
                      {" "}
                      · {faNumber(p.progress_percent)}٪
                    </span>
                  </span>
                  <Badge color={STATUS_COLORS[p.status] || "badge-gray"}>
                    {p.status}
                  </Badge>
                </Link>
              ))
            )}
          </Card>
        </div>
      </div>

      <div className="grid grid-2">
        <Card title={`موانع باز من (${data.my_blockers.length})`} tight>
          {data.my_blockers.length === 0 ? (
            <Empty>مانع باز ندارید.</Empty>
          ) : (
            <Table headers={["مانع", "دسته", "پروژه", "سن", "عمل"]}>
              {data.my_blockers.map((b) => (
                <tr key={b.id}>
                  <td>
                    <b>{b.title}</b>
                  </td>
                  <td className="muted small">
                    {BLOCKER_CATEGORY_LABELS[b.category] || b.category}
                  </td>
                  <td className="muted small">{b.project_name || "—"}</td>
                  <td className="num">{faAgo(b.created_at)}</td>
                  <td>
                    <button
                      className="btn btn-sm"
                      onClick={() => resolveBlocker(b.id)}
                      disabled={busy === `b${b.id}`}
                    >
                      رفع مانع
                    </button>
                  </td>
                </tr>
              ))}
            </Table>
          )}
        </Card>

        <Card title={`تیکت‌های پشتیبانی من (${data.my_support.length})`} tight>
          {data.my_support.length === 0 ? (
            <Empty>تیکت باز ندارید.</Empty>
          ) : (
            <Table headers={["تیکت", "پروژه", "شدت", "وضعیت", "عمل"]}>
              {data.my_support.map((t) => (
                <tr key={t.id}>
                  <td>
                    <b>{t.title}</b>
                  </td>
                  <td className="muted small">{t.project_name || "عمومی"}</td>
                  <td>
                    <PriorityBadge value={t.severity} />
                  </td>
                  <td>
                    <Badge color={STATUS_COLORS[t.status] || "badge-gray"}>
                      {t.status}
                    </Badge>
                  </td>
                  <td>
                    <button
                      className="btn btn-sm"
                      style={{ borderColor: "var(--ok)", color: "var(--ok)" }}
                      onClick={() => closeSupport(t.id)}
                      disabled={busy === `s${t.id}`}
                    >
                      ✓ حل شد
                    </button>
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
