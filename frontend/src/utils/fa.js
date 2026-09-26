/** Persian helpers: numbers, dates. */

const FA_NUMS = "۰۱۲۳۴۵۶۷۸۹";

/** Convert any numeric value to a Persian digit string. */
export function faNumber(value) {
  if (value === null || value === undefined) return "";
  return String(value).replace(/[0-9]/g, (d) => FA_NUMS[Number(d)]);
}

/** "1405-06-30" or ISO date -> Persian calendar date (e.g. ۳۰ تیر ۱۴۰۵). */
export function faDate(value, withYear = true) {
  if (!value) return "—";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return "—";
  try {
    return new Intl.DateTimeFormat(
      "fa-IR",
      withYear
        ? { year: "numeric", month: "long", day: "numeric" }
        : { month: "long", day: "numeric" },
    ).format(d);
  } catch {
    return faNumber(d.toISOString().slice(0, 10));
  }
}

/** Short datetime in Persian (e.g. ۳۰ تیر ۱۴۰۵، ۱۰:۳۰). */
export function faDateTime(value) {
  if (!value) return "—";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return "—";
  try {
    return new Intl.DateTimeFormat("fa-IR", {
      month: "long",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    }).format(d);
  } catch {
    return faNumber(d.toISOString());
  }
}

/** Relative "x days ago" in Persian. */
export function faAgo(value) {
  if (!value) return "—";
  const d = new Date(value);
  const days = Math.max(0, Math.floor((Date.now() - d.getTime()) / 86400000));
  if (days === 0) return "امروز";
  if (days === 1) return "دیروز";
  return `${faNumber(days)} روز پیش`;
}
