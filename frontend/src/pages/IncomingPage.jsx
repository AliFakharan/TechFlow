import React, { useCallback, useEffect, useState } from "react";
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
  Badge,
  Modal,
  Field,
  TextInput,
  Select,
  TextArea,
  faNumber,
  faAgo,
} from "../components/ui.jsx";
import { INCOMING_STATUS_LABELS } from "../utils/labels.js";

const INCOMING_STATUSES = Object.entries(INCOMING_STATUS_LABELS);

const STATUS_COLORS = {
  new: "badge-gray",
  evaluating: "badge-blue",
  accepted: "badge-green",
  rejected: "badge-red",
  converted_task: "badge-purple",
  converted_support: "badge-purple",
  converted_project: "badge-purple",
};

export default function IncomingPage() {
  const { user } = useAuth();
  const ops = isOps(user?.role);

  const [rows, setRows] = useState(null);
  const [error, setError] = useState("");
  const [status, setStatus] = useState("");
  const [showCreate, setShowCreate] = useState(false);
  const [converting, setConverting] = useState(null);
  const [projects, setProjects] = useState([]);
  const [flash, setFlash] = useState("");

  const notify = (msg) => {
    setFlash(msg);
    setTimeout(() => setFlash(""), 2500);
  };

  const load = useCallback(() => {
    const p = new URLSearchParams();
    if (status) p.set("status", status);
    api
      .list(`/api/incoming-work/?${p.toString()}`)
      .then(setRows)
      .catch((e) => setError(e.message));
  }, [status]);
  useEffect(load, [load]);

  useEffect(() => {
    api
      .list("/api/projects/")
      .then(setProjects)
      .catch(() => {});
  }, []);

  const changeStatus = async (id, newStatus) => {
    try {
      await api.post(`/api/incoming-work/${id}/status/`, { status: newStatus });
      notify("وضعیت به‌روزرسانی شد.");
      load();
    } catch (e) {
      notify(e.message);
    }
  };

  const convert = async (target, project) => {
    try {
      await api.post(`/api/incoming-work/${converting.id}/convert/`, {
        convert_to: target,
        project: project || null,
      });
      notify("کار ورودی با موفقیت تبدیل شد.");
      setConverting(null);
      load();
    } catch (e) {
      notify(e.message);
    }
  };

  return (
    <>
      <PageHead
        title="کارهای ورودی"
        subtitle="کارهای غیربرنامه‌ای که به تیم می‌رسند — تا دیر نشده ثبت شوند."
        actions={
          <button
            className="btn btn-primary"
            onClick={() => setShowCreate(true)}
          >
            + ثبت کار ورودی
          </button>
        }
      />
      {flash && <div className="flash">{flash}</div>}

      <Card tight>
        <div className="filter-bar">
          <Select
            options={INCOMING_STATUSES}
            value={status}
            onChange={(e) => setStatus(e.target.value)}
            placeholder="همه وضعیت‌ها"
          />
          <span className="muted small grow" style={{ textAlign: "left" }}>
            {rows ? `${faNumber(rows.length)} مورد` : ""}
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
            <Empty>موردی یافت نشد.</Empty>
          ) : (
            <Table
              headers={[
                "کار ورودی",
                "منبع",
                "ثبت‌کننده",
                "وضعیت",
                "نتیجه",
                "ثبت",
                "عمل",
              ]}
            >
              {rows.map((w) => (
                <tr key={w.id}>
                  <td>
                    <b>{w.title}</b>
                    {w.description && (
                      <div className="muted tiny">{w.description}</div>
                    )}
                  </td>
                  <td className="muted small">{w.source || "—"}</td>
                  <td className="muted small">{w.reported_by_name || "—"}</td>
                  <td>
                    <Badge color={STATUS_COLORS[w.status] || "badge-gray"}>
                      {INCOMING_STATUS_LABELS[w.status] || w.status}
                    </Badge>
                  </td>
                  <td className="muted small">
                    {w.converted_project_name ||
                      w.converted_task_title ||
                      w.converted_support_title ||
                      "—"}
                  </td>
                  <td className="muted small">{faAgo(w.created_at)}</td>
                  <td>
                    <div className="row">
                      {w.status === "new" && (
                        <button
                          className="btn btn-sm"
                          onClick={() => changeStatus(w.id, "evaluating")}
                        >
                          بررسی
                        </button>
                      )}
                      {w.status === "evaluating" && (
                        <>
                          <button
                            className="btn btn-sm"
                            onClick={() => changeStatus(w.id, "accepted")}
                          >
                            پذیرش
                          </button>
                          <button
                            className="btn btn-sm"
                            style={{ color: "var(--danger)" }}
                            onClick={() => changeStatus(w.id, "rejected")}
                          >
                            رد
                          </button>
                        </>
                      )}
                      {w.status === "accepted" && ops && (
                        <button
                          className="btn btn-sm btn-primary"
                          onClick={() => setConverting(w)}
                        >
                          تبدیل
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
        <CreateIncomingModal
          onClose={() => setShowCreate(false)}
          onCreated={() => {
            setShowCreate(false);
            load();
          }}
        />
      )}

      {converting && (
        <ConvertModal
          item={converting}
          projects={projects}
          onConvert={convert}
          onClose={() => setConverting(null)}
        />
      )}
    </>
  );
}

function CreateIncomingModal({ onClose, onCreated }) {
  const [form, setForm] = useState({ title: "", description: "", source: "" });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      await api.post("/api/incoming-work/create/", form);
      onCreated();
    } catch (err) {
      setError(err.message);
      setBusy(false);
    }
  };

  return (
    <Modal title="ثبت کار ورودی جدید" onClose={onClose}>
      <form onSubmit={submit}>
        <div className="form-grid">
          <Field label="عنوان" full>
            <TextInput value={form.title} onChange={set("title")} required />
          </Field>
          <Field label="منبع / درخواست‌کننده">
            <TextInput
              value={form.source}
              onChange={set("source")}
              placeholder="مثلا: واحد حسابداری"
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
            {busy ? "در حال ذخیره..." : "ثبت"}
          </button>
          <button type="button" className="btn" onClick={onClose}>
            انصراف
          </button>
        </div>
      </form>
    </Modal>
  );
}

function ConvertModal({ item, projects, onConvert, onClose }) {
  const [target, setTarget] = useState("task");
  const [project, setProject] = useState("");
  return (
    <Modal title={`تبدیل کار ورودی: ${item.title}`} onClose={onClose}>
      <div className="form-grid">
        <Field label="تبدیل به" full>
          <Select
            options={[
              ["task", "وظیفه (در پروژه)"],
              ["support", "تیکت پشتیبانی"],
              ["project", "پروژه جدید"],
            ]}
            value={target}
            onChange={(e) => setTarget(e.target.value)}
            placeholder=""
          />
        </Field>
        {target !== "project" && (
          <Field label="پروژه" full>
            <Select
              options={projects.map((p) => [p.id, p.name])}
              value={project}
              onChange={(e) => setProject(e.target.value)}
              placeholder={
                target === "task" ? "پروژه را انتخاب کنید" : "اختیاری"
              }
            />
          </Field>
        )}
      </div>
      <div className="form-actions">
        <button
          className="btn btn-primary"
          onClick={() => onConvert(target, project ? Number(project) : null)}
        >
          تبدیل
        </button>
        <button className="btn" onClick={onClose}>
          انصراف
        </button>
      </div>
    </Modal>
  );
}
