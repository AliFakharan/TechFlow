/** Persian labels for all backend enum values. */

export const ROLE_LABELS = {
  admin: "مدیر سیستم",
  deputy: "معاون فناوری",
  team_manager: "مدیر تیم",
  scrum_master: "اسکرم مستر",
  developer: "توسعه‌دهنده",
};

export const PROJECT_STATUS_LABELS = {
  planned: "برنامه‌ریزی‌شده",
  active: "فعال",
  blocked: "مسدود",
  testing: "تست",
  bug_fixing: "رفع باگ",
  done: "انجام‌شده",
  paused: "توقف‌خورده",
  cancelled: "لغو‌شده",
};

export const RISK_LABELS = {
  on_track: "در مسیر",
  at_risk: "در معرض ریسک",
  blocked: "مسدود",
};

export const PRIORITY_LABELS = {
  low: "کم",
  medium: "متوسط",
  high: "زیاد",
  critical: "بحرانی",
};

export const TASK_STATUS_LABELS = {
  todo: "انجام‌نشده",
  in_progress: "در حال انجام",
  blocked: "مسدود",
  done: "انجام‌شده",
};

export const WORK_TYPE_LABELS = {
  feature: "توسعه",
  bug: "باگ",
  support: "پشتیبانی",
  change_request: "درخواست تغییر",
  emergency: "اورژانسی",
};

export const BLOCKER_STATUS_LABELS = {
  open: "باز",
  resolved: "رفع‌شده",
};

export const BLOCKER_CATEGORY_LABELS = {
  requirement_ambiguity: "دو‌معنا بودن نیازمندی",
  waiting_analysis: "در انتظار تحلیل",
  waiting_client: "در انتظار کلاینت",
  technical: "مسئله فنی",
  environment: "محیط/انتشار",
  dependency: "وابستگی",
  management_decision: "تصمیم مدیریتی",
  other: "سایر",
};

export const SUPPORT_STATUS_LABELS = {
  new: "جدید",
  assigned: "تعیین‌مسئول‌شده",
  in_progress: "در حال انجام",
  waiting: "در انتظار",
  resolved: "حل‌شده",
  closed: "بسته",
};

export const INCOMING_STATUS_LABELS = {
  new: "جدید",
  evaluating: "در حال بررسی",
  accepted: "پذیرفته‌شده",
  rejected: "رد‌شده",
  converted_task: "تبدیل به وظیفه",
  converted_support: "تبدیل به پشتیبانی",
  converted_project: "تبدیل به پروژه",
};

export const AUDIT_ACTION_LABELS = {
  project_created: "ایجاد پروژه",
  project_updated: "به‌روزرسانی پروژه",
  project_status_changed: "تغییر وضعیت پروژه",
  priority_changed: "تغییر اولویت",
  expected_completion_changed: "تغییر تاریخ اتمام",
  member_assigned: "افزودن عضو",
  member_removed: "حذف عضو",
  task_created: "ایجاد وظیفه",
  task_status_changed: "تغییر وضعیت وظیفه",
  task_assigned: "تعیین مسئول وظیفه",
  blocker_created: "ثبت مانع",
  blocker_resolved: "رفع مانع",
  support_created: "ایجاد تیکت پشتیبانی",
  support_status_changed: "تغییر وضعیت تیکت",
  capacity_updated: "تغییر تخصیص ظرفیت",
  incoming_work_created: "ثبت کار ورودی",
  incoming_work_converted: "تبدیل کار ورودی",
  member_role_changed: "تغییر نقش",
};

export const STATUS_COLORS = {
  // project status
  planned: "badge-gray",
  active: "badge-blue",
  blocked: "badge-red",
  testing: "badge-purple",
  bug_fixing: "badge-orange",
  done: "badge-green",
  paused: "badge-gray",
  cancelled: "badge-gray",
  // risk
  on_track: "badge-green",
  at_risk: "badge-orange",
  // task
  todo: "badge-gray",
  in_progress: "badge-blue",
  done: "badge-green",
  // support
  new: "badge-gray",
  assigned: "badge-blue",
  waiting: "badge-orange",
  resolved: "badge-green",
  closed: "badge-gray",
};

export const PRIORITY_COLORS = {
  low: "badge-gray",
  medium: "badge-blue",
  high: "badge-orange",
  critical: "badge-red",
};
