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
import { BLOCKER_CATEGORY_LABELS, PRIORITY_LABELS } from "../utils/labels.js";

export default function BlockersPage() {
  const { user } = useAuth();
  const [params, setParams] = useSearchParams();
  const ops = isOps(user?.role);

  const [rows, setRows] = useState(null);
  const [error, setError] = useState("");
  const [open, setOpen] = useState(params.get("open") === "1");
  const [mine, setMine] = useState(params.get("mine") === "1");
  const [category, setCategory] = useState("");
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
    if (category) p.set("category", category);
    api
      .list(`/api/blockers/?${p.toString()}`)
      .then(setRows)
      .catch((e) => setError(e.message));
  }, [open, mine, category]);
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

  const resolve = async (id) => {
    try {
      await api.post(`/api/blockers/${id}/resolve/`, { note: "" });
      notify("مانع رفع شد.");
      load();
    } catch (e) {
      notify(e.message);
    }
  };

  return (
    <>
      <PageHead
        title="موانع"
        subtitle="هر چیزی که جلوی پیشرفت کار را گرفته — ثبت سریع، پایش شفاف."
        actions={
          <button
            className="btn btn-primary"
            onClick={() => setShowCreate(true)}
          >
            + ثبت مانع
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
            options={Object.entries(BLOCKER_CATEGORY_LABELS)}
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            placeholder="همه دسته‌ها"
          />
          <span className="muted small grow" style={{ textAlign: "left" }}>
            {rows ? `${faNumber(rows.length)} مانع` : ""}
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
            <Empty>مانعی مطابق فیلتر یافت نشد.</Empty>
          ) : (
            <Table
              headers={[
                "مانع",
                "دسته",
                "پروژه",
                "اولویت",
                "صاحب",
                "سن",
                "وضعیت",
                "عمل",
              ]}
            >
              {rows.map((b) => (
                <tr key={b.id}>
                  <td>
                    <b>{b.title}</b>
                    {b.description && (
                      <div className="muted tiny">{b.description}</div>
                    )}
                  </td>
                  <td className="muted small">
                    {BLOCKER_CATEGORY_LABELS[b.category] || b.category}
                  </td>
                  <td className="muted small">{b.project_name || "—"}</td>
                  <td>
                    <PriorityBadge value={b.priority} />
                  </td>
                  <td className="muted small">{b.owner_name || "—"}</td>
                  <td className="num">{faAgo(b.created_at)}</td>
                  <td>
                    <Badge
                      color={b.status === "open" ? "badge-red" : "badge-green"}
                    >
                      {b.status === "open" ? "باز" : "رفع‌شده"}
                    </Badge>
                  </td>
                  <td>
                    {b.status === "open" && (
                      <button
                        className="btn btn-sm"
                        onClick={() => resolve(b.id)}
                      >
                        ✓ رفع مانع
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </Table>
          ))}
      </Card>

      {showCreate && (
        <CreateBlockerModal
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

function CreateBlockerModal({ projects, members, ops, onClose, onCreated }) {
  const [form, setForm] = useState({
    title: "",
    description: "",
    project: "",
    task: "",
    category: "technical",
    priority: "medium",
    owner: "",
  });
  const [tasks, setTasks] = useState([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

  // Load tasks for the selected project so a blocker can be attached to one.
  useEffect(() => {
    if (!form.project) {
      setTasks([]);
      return;
    }
    api
      .list(`/api/tasks/?project=${form.project}`)
      .then(setTasks)
      .catch(() => setTasks([]));
  }, [form.project]);

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      await api.post("/api/blockers/create/", {
        title: form.title,
        description: form.description,
        project: form.project ? Number(form.project) : null,
        task: form.task ? Number(form.task) : null,
        category: form.category,
        priority: form.priority,
        owner: ops && form.owner ? Number(form.owner) : null,
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
          "ثبت مانع ناموفق بود.",
      );
      setBusy(false);
    }
  };

  return (
    <Modal title="ثبت مانع جدید" onClose={onClose}>
      <form onSubmit={submit}>
        <div className="form-grid">
          <Field label="عنوان مانع" full>
            <TextInput value={form.title} onChange={set("title")} required />
          </Field>
          <Field label="پروژه (اختیاری)">
            <Select
              options={projects.map((p) => [p.id, p.name])}
              value={form.project}
              onChange={set("project")}
              placeholder="بدون پروژه"
            />
          </Field>
          <Field label="وظیفه (اختیاری)">
            <Select
              options={tasks.map((t) => [t.id, t.title])}
              value={form.task}
              onChange={set("task")}
              placeholder={form.project ? "بدون وظیفه" : "ابتدا پروژه را انتخاب کنید"}
              disabled={!form.project}
            />
          </Field>
          <Field label="دسته">
            <Select
              options={Object.entries(BLOCKER_CATEGORY_LABELS)}
              value={form.category}
              onChange={set("category")}
            />
          </Field>
          <Field label="اهمیت">
            <Select
              options={Object.entries(PRIORITY_LABELS)}
              value={form.priority}
              onChange={set("priority")}
            />
          </Field>
          {ops && (
            <Field label="صاحب مانع">
              <Select
                options={members.map((m) => [m.id, m.full_name])}
                value={form.owner}
                onChange={set("owner")}
                placeholder="خودم"
              />
            </Field>
          )}
          <Field label="توضیحات" full>
            <TextArea
              value={form.description}
              onChange={set("description")}
              placeholder="چکیزی مانع است؟ چه کاری باید انجام شود تا رفع شود؟"
            />
          </Field>
        </div>
        {error && (
          <div className="error-box" style={{ marginTop: 10 }}>
            {error}
          </div>
        )}
        <div className="form-actions">
          <button type="submit" className="btn btn-primary" disabled={busy}>
            {busy ? "در حال ذخیره..." : "ثبت مانع"}
          </button>
          <button type="button" className="btn" onClick={onClose}>
            انصراف
          </button>
        </div>
      </form>
    </Modal>
  );
}
