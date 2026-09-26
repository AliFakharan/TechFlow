import React, { useCallback, useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { api } from "../api/client.js";
import { isOps } from "../utils/roles.js";
import { useAuth } from "../context/AuthContext.jsx";
import {
  PageHead,
  Card,
  Table,
  Empty,
  ErrorBox,
  Spinner,
  PriorityBadge,
  Badge,
  Modal,
  Field,
  TextInput,
  Select,
  TextArea,
  faNumber,
  faAgo,
  faDateTime,
} from "../components/ui.jsx";
import {
  SUPPORT_STATUS_LABELS,
  WORK_TYPE_LABELS,
  PRIORITY_LABELS,
  STATUS_COLORS,
} from "../utils/labels.js";

const SUPPORT_STATUSES = Object.entries(SUPPORT_STATUS_LABELS);

export default function SupportPage() {
  const { user } = useAuth();
  const [params, setParams] = useSearchParams();
  const ops = isOps(user?.role);

  const [rows, setRows] = useState(null);
  const [error, setError] = useState("");
  const [open, setOpen] = useState(params.get("open") === "1");
  const [mine, setMine] = useState(params.get("mine") === "1");
  const [status, setStatus] = useState("");
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
    if (open) p.set("open", "1");
    if (mine) p.set("mine", "1");
    if (status) p.set("status", status);
    api
      .list(`/api/support/?${p.toString()}`)
      .then(setRows)
      .catch((e) => setError(e.message));
  }, [open, mine, status]);
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

  const changeStatus = async (id, newStatus) => {
    try {
      await api.post(`/api/support/${id}/status/`, { status: newStatus });
      notify("وضعیت تیکت به‌روزرسانی شد.");
      load();
    } catch (e) {
      notify(e.message);
    }
  };

  const assign = async (id, memberId) => {
    try {
      await api.post(`/api/support/${id}/assign/`, {
        assignee: Number(memberId),
      });
      notify("مسئول تیکت تعیین شد.");
      load();
    } catch (e) {
      notify(e.message);
    }
  };

  return (
    <>
      <PageHead
        title="پشتیبانی"
        subtitle="تیکت‌های پشتیبانی به‌عنوان یک دسته‌ی کاری رسمی — بدون ساعت‌شماری."
        actions={
          <button
            className="btn btn-primary"
            onClick={() => setShowCreate(true)}
          >
            + تیکت پشتیبانی
          </button>
        }
      />
      {flash && <div className="flash">{flash}</div>}

      <Card tight>
        <div className="filter-bar">
          <label className="row" style={{ fontSize: 12.5 }}>
            <input
              type="checkbox"
              checked={open}
              onChange={(e) => setOpen(e.target.checked)}
            />
            فقط باز
          </label>
          <label className="row" style={{ fontSize: 12.5 }}>
            <input
              type="checkbox"
              checked={mine}
              onChange={(e) => setMine(e.target.checked)}
            />
            فقط من
          </label>
          <Select
            options={SUPPORT_STATUSES}
            value={status}
            onChange={(e) => setStatus(e.target.value)}
            placeholder="همه وضعیت‌ها"
          />
          <span className="muted small grow" style={{ textAlign: "left" }}>
            {rows ? `${faNumber(rows.length)} تیکت` : ""}
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
            <Empty>تیکتی مطابق فیلتر یافت نشد.</Empty>
          ) : (
            <Table
              headers={[
                "تیکت",
                "پروژه",
                "درخواست‌دهنده",
                "شدت",
                "مسئول",
                "وضعیت",
                "ثبت",
                "عمل",
              ]}
            >
              {rows.map((t) => (
                <tr key={t.id}>
                  <td>
                    <b>{t.title}</b>
                    {t.description && (
                      <div className="muted tiny">{t.description}</div>
                    )}
                  </td>
                  <td className="muted small">{t.project_name || "عمومی"}</td>
                  <td className="muted small">{t.requester || "—"}</td>
                  <td>
                    <PriorityBadge value={t.severity} />
                  </td>
                  <td>
                    {ops ? (
                      <select
                        className="input"
                        style={{ minWidth: 130 }}
                        value={t.assignee || ""}
                        onChange={(e) =>
                          e.target.value && assign(t.id, e.target.value)
                        }
                      >
                        <option value="">
                          {t.assignee_name || "بدون مسئول"}
                        </option>
                        {members
                          .filter((m) => m.role === "developer")
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
                    <Badge color={STATUS_COLORS[t.status] || "badge-gray"}>
                      {SUPPORT_STATUS_LABELS[t.status] || t.status}
                    </Badge>
                  </td>
                  <td className="muted small">{faAgo(t.created_at)}</td>
                  <td>
                    <div className="row">
                      {t.status === "new" && (
                        <button
                          className="btn btn-sm"
                          onClick={() => changeStatus(t.id, "in_progress")}
                        >
                          شروع
                        </button>
                      )}
                      {(t.status === "new" ||
                        t.status === "assigned" ||
                        t.status === "in_progress") && (
                        <button
                          className="btn btn-sm"
                          style={{
                            borderColor: "var(--ok)",
                            color: "var(--ok)",
                          }}
                          onClick={() => changeStatus(t.id, "resolved")}
                        >
                          ✓ حل شد
                        </button>
                      )}
                      {t.status === "resolved" && (
                        <button
                          className="btn btn-sm"
                          onClick={() => changeStatus(t.id, "closed")}
                        >
                          بستن
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
        <CreateTicketModal
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

function CreateTicketModal({ projects, members, ops, onClose, onCreated }) {
  const [form, setForm] = useState({
    title: "",
    description: "",
    project: "",
    requester: "",
    severity: "medium",
    work_type: "support",
    assignee: "",
  });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      await api.post("/api/support/create/", {
        title: form.title,
        description: form.description,
        project: form.project ? Number(form.project) : null,
        requester: form.requester,
        severity: form.severity,
        work_type: form.work_type,
        assignee: ops && form.assignee ? Number(form.assignee) : null,
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
          "ثبت تیکت ناموفق بود.",
      );
      setBusy(false);
    }
  };

  return (
    <Modal title="ثبت تیکت پشتیبانی" onClose={onClose}>
      <form onSubmit={submit}>
        <div className="form-grid">
          <Field label="عنوان تیکت" full>
            <TextInput value={form.title} onChange={set("title")} required />
          </Field>
          <Field label="پروژه (اختیاری)">
            <Select
              options={projects.map((p) => [p.id, p.name])}
              value={form.project}
              onChange={set("project")}
              placeholder="عمومی (بدون پروژه)"
            />
          </Field>
          <Field label="درخواست‌دهنده">
            <TextInput value={form.requester} onChange={set("requester")} />
          </Field>
          <Field label="شدت">
            <Select
              options={Object.entries(PRIORITY_LABELS)}
              value={form.severity}
              onChange={set("severity")}
            />
          </Field>
          <Field label="نوع کار">
            <Select
              options={Object.entries(WORK_TYPE_LABELS)}
              value={form.work_type}
              onChange={set("work_type")}
            />
          </Field>
          {ops && (
            <Field label="مسئول (اختیاری)">
              <Select
                options={members
                  .filter((m) => m.role === "developer")
                  .map((m) => [m.id, m.full_name])}
                value={form.assignee}
                onChange={set("assignee")}
                placeholder="خودم"
              />
            </Field>
          )}
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
            {busy ? "در حال ذخیره..." : "ثبت تیکت"}
          </button>
          <button type="button" className="btn" onClick={onClose}>
            انصراف
          </button>
        </div>
      </form>
    </Modal>
  );
}
