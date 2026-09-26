import React, { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
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
  Modal,
  Field,
  TextInput,
  Select,
  TextArea,
  faNumber,
  faDate,
} from "../components/ui.jsx";
import JalaliDateField from "../components/JalaliDateField.jsx";
import {
  PROJECT_STATUS_LABELS,
  PRIORITY_LABELS,
  RISK_LABELS,
} from "../utils/labels.js";

const today = () => new Date().toISOString().slice(0, 10);
const plusDays = (d) =>
  new Date(Date.now() + d * 86400000).toISOString().slice(0, 10);

export default function ProjectsPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [rows, setRows] = useState(null);
  const [error, setError] = useState("");
  const [q, setQ] = useState("");
  const [status, setStatus] = useState("");
  const [priority, setPriority] = useState("");
  const [risk, setRisk] = useState("");
  const [showCreate, setShowCreate] = useState(false);
  const [teams, setTeams] = useState([]);
  const [members, setMembers] = useState([]);

  const role = user?.role;
  const canCreate = canManageProjects(role);

  const load = useCallback(() => {
    const params = new URLSearchParams();
    if (q) params.set("q", q);
    if (status) params.set("status", status);
    if (priority) params.set("priority", priority);
    if (risk) params.set("risk_status", risk);
    api
      .list(`/api/projects/?${params.toString()}`)
      .then(setRows)
      .catch((e) => setError(e.message));
  }, [q, status, priority, risk]);
  useEffect(load, [load]);

  useEffect(() => {
    api
      .list("/api/teams/")
      .then(setTeams)
      .catch(() => {});
    api
      .list("/api/members/")
      .then(setMembers)
      .catch(() => {});
  }, []);

  return (
    <>
      <PageHead
        title="پروژه‌ها"
        subtitle="فهرست پروژه‌های تیم با وضعیت، اولویت و سیگنال ریسک شفاف."
        actions={
          canCreate && (
            <button
              className="btn btn-primary"
              onClick={() => setShowCreate(true)}
            >
              + پروژه جدید
            </button>
          )
        }
      />

      <Card tight>
        <div className="filter-bar">
          <input
            className="input grow"
            placeholder="جستجو در نام پروژه یا کلاینت..."
            value={q}
            onChange={(e) => setQ(e.target.value)}
          />
          <Select
            options={Object.entries(PROJECT_STATUS_LABELS)}
            value={status}
            onChange={(e) => setStatus(e.target.value)}
            placeholder="همه وضعیت‌ها"
          />
          <Select
            options={Object.entries(PRIORITY_LABELS)}
            value={priority}
            onChange={(e) => setPriority(e.target.value)}
            placeholder="همه اولویت‌ها"
          />
          <Select
            options={Object.entries(RISK_LABELS)}
            value={risk}
            onChange={(e) => setRisk(e.target.value)}
            placeholder="همه وضعیت‌های ریسک"
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
            <Empty>پروژه‌ای مطابق فیلتر یافت نشد.</Empty>
          ) : (
            <Table
              headers={[
                "پروژه",
                "وضعیت",
                "اولویت",
                "ریسک",
                "پیشرفت",
                "مهلت",
                "مالک",
                "اعضا",
                "مانع باز",
              ]}
            >
              {rows.map((p) => (
                <tr
                  key={p.id}
                  className="clickable"
                  onClick={() => navigate(`/projects/${p.id}`)}
                >
                  <td>
                    <b>{p.name}</b>
                    {p.client && <div className="muted tiny">{p.client}</div>}
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
                    {p.expected_completion
                      ? faDate(p.expected_completion)
                      : "—"}
                    {p.days_to_expected_completion != null && (
                      <div className="tiny">
                        {p.days_to_expected_completion < 0
                          ? `${faNumber(-p.days_to_expected_completion)} روز گذشته`
                          : `${faNumber(p.days_to_expected_completion)} روز مانده`}
                      </div>
                    )}
                  </td>
                  <td className="muted small">{p.owner_name || "—"}</td>
                  <td className="num">{faNumber(p.member_count)}</td>
                  <td className="num">{faNumber(p.open_blocker_count)}</td>
                </tr>
              ))}
            </Table>
          ))}
      </Card>

      {showCreate && (
        <CreateProjectModal
          teams={teams}
          members={members}
          onClose={() => setShowCreate(false)}
          onCreated={(id) => {
            setShowCreate(false);
            navigate(`/projects/${id}`);
          }}
        />
      )}
    </>
  );
}

