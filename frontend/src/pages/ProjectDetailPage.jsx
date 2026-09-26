import React, { useCallback, useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { api } from "../api/client.js";
import { useAuth } from "../context/AuthContext.jsx";
import { canManageProjects, canChangePriority } from "../utils/roles.js";
import {
  PageHead,
  Card,
  Table,
  Empty,
  ErrorBox,
  Spinner,
  ProgressBar,
  PriorityBadge,
  ProjectStatusBadge,
  RiskBadge,
  TaskStatusBadge,
  Badge,
  Modal,
  Field,
  TextInput,
  Select,
  TextArea,
  KV,
  Timeline,
  faNumber,
  faDate,
  faDateTime,
  faAgo,
} from "../components/ui.jsx";
import JalaliDateField from "../components/JalaliDateField.jsx";
import {
  PROJECT_STATUS_LABELS,
  PRIORITY_LABELS,
  TASK_STATUS_LABELS,
  WORK_TYPE_LABELS,
  BLOCKER_CATEGORY_LABELS,
} from "../utils/labels.js";

export default function ProjectDetailPage() {
  const { id } = useParams();
  const { user } = useAuth();
  const role = user?.role;
  const canManage = canManageProjects(role);
  const canPriority = canChangePriority(role);

  const [project, setProject] = useState(null);
  const [error, setError] = useState("");
  const [tasks, setTasks] = useState(null);
  const [blockers, setBlockers] = useState(null);
  const [changes, setChanges] = useState(null);
  const [members, setMembers] = useState([]);
  const [taskFilter, setTaskFilter] = useState("");

  const [modal, setModal] = useState(null); // "priority" | "status" | "date"
  const [flash, setFlash] = useState("");

  const notify = (msg) => {
    setFlash(msg);
    setTimeout(() => setFlash(""), 2500);
  };

  const load = useCallback(() => {
    api
      .get(`/api/projects/${id}/`)
      .then(setProject)
      .catch((e) => setError(e.message));
    const params = new URLSearchParams({ project: id });
    if (taskFilter) params.set("status", taskFilter);
    api
      .list(`/api/tasks/?${params.toString()}`)
      .then(setTasks)
      .catch(() => setTasks([]));
    api
      .list(`/api/blockers/?project=${id}`)
      .then(setBlockers)
      .catch(() => setBlockers([]));
    api
      .list(`/api/priority-changes/?project=${id}`)
      .then(setChanges)
      .catch(() => setChanges([]));
  }, [id, taskFilter]);
  useEffect(load, [load]);

  useEffect(() => {
    api
      .list("/api/members/")
      .then(setMembers)
      .catch(() => {});
  }, []);

  const changePriority = async (new_priority, reason, impact) => {
    await api.post(`/api/projects/${id}/priority/`, {
      new_priority,
      reason,
      impact,
    });
    setModal(null);
    load();
    notify("اولویت با موفقیت تغییر کرد.");
  };

  const changeStatus = async (status, note) => {
    await api.post(`/api/projects/${id}/status/`, { status, note });
    setModal(null);
    load();
    notify("وضعیت پروژه به‌روزرسانی شد.");
  };

  const changeDate = async (expected_completion) => {
    await api.patch(`/api/projects/${id}/`, { expected_completion });
    setModal(null);
    load();
    notify("تاریخ اتمام به‌روزرسانی شد.");
  };

  const setProgress = async (value) => {
    try {
      await api.patch(`/api/projects/${id}/`, {
        progress_percent: Number(value),
      });
      load();
    } catch (e) {
      notify(e.message);
    }
  };

  const assignMember = async (memberId) => {
    await api.post(`/api/projects/${id}/assign/`, {
      member: memberId,
      is_lead: false,
    });
    load();
    notify("عضو به پروژه اضافه شد.");
  };

  const removeMember = async (memberId) => {
    await api.post(`/api/projects/${id}/remove/${memberId}/`);
    load();
    notify("عضو از پروژه حذف شد.");
  };

  const resolveBlocker = async (blockerId) => {
    await api.post(`/api/blockers/${blockerId}/resolve/`, { note: "" });
    load();
  };

  const addTask = async (title) => {
    await api.post("/api/tasks/create/", { project: Number(id), title });
    load();
  };

  if (error) return <ErrorBox>{error}</ErrorBox>;
  if (!project) return <Spinner />;

  const currentMemberIds = (project.project_members || [])
    .filter((pm) => pm.unassigned_at === null || pm.unassigned_at === undefined)
    .map((pm) => pm.member);

  const availableMembers = members.filter(
    (m) => !currentMemberIds.includes(m.id) && m.is_active,
  );

  return (
    <>
      <PageHead
        title={project.name}
        subtitle={`${project.team_name || ""} ${project.client ? "· " + project.client : ""}`}
        actions={
          <>
            <Link to="/projects" className="btn">
              ← فهرست پروژه‌ها
            </Link>
            {canPriority && (
              <button
                className="btn btn-primary"
                onClick={() => setModal("priority")}
              >
                🔀 تغییر اولویت
              </button>
            )}
            {canManage && (
              <>
                <button className="btn" onClick={() => setModal("status")}>
                  تغییر وضعیت
                </button>
                <button className="btn" onClick={() => setModal("date")}>
                  تغییر تاریخ اتمام
                </button>
              </>
            )}
          </>
        }
      />
      {flash && <div className="flash">{flash}</div>}

      <div className="grid grid-3">
        <Card title="مشخصات پروژه" style={{ gridColumn: "span 1" }}>
          <KV
            rows={[
              ["وضعیت", <ProjectStatusBadge key="s" status={project.status} />],
              ["اولویت", <PriorityBadge key="p" value={project.priority} />],
              ["ریسک", <RiskBadge key="r" status={project.risk_status} />],
              [
                "تاریخ شروع",
                project.start_date ? faDate(project.start_date) : "—",
              ],
              [
                "تاریخ اتمام مورد انتظار",
                project.expected_completion ? (
                  <span>
                    {faDate(project.expected_completion)}{" "}
                    {project.days_to_expected_completion != null && (
                      <Badge
                        color={
                          project.days_to_expected_completion < 0
                            ? "badge-red"
                            : project.days_to_expected_completion <= 14
                              ? "badge-orange"
                              : "badge-gray"
                        }
                      >
                        {project.days_to_expected_completion < 0
                          ? `${faNumber(-project.days_to_expected_completion)} روز گذشته`
                          : `${faNumber(project.days_to_expected_completion)} روز مانده`}
                      </Badge>
                    )}
                  </span>
                ) : (
                  "—"
                ),
              ],
              [
                "تاریخ اتمام واقعی",
                project.actual_completion
                  ? faDate(project.actual_completion)
                  : "—",
              ],
              ["مالک", project.owner_name || "—"],
              ["کلاینت", project.client || "—"],
            ]}
          />
          {project.description && (
            <p className="muted small" style={{ marginTop: 10 }}>
              {project.description}
            </p>
          )}
          <div className="mt">
            <div className="row-between mb">
              <span className="muted small">درصد پیشرفت</span>
              {role === "developer" ? (
                <input
                  type="number"
                  className="input"
                  style={{ width: 70 }}
                  min="0"
                  max="100"
                  defaultValue={project.progress_percent}
                  onBlur={(e) =>
                    e.target.value !== project.progress_percent &&
                    setProgress(e.target.value)
                  }
                />
              ) : (
                <b>{faNumber(project.progress_percent)}٪</b>
              )}
            </div>
            <ProgressBar value={project.progress_percent} />
          </div>
        </Card>

        <Card title="آمار وظایف">
          <KV
            rows={[
              ["کل وظایف", faNumber(project.task_stats?.total || 0)],
              ["انجام‌نشده", faNumber(project.task_stats?.todo || 0)],
              ["در حال انجام", faNumber(project.task_stats?.in_progress || 0)],
              ["مسدود", faNumber(project.task_stats?.blocked || 0)],
              ["انجام‌شده", faNumber(project.task_stats?.done || 0)],
              ["مانع باز", faNumber(project.open_blocker_count || 0)],
            ]}
          />
        </Card>

        <Card title={`اعضای پروژه (${currentMemberIds.length})`}>
          <div>
            {(project.project_members || [])
              .filter((pm) => !pm.unassigned_at)
              .map((pm) => (
                <div
                  className="row-between"
                  key={pm.id}
                  style={{
                    padding: "4px 0",
                    borderBottom: "1px solid #eef2f6",
                  }}
                >
                  <span>
                    {pm.member_name}
                    {pm.is_lead && (
                      <Badge color="badge-purple" style={{ marginRight: 6 }}>
                        مسئول
                      </Badge>
                    )}
                  </span>
                  {canManage && (
                    <button
                      className="btn btn-ghost btn-sm"
                      onClick={() => removeMember(pm.member)}
                    >
                      حذف
                    </button>
                  )}
                </div>
              ))}
          </div>
          {canManage && (
            <Select
              options={availableMembers.map((m) => [m.id, m.full_name])}
              placeholder="+ افزودن عضو"
              value=""
              onChange={(e) =>
                e.target.value && assignMember(Number(e.target.value))
              }
              style={{ marginTop: 10 }}
            />
          )}
        </Card>
      </div>

      <Card
        title="وظایف پروژه"
        tight
        actions={
          <Select
            options={Object.entries(TASK_STATUS_LABELS)}
            value={taskFilter}
            onChange={(e) => setTaskFilter(e.target.value)}
            placeholder="همه وضعیت‌ها"
            style={{ minWidth: 140 }}
          />
        }
      >
        {tasks === null ? (
          <Spinner />
        ) : tasks.length === 0 ? (
          <Empty>وظیفه‌ای یافت نشد.</Empty>
        ) : (
          <Table
            headers={[
              "وظیفه",
              "نوع",
              "اولویت",
              "مسئول",
              "وضعیت",
              "مهلت",
              "به‌روزرسانی",
            ]}
          >
            {tasks.map((t) => (
              <tr key={t.id}>
                <td>
                  <b>{t.title}</b>
                </td>
                <td className="muted small">
                  {WORK_TYPE_LABELS[t.work_type] || t.work_type}
                </td>
                <td>
                  <PriorityBadge value={t.priority} />
                </td>
                <td className="muted small">{t.assignee_name || "—"}</td>
                <td>
                  <TaskStatusBadge status={t.status} />
                </td>
                <td className="muted small">
                  {t.due_date ? faDate(t.due_date) : "—"}
                </td>
                <td className="muted small">{faAgo(t.updated_at)}</td>
              </tr>
            ))}
          </Table>
        )}
        <div style={{ padding: 10 }}>
          <QuickAddTask onAdd={addTask} disabled={!tasks} />
        </div>
      </Card>

      <div className="grid grid-2">
        <Card title={`موانع (${(blockers || []).length})`} tight>
          {blockers === null ? (
            <Spinner />
          ) : blockers.length === 0 ? (
            <Empty>مانعی ثبت نشده است.</Empty>
          ) : (
            <Table headers={["مانع", "دسته", "اولویت", "وضعیت", "صاحب", "عمل"]}>
              {blockers.map((b) => (
                <tr key={b.id}>
                  <td>
                    <b>{b.title}</b>
                    <div className="muted tiny">{faAgo(b.created_at)}</div>
                  </td>
                  <td className="muted small">
                    {BLOCKER_CATEGORY_LABELS[b.category] || b.category}
                  </td>
                  <td>
                    <PriorityBadge value={b.priority} />
                  </td>
                  <td>
                    <Badge
                      color={b.status === "open" ? "badge-red" : "badge-green"}
                    >
                      {b.status === "open" ? "باز" : "رفع‌شده"}
                    </Badge>
                  </td>
                  <td className="muted small">{b.owner_name || "—"}</td>
                  <td>
                    {b.status === "open" && (
                      <button
                        className="btn btn-sm"
                        onClick={() => resolveBlocker(b.id)}
                      >
                        رفع مانع
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </Table>
          )}
        </Card>

        <Card
          title="تاریخچه اولویت"
          tight
          actions={
            <Link to="/priority-history" className="btn btn-sm">
              سابقه تیم
            </Link>
          }
        >
          {changes === null ? (
            <Spinner />
          ) : changes.length === 0 ? (
            <Empty>تغییر اولویتی ثبت نشده است.</Empty>
          ) : (
            <div className="card-body">
              {changes.map((c) => (
                <div
                  key={c.id}
                  style={{
                    padding: "8px 0",
                    borderBottom: "1px solid #eef2f6",
                  }}
                >
                  <div className="row">
                    <PriorityBadge value={c.old_priority} />
                    <span className="muted">←</span>
                    <PriorityBadge value={c.new_priority} />
                    <span
                      className="muted small"
                      style={{ marginRight: "auto" }}
                    >
                      {faDateTime(c.created_at)}
                    </span>
                  </div>
                  <div className="small" style={{ marginTop: 4 }}>
                    <b>{c.changed_by_name || "سیستم"}</b>
                    {c.reason && <span className="muted"> — {c.reason}</span>}
                    {c.impact && (
                      <div className="muted tiny">اثر: {c.impact}</div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>

      <Card title="تاریخچه تغییرات پروژه">
        <Timeline items={project.status_history || []} />
      </Card>

      {modal === "priority" && (
        <PriorityModal
          current={project.priority}
          onConfirm={changePriority}
          onClose={() => setModal(null)}
        />
      )}
      {modal === "status" && (
        <StatusModal
          current={project.status}
          onConfirm={changeStatus}
          onClose={() => setModal(null)}
        />
      )}
      {modal === "date" && (
        <DateModal
          current={project.expected_completion}
          onConfirm={changeDate}
          onClose={() => setModal(null)}
        />
      )}
    </>
  );
}

function QuickAddTask({ onAdd, disabled }) {
  const [title, setTitle] = useState("");
  const [busy, setBusy] = useState(false);
  return (
    <form
      className="row"
      onSubmit={async (e) => {
        e.preventDefault();
        if (!title.trim()) return;
        setBusy(true);
        try {
          await onAdd(title.trim());
          setTitle("");
        } finally {
          setBusy(false);
        }
      }}
    >
      <input
        className="input grow"
        style={{ flex: 1 }}
        placeholder="ثبت سریع وظیفه جدید..."
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        disabled={disabled || busy}
      />
      <button
        className="btn btn-primary"
        type="submit"
        disabled={disabled || busy}
      >
        افزودن
      </button>
    </form>
  );
}

function PriorityModal({ current, onConfirm, onClose }) {
  const [new_priority, setNewPriority] = useState(
    PRIORITY_LABELS[current] ? current : "medium",
  );
  const [reason, setReason] = useState("");
  const [impact, setImpact] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  return (
    <Modal title="تغییر اولویت پروژه" onClose={onClose}>
      <p className="muted small">
        هر تغییر اولویت به‌صورت کامل ثبت می‌شود تا تصمیمات مدیریتی شفاف بمانند —
        نه برای سرزنش، بلکه برای درک مبادلات (Trade-off) بین پروژه‌ها.
      </p>
      <div className="form-grid">
        <Field label="اولویت فعلی">
          <input
            className="input"
            readOnly
            value={PRIORITY_LABELS[current] || current}
          />
        </Field>
        <Field label="اولویت جدید">
          <Select
            options={Object.entries(PRIORITY_LABELS)}
            value={new_priority}
            onChange={(e) => setNewPriority(e.target.value)}
          />
        </Field>
        <Field label="دلیل تغییر" full>
          <TextArea
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            placeholder="مثلاً: درخواست جدید معاونت، تغییر شرایط بازار..."
          />
        </Field>
        <Field label="اثر بر سایر کارها (اختیاری)" full>
          <TextArea
            value={impact}
            onChange={(e) => setImpact(e.target.value)}
            placeholder="مثلاً: توسعه‌دهنده‌ای از پروژه X منتقل می‌شود؛ پروژه Y دیرتر تحویل داده می‌شود."
          />
        </Field>
      </div>
      {error && (
        <div className="error-box" style={{ marginTop: 10 }}>
          {error}
        </div>
      )}
      <div className="form-actions">
        <button
          className="btn btn-primary"
          disabled={busy}
          onClick={async () => {
            setBusy(true);
            setError("");
            try {
              await onConfirm(new_priority, reason, impact);
            } catch (e) {
              setError(e.message);
              setBusy(false);
            }
          }}
        >
          ثبت تغییر اولویت
        </button>
        <button className="btn" onClick={onClose}>
          انصراف
        </button>
      </div>
    </Modal>
  );
}

function StatusModal({ current, onConfirm, onClose }) {
  const [status, setStatus] = useState("active");
  const [note, setNote] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  return (
    <Modal title="تغییر وضعیت پروژه" onClose={onClose}>
      <div className="form-grid">
        <Field label="وضعیت فعلی">
          <input
            className="input"
            readOnly
            value={PROJECT_STATUS_LABELS[current] || current}
          />
        </Field>
        <Field label="وضعیت جدید">
          <Select
            options={Object.entries(PROJECT_STATUS_LABELS)}
            value={status}
            onChange={(e) => setStatus(e.target.value)}
          />
        </Field>
        <Field label="توضیح (اختیاری)" full>
          <TextArea value={note} onChange={(e) => setNote(e.target.value)} />
        </Field>
      </div>
      {error && (
        <div className="error-box" style={{ marginTop: 10 }}>
          {error}
        </div>
      )}
      <div className="form-actions">
        <button
          className="btn btn-primary"
          disabled={busy}
          onClick={async () => {
            setBusy(true);
            setError("");
            try {
              await onConfirm(status, note);
            } catch (e) {
              setError(e.message);
              setBusy(false);
            }
          }}
        >
          ثبت تغییر
        </button>
        <button className="btn" onClick={onClose}>
          انصراف
        </button>
      </div>
    </Modal>
  );
}

function DateModal({ current, onConfirm, onClose }) {
  const [date, setDate] = useState(current || "");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  return (
    <Modal title="تغییر تاریخ اتمام مورد انتظار" onClose={onClose}>
      <Field label="تاریخ جدید (تقویم شمسی)">
        <JalaliDateField value={date} onChange={setDate} />
      </Field>
      {error && (
        <div className="error-box" style={{ marginTop: 10 }}>
          {error}
        </div>
      )}
      <div className="form-actions">
        <button
          className="btn btn-primary"
          disabled={busy}
          onClick={async () => {
            setBusy(true);
            setError("");
            try {
              await onConfirm(date || null);
            } catch (e) {
              setError(e.message);
              setBusy(false);
            }
          }}
        >
          ثبت
        </button>
        <button className="btn" onClick={onClose}>
          انصراف
        </button>
      </div>
    </Modal>
  );
}
