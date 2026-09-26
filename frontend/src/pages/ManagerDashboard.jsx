import React, { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client.js";
import { PageHead, ErrorBox, Spinner } from "../components/ui.jsx";
import TeamDashboardBody from "./TeamDashboardBody.jsx";

export default function ManagerDashboard() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  const load = useCallback(() => {
    api
      .get("/api/dashboard/?view=manager")
      .then(setData)
      .catch((e) => setError(e.message));
  }, []);
  useEffect(load, [load]);

  return (
    <>
      <PageHead
        title="پیشخوان مدیر تیم"
        subtitle="وضعیت پروژه‌ها، موانع و ظرفیت تیم — با سیگنال‌های ریسک شفاف."
        actions={
          <>
            <Link to="/projects" className="btn">
              فهرست پروژه‌ها
            </Link>
            <Link to="/report" className="btn btn-primary">
              📈 گزارش هفتگی
            </Link>
          </>
        }
      />
      {error && <ErrorBox>{error}</ErrorBox>}
      {!data && !error && <Spinner />}
      {data && <TeamDashboardBody data={data} />}
    </>
  );
}
