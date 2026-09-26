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
  BarRow,
  Modal,
  Field,
  Select,
  TextInput,
  faNumber,
} from "../components/ui.jsx";

export default function CapacityPage() {
  const { user } = useAuth();
  const [params, setParams] = useSearchParams();
  const ops = isOps(user?.role);

  const [summary, setSummary] = useState(null);
  const [error, setError] = useState("");
  const [projects, setProjects] = useState([]);
  const [editing, setEditing] = useState(null); // member row
  const [flash, setFlash] = useState("");

  const notify = (msg) => {
    setFlash(msg);
    setTimeout(() => setFlash(""), 2500);
  };

  const load = useCallback(() => {
    api
      .get("/api/capacity/summary/")
      .then(setSummary)
      .catch((e) => setError(e.message));
  }, []);
  useEffect(load, [load]);

  useEffect(() => {
    api
      .list("/api/projects/")
      .then(setProjects)
      .catch(() => {});
  }, []);

  const saveAllocation = async (memberId, project, percent) => {
    try {
      const res = await api.post("/api/capacity/set/", {
        member: Number(memberId),
        project: project ? Number(project) : null,
        percent: Number(percent),
      });
      if (res.overallocated) {
        notify(
          `⚠ مجموع تخصیص ${faNumber(res.member_total_percent)}٪ — بیش از ظرفیت!`,
        );
      } else {
        notify("تخصیص ذخیره شد.");
      }
      setEditing(null);
      load();
    } catch (e) {
      notify(e.message);
    }
  };

  const canEdit = (memberId) => ops || memberId === user?.id;
  const focusSelf = params.get("focus") === "self";

  return (
    <>
      <PageHead
        title="ظرفیت تیم"
        subtitle="کجا ظرفیت در دسترس است؟ — تخصیص درصدی، بدون ساعت‌شماری و پایش فردی."
      />
      {flash && <div className="flash">{flash}</div>}

      {error && <ErrorBox>{error}</ErrorBox>}
      {!summary && !error && <Spinner />}

      {summary && (
        <>
          {focusSelf && (
            <Card title="تخصیص‌های من">
              <div className="row">
                <span className="muted">
                  مجموع:{" "}
                  <b>
                    {faNumber(
                      summary.per_member.find((m) => m.member_id === user?.id)
                        ?.total_percent ?? 0,
                    )}
                    ٪
                  </b>
                </span>
                <span className="small muted">
                  برای ویرایش، روی «ویرایش» در جدول زیر بزنید.
                </span>
              </div>
            </Card>
          )}

          <div className="grid grid-2-1">
            <Card title="تخصیص به تفکیک عضو" tight>
              <Table headers={["عضو", "پشتیبانی", "پروژه‌ها", "مجموع", "عمل"]}>
                {summary.per_member.map((m) => (
                  <tr key={m.member_id}>
                    <td>
                      <b>{m.full_name}</b>
                    </td>
                    <td className="num">{faNumber(m.support_percent)}٪</td>
                    <td>
                      <div className="chip-list">
                        {m.projects.map((p) => (
                          <span className="chip" key={p.project_id}>
                            {projectName(projects, p.project_id)}:{" "}
                            <b>{faNumber(p.percent)}٪</b>
                          </span>
                        ))}
                        {m.projects.length === 0 && (
                          <span className="muted tiny">—</span>
                        )}
                      </div>
                    </td>
                    <td>
                      <b
                        style={{
                          color:
                            m.total_percent > 100
                              ? "var(--danger)"
                              : m.total_percent < 50
                                ? "var(--warn)"
                                : "var(--text)",
                        }}
                      >
                        {faNumber(m.total_percent)}٪
                      </b>
                      {m.overallocated && (
                        <span className="muted tiny"> بیش از ظرفیت</span>
                      )}
                      {m.underallocated && (
                        <span className="muted tiny"> کم‌تخصیص</span>
                      )}
                    </td>
                    <td>
                      {canEdit(m.member_id) && (
                        <button
                          className="btn btn-sm"
                          onClick={() =>
                            setEditing({
                              member_id: m.member_id,
                              full_name: m.full_name,
                              projects: m.projects,
                              support: m.support_percent,
                            })
                          }
                        >
                          ویرایش
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </Table>
            </Card>

            <div>
              <Card title="مجموع ظرفیت مصرف‌شده به تفکیک پروژه">
                {(summary.per_project || []).length === 0 ? (
                  <Empty>تخصیصی ثبت نشده.</Empty>
                ) : (
                  summary.per_project.map((p) => (
                    <BarRow
                      key={p.project_id || "support"}
                      label={p.label || projectName(projects, p.project_id)}
                      value={p.total_percent}
                      max={Math.max(400, p.total_percent)}
                    />
                  ))
                )}
              </Card>
              <Card title="خلاصه">
                <div
                  className="kv"
                  style={{
                    display: "grid",
                    gridTemplateColumns: "1fr 1fr",
                    rowGap: 8,
                  }}
                >
                  <div>
                    <div className="muted small">میانگین تخصیص تیم</div>
                    <b>
                      {faNumber(Math.round(summary.team_average_percent || 0))}٪
                    </b>
                  </div>
                  <div>
                    <div className="muted small">اعضای بیش‌تخصیص</div>
                    <b
                      style={{
                        color: summary.overallocated_members.length
                          ? "var(--danger)"
                          : "var(--ok)",
                      }}
                    >
                      {summary.overallocated_members.length
                        ? summary.overallocated_members
                            .map((m) => m.full_name)
                            .join("، ")
                        : "ندارد ✓"}
                    </b>
                  </div>
                </div>
                <p className="muted small" style={{ marginTop: 12 }}>
                  تخصیص بیش از ۱۰۰٪ خطا نیست؛ یک هشدار است که به مدیر تیم برای
                  تعادل بار کاری کمک می‌کند.
                </p>
              </Card>
            </div>
          </div>
        </>
      )}

      {editing && (
        <EditAllocationsModal
          member={editing}
          projects={projects}
          onSave={saveAllocation}
          onClose={() => setEditing(null)}
        />
      )}
    </>
  );
}

function projectName(projects, id) {
  return projects.find((p) => p.id === id)?.name || `پروژه #${id}`;
}

function EditAllocationsModal({ member, projects, onSave, onClose }) {
  const rows = [
    { key: "support", label: "پشتیبانی (عمومی)", value: member.support || 0 },
    ...member.projects.map((p) => ({
      key: p.project_id,
      label: projectName(projects, p.project_id),
      value: p.percent,
    })),
  ];
  const [values, setValues] = useState(
    Object.fromEntries(rows.map((r) => [r.key, r.value])),
  );
  const [project, setProject] = useState("");
  const [newPercent, setNewPercent] = useState(10);
  const total = Object.values(values).reduce((s, v) => s + (Number(v) || 0), 0);

  return (
    <Modal title={`ویرایش تخصیص — ${member.full_name}`} onClose={onClose} wide>
      <div>
        {rows.map((r) => (
          <div
            className="row-between"
            key={r.key}
            style={{ padding: "6px 0", borderBottom: "1px solid #eef2f6" }}
          >
            <span>{r.label}</span>
            <div className="row">
              <input
                type="number"
                className="input"
                style={{ width: 80 }}
                min="0"
                max="200"
                value={values[r.key] ?? 0}
                onChange={(e) =>
                  setValues((v) => ({ ...v, [r.key]: e.target.value }))
                }
              />
              <span className="muted small">٪</span>
            </div>
          </div>
        ))}
      </div>

      <div className="row-between mt">
        <b>
          مجموع: {faNumber(total)}٪{" "}
          {total > 100 && (
            <span style={{ color: "var(--danger)" }}>⚠ بیش از ظرفیت</span>
          )}
        </b>
      </div>

      <div className="row mt">
        <Select
          options={projects.map((p) => [p.id, p.name])}
          value={project}
          onChange={(e) => setProject(e.target.value)}
          placeholder="افزودن تخصیص برای پروژه..."
          style={{ flex: 1 }}
        />
        <input
          type="number"
          className="input"
          style={{ width: 80 }}
          min="0"
          max="200"
          value={newPercent}
          onChange={(e) => setNewPercent(e.target.value)}
        />
        <span className="muted small">٪</span>
        <button
          className="btn"
          disabled={!project}
          onClick={() => {
            setValues((v) => ({ ...v, [project]: Number(newPercent) }));
            setProject("");
            setNewPercent(10);
          }}
        >
          افزودن
        </button>
      </div>

      <div className="form-actions">
        {rows.map((r) => (
          <button
            key={r.key}
            className="btn btn-sm"
            onClick={() => onSave(member.member_id, r.key, values[r.key] ?? 0)}
          >
            ذخیره: {r.label} = {faNumber(values[r.key] ?? 0)}٪
          </button>
        ))}
        <button className="btn" onClick={onClose}>
          بستن
        </button>
      </div>
    </Modal>
  );
}
