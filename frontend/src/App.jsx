import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { useAuth } from "./context/AuthContext.jsx";
import Layout from "./components/Layout.jsx";
import { Spinner } from "./components/ui.jsx";
import { homeRoute, isExecutive } from "./utils/roles.js";
import Login from "./pages/Login.jsx";
import DeveloperDashboard from "./pages/DeveloperDashboard.jsx";
import ManagerDashboard from "./pages/ManagerDashboard.jsx";
import ScrumDashboard from "./pages/ScrumDashboard.jsx";
import DeputyDashboard from "./pages/DeputyDashboard.jsx";
import ProjectsPage from "./pages/ProjectsPage.jsx";
import ProjectDetailPage from "./pages/ProjectDetailPage.jsx";
import TasksPage from "./pages/TasksPage.jsx";
import BlockersPage from "./pages/BlockersPage.jsx";
import SupportPage from "./pages/SupportPage.jsx";
import IncomingPage from "./pages/IncomingPage.jsx";
import CapacityPage from "./pages/CapacityPage.jsx";
import WeeklyReportPage from "./pages/WeeklyReportPage.jsx";
import PriorityHistoryPage from "./pages/PriorityHistoryPage.jsx";
import AuditPage from "./pages/AuditPage.jsx";

function RequireRole({ roles, children }) {
  const { user } = useAuth();
  if (!user) return null;
  if (!roles.includes(user.role)) {
    return <Navigate to={homeRoute(user.role)} replace />;
  }
  return children;
}

export default function App() {
  const { user, loading } = useAuth();

  if (loading) {
    return <div className="loading-screen">در حال بارگذاری TechFlow...</div>;
  }
  if (!user) {
    return (
      <Routes>
        <Route path="*" element={<Login />} />
      </Routes>
    );
  }

  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Navigate to={homeRoute(user.role)} replace />} />
        <Route path="/dev" element={<DeveloperDashboard />} />
        <Route
          path="/manager"
          element={
            <RequireRole roles={["team_manager", "admin"]}>
              <ManagerDashboard />
            </RequireRole>
          }
        />
        <Route
          path="/scrum"
          element={
            <RequireRole roles={["scrum_master", "admin"]}>
              <ScrumDashboard />
            </RequireRole>
          }
        />
        <Route
          path="/deputy"
          element={
            <RequireRole roles={["deputy", "admin"]}>
              <DeputyDashboard />
            </RequireRole>
          }
        />
        <Route path="/projects" element={<ProjectsPage />} />
        <Route path="/projects/:id" element={<ProjectDetailPage />} />
        <Route path="/tasks" element={<TasksPage />} />
        <Route path="/blockers" element={<BlockersPage />} />
        <Route path="/support" element={<SupportPage />} />
        <Route path="/incoming" element={<IncomingPage />} />
        <Route path="/capacity" element={<CapacityPage />} />
        <Route
          path="/report"
          element={
            <RequireRole
              roles={["admin", "deputy", "team_manager", "scrum_master"]}
            >
              <WeeklyReportPage />
            </RequireRole>
          }
        />
        <Route
          path="/priority-history"
          element={
            <RequireRole
              roles={["admin", "deputy", "team_manager", "scrum_master"]}
            >
              <PriorityHistoryPage />
            </RequireRole>
          }
        />
        <Route
          path="/audit"
          element={
            <RequireRole
              roles={["admin", "deputy", "team_manager", "scrum_master"]}
            >
              <AuditPage />
            </RequireRole>
          }
        />
        <Route
          path="*"
          element={<Navigate to={homeRoute(user.role)} replace />}
        />
      </Route>
    </Routes>
  );
}