function CreateProjectModal({ teams, members, onClose, onCreated }) {
  const [form, setForm] = useState({
    team: "",
    name: "",
    description: "",
    status: "planned",
    priority: "medium",
    start_date: today(),
    expected_completion: plusDays(60),
    client: "",
    owner: "",
    member_ids: [],
  });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

  const toggleMember = (id) =>
    setForm((f) => ({
      ...f,
      member_ids: f.member_ids.includes(id)
        ? f.member_ids.filter((x) => x !== id)
        : [...f.member_ids, id],
    }));

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      const body = {
        ...form,
        team: Number(form.team),
        owner: form.owner ? Number(form.owner) : null,
        expected_completion: form.expected_completion || null,
      };
      const created = await api.post("/api/projects/create/", body);
      onCreated(created.id);
    } catch (err) {
      const d = err.data;
      setError(
        (d &&
          (d.detail ||
            d.non_field_errors ||
            Object.values(d)
              .map((v) => (typeof v === "string" ? v : v.join(" ")))
              .join(" "))) ||
          "ایجاد پروژه ناموفق بود.",
      );
      setBusy(false);
    }
  };

  return (
    <Modal title="ایجاد پروژه جدید" onClose={onClose} wide>
      <form onSubmit={submit}>
        <div className="form-grid">
          <Field label="تیم">
            <Select
              options={teams.map((t) => [t.id, t.name])}
              value={form.team}
              onChange={set("team")}
            />
          </Field>
          <Field label="نام پروژه">
            <TextInput value={form.name} onChange={set("name")} required />
          </Field>
          <Field label="وضعیت">
            <Select
              options={Object.entries(PROJECT_STATUS_LABELS)}
              value={form.status}
              onChange={set("status")}
            />
          </Field>
          <Field label="اولویت">
            <Select
              options={Object.entries(PRIORITY_LABELS)}
              value={form.priority}
              onChange={set("priority")}
            />
          </Field>
          <Field label="تاریخ شروع">
            <JalaliDateField
              value={form.start_date}
              onChange={(iso) => setForm((f) => ({ ...f, start_date: iso }))}
            />
          </Field>
          <Field label="تاریخ اتمام مورد انتظار">
            <JalaliDateField
              value={form.expected_completion}
              onChange={(iso) =>
                setForm((f) => ({ ...f, expected_completion: iso }))
              }
            />
          </Field>
          <Field label="کلاینت / درخواست‌کننده">
            <TextInput value={form.client} onChange={set("client")} />
          </Field>
          <Field label="مالک پروژه">
            <Select
              options={members.map((m) => [m.id, m.full_name])}
              value={form.owner}
              onChange={set("owner")}
              placeholder="بدون مالک"
            />
          </Field>
          <Field label="توضیحات" full>
            <TextArea value={form.description} onChange={set("description")} />
          </Field>
          <Field label="اعضای پروژه" full>
            <div className="chip-list">
              {members
                .filter((m) => m.role === "developer" || m.is_active)
                .map((m) => (
                  <button
                    type="button"
                    key={m.id}
                    className="chip"
                    onClick={() => toggleMember(m.id)}
                    style={{
                      cursor: "pointer",
                      background: form.member_ids.includes(m.id)
                        ? "var(--primary-soft)"
                        : "#eef2f6",
                      border: form.member_ids.includes(m.id)
                        ? "1px solid var(--accent)"
                        : "1px solid transparent",
                    }}
                  >
                    {m.full_name}
                  </button>
                ))}
            </div>
          </Field>
        </div>
        {error && (
          <div className="error-box" style={{ marginTop: 10 }}>
            {error}
          </div>
        )}
        <div className="form-actions">
          <button type="submit" className="btn btn-primary" disabled={busy}>
            {busy ? "در حال ذخیره..." : "ایجاد پروژه"}
          </button>
          <button type="button" className="btn" onClick={onClose}>
            انصراف
          </button>
        </div>
      </form>
    </Modal>
  );
}
