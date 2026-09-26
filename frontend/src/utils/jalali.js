/**
 * Jalali (Shamsi) calendar helpers — zero dependency.
 *
 * Conversions use the browser/Node `Intl` Persian calendar, which is
 * guaranteed-correct (ICU). `formatToParts` gives the exact jY/jM/jD of any
 * Gregorian date; the reverse (jY/jM/jD -> Date) is done by anchoring at the
 * Persian New Year (Farvardin 1) and stepping whole calendar days.
 *
 * Everything uses the local timezone (Asia/Tehran) consistently, and ISO
 * dates are treated as *calendar* dates (local, not UTC) to avoid ±1-day
 * shifts.
 */

const FA = "۰۱۲۳۴۵۶۷۸۹";
export const toFa = (n) => String(n).replace(/[0-9]/g, (c) => FA[Number(c)]);

export const J_PERSIAN_MONTHS = [
  "فروردین",
  "اردیبهشت",
  "خرداد",
  "تیر",
  "مرداد",
  "شهریور",
  "مهر",
  "آبان",
  "آذر",
  "دی",
  "بهمن",
  "اسفند",
];
export const J_WEEKDAYS = ["ش", "ی", "د", "س", "چ", "پ", "ج"];

// One cached formatter does the heavy lifting.
const jFormatter = new Intl.DateTimeFormat("en-u-ca-persian", {
  year: "numeric",
  month: "numeric",
  day: "numeric",
});

const _partsCache = new Map();
const partsCache = (date) => {
  const key = date.getTime();
  const hit = _partsCache.get(key);
  if (hit) return hit;
  let y = 0;
  let m = 1;
  let d = 1;
  for (const p of jFormatter.formatToParts(date)) {
    if (p.type === "year") y = Number(p.value);
    else if (p.type === "month") m = Number(p.value);
    else if (p.type === "day") d = Number(p.value);
  }
  const o = { y, m, d };
  if (_partsCache.size > 4000) _partsCache.clear();
  _partsCache.set(key, o);
  return o;
};

/** Local Jalali {y,m,d} of a Date. */
export const jalaliPartsOf = (date) => partsCache(date);

/** Today as local Jalali {y,m,d}. */
export const jalaliToday = () => jalaliPartsOf(new Date());

/** Add whole calendar days (local, DST-safe). */
export function addDays(date, n) {
  const d = new Date(date.getTime());
  d.setDate(d.getDate() + n);
  return d;
}

/** Farvardin 1 of Jalali year `y`, as a local Date (noon avoids DST edges).
 * Nowruz falls on March 20/21/22, so scan that small window each year. */
export function jalaliYearStart(y) {
  for (let g = y + 610; g < y + 640; g++) {
    for (let day = 18; day <= 23; day++) {
      const d = new Date(g, 2, day, 12, 0, 0);
      const p = partsCache(d);
      if (p.y === y && p.m === 1 && p.d === 1) return d;
    }
  }
  throw new Error("jalaliYearStart: year " + y + " not found");
}

/** First day of the month after `date` (same Jalali year). */
export function firstOfNextMonth(date) {
  const y = partsCache(date).y;
  let d = addDays(date, 1);
  for (let i = 0; i < 33; i++) {
    const p = partsCache(d);
    if (p.y === y && p.m === partsCache(date).m + 1) return d;
    d = addDays(d, 1);
  }
  return d;
}

/**
 * Jalali {y,m,d} -> ISO "YYYY-MM-DD" (local calendar date).
 * Returns "" for invalid input.
 */
/** First calendar day of Jalali month m (1-12) of year y. */
export function jalaliMonthStart(y, m) {
  let cur = jalaliYearStart(y);
  for (let mm = 1; mm < m; mm++) cur = firstOfNextMonth(cur);
  return cur;
}

export function jalaliToISO({ y, m, d }) {
  if (!y || !m || !d) return "";
  try {
    const target = addDays(jalaliMonthStart(y, m), d - 1);
    const p = partsCache(target);
    if (p.y !== y || p.m !== m || p.d !== d) return "";
    return `${target.getFullYear()}-${String(target.getMonth() + 1).padStart(2, "0")}-${String(
      target.getDate(),
    ).padStart(2, "0")}`;
  } catch {
    return "";
  }
}

/** ISO "YYYY-MM-DD" -> local Jalali {y,m,d} (or null). */
export function isoToJalali(iso) {
  if (!iso) return null;
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(String(iso));
  if (!m) return null;
  const d = new Date(Number(m[1]), Number(m[2]) - 1, Number(m[3]), 12, 0, 0);
  if (Number.isNaN(d.getTime())) return null;
  return partsCache(d);
}

/** "۱۴۰۴/۳/۲۵" (Persian digits). */
export function jalaliDisplay({ y, m, d }) {
  return `${toFa(y)}/${toFa(m)}/${toFa(d)}`;
}

/** "۲۵ اسفند ۱۴۰۴" (or "" when no date). */
export function jalaliLong(value) {
  const j = typeof value === "string" ? isoToJalali(value) : value;
  if (!j) return "";
  return `${toFa(j.d)} ${J_PERSIAN_MONTHS[j.m - 1]} ${toFa(j.y)}`;
}
