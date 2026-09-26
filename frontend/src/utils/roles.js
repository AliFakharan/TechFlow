/** Role helpers for the frontend (mirrors backend core.constants). */

export const ROLE = {
  ADMIN: "admin",
  DEPUTY: "deputy",
  TEAM_MANAGER: "team_manager",
  SCRUM_MASTER: "scrum_master",
  DEVELOPER: "developer",
};

/** Can change a project priority (admin, team manager, deputy). */
export const canChangePriority = (role) =>
  ["admin", "team_manager", "deputy"].includes(role);

/** Can make management decisions: status, expected completion,
 *  assignments, project creation (admin, team manager). */
export const canManageProjects = (role) =>
  ["admin", "team_manager"].includes(role);

/** Operations roles: record operational data for the whole team. */
export const isOps = (role) =>
  ["admin", "team_manager", "scrum_master"].includes(role);

/** Executive read roles: dashboards, reports, history. */
export const isExecutive = (role) =>
  ["admin", "deputy", "team_manager", "scrum_master"].includes(role);

/** Home route by role. */
export const homeRoute = (role) => {
  switch (role) {
    case "team_manager":
      return "/manager";
    case "scrum_master":
      return "/scrum";
    case "deputy":
      return "/deputy";
    case "admin":
      return "/manager";
    default:
      return "/dev";
  }
};
