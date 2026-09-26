import React, { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client.js";
import { PageHead, ErrorBox, Spinner } from "../components/ui.jsx";
import TeamDashboardBody from "./TeamDashboardBody.jsx";

export default function ScrumDashboard() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  const load = useCallback(() => {
    api
      .get("/api/dashboard/?view=scrum")
      .then(setData)
      .catch((e) => setError(e.message));
  }, []);
  useEffect(load, [load]);

  return (
    <>
      <PageHead
        title="پیشخوان اسکرم مستر"
        subtitle="کاکپیت عملیاتی تیم: کارها، موانع، پشتیبانی، رویدادهای اخیر."
        actions={
          <>
            <Link to="/blockers?open=1" className="btn">
              موانع باز
            </Link>
            <Link to="/report" className="btn btn-primary">
              📈 گزارش هفتگی
            </Link>
          </>
        }
      />
      {error && <ErrorBox>{error}</ErrorBox>}
      {!data && !error && <Spinner />}
      {data && <TeamDashboardBody data={data} showEvents />}
    </>
  );
}
