import React, { useCallback, useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { api } from "../api/client.js";
import { useAuth } from "../context/AuthContext.jsx";
import { isOps } from "../utils/roles.js";
import {
  PageHead,
  Card,
  Table,
  Empty,
  ErrorBox,
  Spinner,
  PriorityBadge,
  TaskStatusBadge,
  Modal,
  Field,
  TextInput,
  Select,
  TextArea,
  faNumber,
  faDate,
  faAgo,
} from "../components/ui.jsx";
import JalaliDateField from "../components/JalaliDateField.jsx";
import {
  TASK_STATUS_LABELS,
  WORK_TYPE_LABELS,
  PRIORITY_LABELS,
} from "../utils/labels.js";

const today = () => new Date().toISOString().slice(0, 10);

export default function TasksPage() {
  const { user } = useAuth();
  const [params, setParams] = useSearchParams();
  const role = user?.role;
  const ops = isOps(role);

  const [rows, setRows] = useState(null);
  const [error, setError] = useState("");
  const [q, setQ] = useState("");
  const [status, setStatus] = useState(params.get("status") || "");
  const [mine, setMine] = useState(params.get("mine") === "1");
  const [projects, setProjects] = useState([]);
  const [members, setMembers] = useState([]);
  const [showCreate, setShowCreate] = useState(false);
  const [flash, setFlash] = useState("");

  const notify = (msg) => {
    setFlash(msg);
    setTimeout(() => setFlash(""), 2500);
  };

  const load = useCallback(() => {
    const p = new URLSearchParams();
    if (status) p.set("status", status);
    if (mine) p.set("mine", "1");
    api
      .list(`/api/tasks/?${p.toString()}`)
      .then(setRows)
      .catch((e) => setError(e.message));
  }, [status, mine]);
  useEffect(load, [load]);

  useEffect(() => {
    api
      .list("/api/projects/")
      .then(setProjects)
      .catch(() => {});
    api
      .list("/api/members/")
      .then(setMembers)
      .catch(() => {});
  }, []);

  const quickStatus = async (id, newStatus) => {
    try {
      await api.post(`/api/tasks/${id}/status/`, { status: newStatus });
      notify("وضعیت به‌روزرسانی شد.");
      load();
    } catch (e) {
      notify(e.message);
    }
  };

  const setAssignee = async (id, memberId) => {
    try {
      await api.post(`/api/tasks/${id}/assign/`, {
        assignee: memberId ? Number(memberId) : null,
      });
      notify("مسئول به‌روزرسانی شد.");
      load();
    } catch (e) {
      notify(e.message);
    }
  };

  return (
    <>
      <PageHead
        title="وظایف"
        subtitle="کارهای تیم به تفکیک پروژه، نوع و وضعیت."
        actions={
          <button
            className="btn btn-primary"
            onClick={() => setShowCreate(true)}
          >
            + وظیفه جدید
          </button>
        }
      />
      {flash && <div className="flash">{flash}</div>}

      <Card tight>
        <div className="filter-bar">
          <Select
            options={Object.entries(TASK_STATUS_LABELS)}
            value={status}
            onChange={(e) => setStatus(e.target.value)}
            placeholder="همه وضعیت‌ها"
          />
          <label className="row" style={{ fontSize: 12.5 }}>
            <input
              type="checkbox"
              checked={mine}
              onChange={(e) => setMine(e.target.checked)}
            />
            فقط من
          </label>
          <span className="muted small grow" style={{ textAlign: "left" }}>
            {rows ? `${faNumber(rows.length)} وظیفه` : ""}
          </span>
        </div>
        {error && (
          <div className="card-body">
            <ErrorBox>{error}</ErrorBox>
          </div>
        )}
        {!rows && !error && <Spinner />}
        {rows &&
          (rows.length === 0 ? (
            <Empty>وظیفه‌ای یافت نشد.</Empty>
          ) : (
            <Table
              headers={[
                "وظیفه",
                "پروژه",
                "نوع",
                "اولویت",
                "مسئول",
                "وضعیت",
                "مهلت",
                "به‌روزرسانی",
                "عمل سریع",
              ]}
            >
              {rows.map((t) => (
                <tr key={t.id}>
                  <td>
                    <b>{t.title}</b>
                  </td>
                  <td className="muted small">{t.project_name}</td>
                  <td className="muted small">
                    {WORK_TYPE_LABELS[t.work_type] || t.work_type}
                  </td>
                  <td>
                    <PriorityBadge value={t.priority} />
                  </td>
                  <td>
                    {ops ? (
                      <select
                        className="input"
                        style={{ minWidth: 130 }}
                        value={t.assignee || ""}
                        onChange={(e) => setAssignee(t.id, e.target.value)}
                      >
                        <option value="">بدون مسئول</option>
                        {members
                          .filter((m) => m.role === "developer" || m.is_active)
                          .map((m) => (
                            <option key={m.id} value={m.id}>
                              {m.full_name}
                            </option>
                          ))}
                      </select>
                    ) : (
                      <span className="muted small">
                        {t.assignee_name || "—"}
                      </span>
                    )}
                  </td>
                  <td>
                    <TaskStatusBadge status={t.status} />
                  </td>
                  <td className="muted small">
                    {t.due_date ? faDate(t.due_date) : "—"}
                  </td>
                  <td className="muted small">{faAgo(t.updated_at)}</td>
                  <td>
                    <div className="row">
                      {t.status !== "in_progress" && t.status !== "done" && (
                        <button
                          className="btn btn-sm"
                          onClick={() => quickStatus(t.id, "in_progress")}
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
                          onClick={() => quickStatus(t.id, "done")}
                        >
                          ✓ انجام شد
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </Table>
          ))}
      </Card>

      {showCreate && (
        <CreateTaskModal
          projects={projects}
          members={members}
          ops={ops}
          onClose={() => setShowCreate(false)}
          onCreated={() => {
            setShowCreate(false);
            load();
          }}
        />
      )}
    </>
  );
}

function CreateTaskModal({ projects, members, ops, onClose, onCreated }) {
  const [form, setForm] = useState({
    project: "",
    title: "",
    description: "",
    work_type: "feature",
    priority: "medium",
    assignee: "",
    due_date: "",
  });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      await api.post("/api/tasks/create/", {
        project: Number(form.project),
        title: form.title,
        description: form.description,
        work_type: form.work_type,
        priority: form.priority,
        assignee: form.assignee ? Number(form.assignee) : null,
        due_date: form.due_date || null,
      });
      onCreated();
    } catch (err) {
      const d = err.data;
      setError(
        (d &&
          (d.detail ||
            d.non_field_errors ||
            Object.values(d)
              .map((v) => (typeof v === "string" ? v : v.join(" ")))
              .join(" "))) ||
          "ایجاد وظیفه ناموفق بود.",
      );
      setBusy(false);
    }
  };

  return (
    <Modal title="ایجاد وظیفه جدید" onClose={onClose}>
      <form onSubmit={submit}>
        <div className="form-grid">
          <Field label="پروژه">
            <Select
              options={projects.map((p) => [p.id, p.name])}
              value={form.project}
              onChange={set("project")}
            />
          </Field>
          <Field label="عنوان وظیفه">
            <TextInput value={form.title} onChange={set("title")} required />
          </Field>
          <Field label="نوع کار">
            <Select
              options={Object.entries(WORK_TYPE_LABELS)}
              value={form.work_type}
              onChange={set("work_type")}
            />
          </Field>
          <Field label="اولویت">
            <Select
              options={Object.entries(PRIORITY_LABELS)}
              value={form.priority}
              onChange={set("priority")}
            />
          </Field>
          <Field label="مسئول">
            <Select
              options={members
                .filter((m) => m.role === "developer")
                .map((m) => [m.id, m.full_name])}
              value={form.assignee}
              onChange={set("assignee")}
              placeholder="خودم"
            />
          </Field>
          <Field label="مهلت (اختیاری)">
            <JalaliDateField
              value={form.due_date}
              onChange={(iso) => setForm((f) => ({ ...f, due_date: iso }))}
            />
          </Field>
          <Field label="توضیحات" full>
            <TextArea value={form.description} onChange={set("description")} />
          </Field>
        </div>
        {error && (
          <div className="error-box" style={{ marginTop: 10 }}>
            {error}
          </div>
        )}
        <div className="form-actions">
          <button type="submit" className="btn btn-primary" disabled={busy}>
            {busy ? "در حال ذخیره..." : "ایجاد وظیفه"}
          </button>
          <button type="button" className="btn" onClick={onClose}>
            انصراف
          </button>
        </div>
      </form>
    </Modal>
  );
}
