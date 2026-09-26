import React, { useEffect, useMemo, useRef, useState } from "react";
import {
  isoToJalali,
  jalaliToISO,
  jalaliLong,
  jalaliMonthStart,
  jalaliPartsOf,
  jalaliToday,
  addDays,
  toFa,
  J_PERSIAN_MONTHS,
  J_WEEKDAYS,
} from "../utils/jalali.js";

/**
 * Jalali (Shamsi) date picker.
 *
 * Props:
 *   value    — ISO "YYYY-MM-DD" string or "" (what the API uses)
 *   onChange — called with the ISO string (or "" when cleared)
 *
 * The visible control is a text input showing e.g. «۳ مهر ۱۴۰۵» so it works in
 * every browser (no reliance on native Persian calendars). A popover calendar
 * — built on Intl's guaranteed-correct Persian calendar — lets the user pick
 * the date by clicking or by typing "YYYY/MM/DD".
 */
export default function JalaliDateField({
  value,
  onChange,
  name,
  id,
  ...rest
}) {
  const [open, setOpen] = useState(false);
  const [draft, setDraft] = useState(""); // free text while editing

  const boxRef = useRef(null);
  const jVal = useMemo(() => isoToJalali(value), [value]);
  const today = useMemo(() => jalaliToday(), []);
  const [view, setView] = useState(() =>
    jVal ? { y: jVal.y, m: jVal.m } : { y: today.y, m: today.m },
  );
  const [picked, setPicked] = useState(null); // {y,m,d}

  // When closed, the input shows either the selected date or the free text.
  useEffect(() => {
    if (!open) setDraft(jVal ? jalaliLong(jVal) : "");
  }, [open, jVal]);

  // Close on outside click / Escape.
  useEffect(() => {
    if (!open) return;
    const onDown = (e) => {
      if (boxRef.current && !boxRef.current.contains(e.target)) setOpen(false);
    };
    const onKey = (e) => {
      if (e.key === "Escape") setOpen(false);
    };
    document.addEventListener("mousedown", onDown);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDown);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  const startEdit = () => {
    setPicked(null);
    setView(jVal ? { y: jVal.y, m: jVal.m } : { y: today.y, m: today.m });
    setOpen(true);
  };

  const commitPicked = (j) => {
    setPicked(j);
    const iso = jalaliToISO(j);
    if (iso) onChange(iso);
    setOpen(false);
  };

  const clear = () => {
    setPicked(null);
    setDraft("");
    onChange("");
  };

  const applyText = () => {
    const norm = draft.replace(/[۰-۹]/g, (c) =>
      String("۰۱۲۳۴۵۶۷۸۹".indexOf(c)),
    );
    const m = /^(\d{4})[/\-.](\d{1,2})[/\-.](\d{1,2})$/.exec(norm.trim());
    if (m) {
      const j = { y: +m[1], m: +m[2], d: +m[3] };
      if (jalaliToISO(j)) {
        commitPicked(j);
        return;
      }
    }
    // Not a valid Jalali date — revert to the committed value.
    setDraft(jVal ? jalaliLong(jVal) : "");
    setOpen(false);
  };

  const showToday = () => {
    setPicked(today);
    setView({ y: today.y, m: today.m });
  };

  return (
    <div className="jdate" ref={boxRef}>
      <input
        className="input jdate-input"
        dir="rtl"
        type="text"
        name={name}
        id={id}
        value={draft}
        placeholder="انتخاب تاریخ (تقویم شمسی)"
        onFocus={(e) => {
          startEdit();
          setTimeout(() => e.target.select(), 0);
        }}
        onChange={(e) => setDraft(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter") applyText();
        }}
        {...rest}
      />
      <button
        type="button"
        className="jdate-clear"
        title="پاک کردن"
        onClick={(e) => {
          e.stopPropagation();
          clear();
        }}
      >
        ×
      </button>

      {open && (
        <div className="jdate-pop" dir="rtl">
          <div className="jdate-head">
            <button
              type="button"
              title="ماه بعد"
              onClick={() => shiftMonth(view, +1)}
            >
              ‹
            </button>
            <div className="jdate-title">
              <select
                value={view.m}
                onChange={(e) => setView((v) => ({ ...v, m: +e.target.value }))}
              >
                {J_PERSIAN_MONTHS.map((mo, i) => (
                  <option key={mo} value={i + 1}>
                    {mo}
                  </option>
                ))}
              </select>
              <select
                value={view.y}
                onChange={(e) => setView((v) => ({ ...v, y: +e.target.value }))}
              >
                {yearOptions(view.y).map((y) => (
                  <option key={y} value={y}>
                    {toFa(y)}
                  </option>
                ))}
              </select>
            </div>
            <button
              type="button"
              title="ماه قبل"
              onClick={() => shiftMonth(view, -1)}
            >
              ›
            </button>
          </div>

          <div className="jdate-grid">
            {weekdayOrder.map((i) => (
              <div key={i} className="jdate-wd">
                {J_WEEKDAYS[i]}
              </div>
            ))}
            {dayCells(view, today, jVal, picked, commitPicked)}
          </div>

          <div className="jdate-foot">
            <button type="button" className="btn" onClick={showToday}>
              امروز
            </button>
            <button type="button" className="btn" onClick={clear}>
              پاک کردن
            </button>
            <button
              type="button"
              className="btn btn-primary"
              onClick={applyText}
            >
              تأیید
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

// Sunday-first header (J_WEEKDAYS is indexed Sat=0 … Fri=6).
const weekdayOrder = [1, 2, 3, 4, 5, 6, 0];

function shiftMonth(view, dir) {
  let { y, m } = view;
  m += dir;
  if (m < 1) {
    m = 12;
    y -= 1;
  } else if (m > 12) {
    m = 1;
    y += 1;
  }
  return { y, m };
}

function yearOptions(center) {
  const list = [];
  for (let y = center - 10; y <= center + 10; y++) list.push(y);
  return list;
}

function dayCells(view, today, selected, picked, onPick) {
  const cells = [];
  const firstDate = jalaliMonthStart(view.y, view.m);
  for (let i = 0; i < firstDate.getDay(); i++)
    cells.push(<div key={`b${i}`} className="jdate-cell" />);

  let d = firstDate;
  let guard = 0;
  while (guard++ < 42) {
    const p = jalaliPartsOf(d);
    if (p.y !== view.y || p.m !== view.m) break;
    const isToday = p.y === today.y && p.m === today.m && p.d === today.d;
    const isSel =
      (picked && picked.y === p.y && picked.m === p.m && picked.d === p.d) ||
      (selected &&
        selected.y === p.y &&
        selected.m === p.m &&
        selected.d === p.d);
    cells.push(
      <button
        key={p.d}
        type="button"
        className={`jdate-cell${isSel ? " sel" : ""}${isToday ? " today" : ""}`}
        onClick={() => onPick({ y: p.y, m: p.m, d: p.d })}
      >
        {toFa(p.d)}
      </button>,
    );
    d = addDays(d, 1);
  }
  return cells;
}
