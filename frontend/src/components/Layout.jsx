import React from "react";
import { NavLink, useLocation, Outlet } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";
import { ROLE_LABELS } from "../utils/labels.js";
import { isOps, isExecutive } from "../utils/roles.js";

const NAV = [
  {
    section: "پیشخوان",
    items: [
      { to: "/dev", label: "پیشخوان من", icon: "👤", show: () => true },
      {
        to: "/manager",
        label: "پیشخوان مدیر تیم",
        icon: "📊",
        show: (r) => r === "team_manager" || r === "admin",
      },
      {
        to: "/scrum",
        label: "پیشخوان اسکرم",
        icon: "🧭",
        show: (r) => r === "scrum_master" || r === "admin",
      },
      {
        to: "/deputy",
        label: "پیشخوان معاون",
        icon: "🏛️",
        show: (r) => isExecutive(r),
      },
    ],
  },
  {
    section: "عملیات",
    items: [
      { to: "/projects", label: "پروژه‌ها", icon: "📁", show: () => true },
      { to: "/tasks", label: "وظایف", icon: "✅", show: () => true },
      { to: "/blockers", label: "موانع", icon: "🚧", show: () => true },
      { to: "/support", label: "پشتیبانی", icon: "🎧", show: () => true },
      { to: "/incoming", label: "کارهای ورودی", icon: "📥", show: () => true },
    ],
  },
  {
    section: "پایش و گزارش",
    items: [
      { to: "/capacity", label: "ظرفیت", icon: "📐", show: () => true },
      {
        to: "/report",
        label: "گزارش هفتگی",
        icon: "📈",
        show: (r) => isExecutive(r),
      },
      {
        to: "/priority-history",
        label: "تاریخچه اولویت‌ها",
        icon: "🔀",
        show: (r) => isExecutive(r),
      },
      {
        to: "/audit",
        label: "گزارش وقایع",
        icon: "🕓",
        show: (r) => isExecutive(r),
      },
    ],
  },
];

export default function Layout() {
  const { user, logout } = useAuth();
  const location = useLocation();
  const role = user?.role || "developer";

  const initials = (user?.full_name || user?.username || "؟")
    .split(" ")
    .map((s) => s[0])
    .slice(0, 2)
    .join("");

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <div className="brand-title">TechFlow</div>
          <div className="brand-sub">سامانه عملیات و پایش تیم فناوری</div>
        </div>
        <nav className="sidebar-nav">
          {NAV.map((group) => {
            const items = group.items.filter((i) => i.show(role));
            if (!items.length) return null;
            return (
              <div key={group.section}>
                <div className="nav-section">{group.section}</div>
                {items.map((i) => (
                  <NavLink
                    key={i.to}
                    to={i.to}
                    className={({ isActive }) =>
                      `nav-item ${isActive ? "active" : ""}`
                    }
                  >
                    <span className="nav-icon">{i.icon}</span>
                    {i.label}
                  </NavLink>
                ))}
              </div>
            );
          })}
        </nav>
        <div className="sidebar-foot">
          <div className="name">{user?.full_name || user?.username}</div>
          <div className="role">{ROLE_LABELS[role] || role}</div>
          <button
            className="btn btn-ghost btn-sm"
            style={{ marginTop: 6 }}
            onClick={logout}
          >
            خروج از سامانه
          </button>
        </div>
      </aside>
      <div className="main">
        <header className="topbar">
          <div className="crumb">
            {NAV.flatMap((g) => g.items).find((i) => location.pathname === i.to)
              ?.label || "TechFlow"}
          </div>
          <div className="user-chip">
            <span>{user?.team_name || "تیم"}</span>
            <span className="avatar">{initials}</span>
          </div>
        </header>
        <main className="content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
