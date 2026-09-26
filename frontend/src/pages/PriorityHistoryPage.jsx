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
  PriorityBadge,
  faNumber,
  faDateTime,
} from "../components/ui.jsx";

export default function PriorityHistoryPage() {
  const [rows, setRows] = useState(null);
  const [error, setError] = useState("");
  const [project, setProject] = useState("");
  const [projects, setProjects] = useState([]);

  const load = useCallback(() => {
    const p = new URLSearchParams();
    if (project) p.set("project", project);
    api
      .list(`/api/priority-changes/?${p.toString()}`)
      .then(setRows)
      .catch((e) => setError(e.message));
  }, [project]);
  useEffect(load, [load]);

  useEffect(() => {
    api
      .list("/api/projects/")
      .then(setProjects)
      .catch(() => {});
  }, []);

  return (
    <>
      <PageHead
        title="تاریخچه تغییرات اولویت"
        subtitle="هر تغییر اولویت با دلیل، اثر و تغییردهنده ثبت می‌شود — تا مبادلات مدیریتی شفاف بمانند، نه برای سرزنش."
      />

      <Card tight>
        <div className="filter-bar">
          <select
            className="input"
            value={project}
            onChange={(e) => setProject(e.target.value)}
            style={{ minWidth: 220 }}
          >
            <option value="">همه پروژه‌ها</option>
            {projects.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>
          <span className="muted small grow" style={{ textAlign: "left" }}>
            {rows ? `${faNumber(rows.length)} تغییر ثبت‌شده` : ""}
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
            <Empty>تغییر اولویتی ثبت نشده است.</Empty>
          ) : (
            <Table
              headers={[
                "پروژه",
                "از",
                "به",
                "تغییردهنده",
                "دلیل",
                "اثر",
                "تاریخ",
              ]}
            >
              {rows.map((c) => (
                <tr key={c.id}>
                  <td>
                    <Link to={`/projects/${c.project}`}>
                      <b>{c.project_name}</b>
                    </Link>
                  </td>
                  <td>
                    <PriorityBadge value={c.old_priority} />
                  </td>
                  <td>
                    <PriorityBadge value={c.new_priority} />
                  </td>
                  <td className="muted small">{c.changed_by_name || "—"}</td>
                  <td className="muted small">{c.reason || "—"}</td>
                  <td className="muted small">{c.impact || "—"}</td>
                  <td className="muted small">{faDateTime(c.created_at)}</td>
                </tr>
              ))}
            </Table>
          ))}
      </Card>
    </>
  );
}
