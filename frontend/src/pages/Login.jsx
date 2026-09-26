import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";
import { homeRoute } from "../utils/roles.js";

export default function Login() {
  const { login, register } = useAuth();
  const navigate = useNavigate();

  const [tab, setTab] = useState("login"); // "login" | "register"
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  // login fields
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  // register fields
  const [regName, setRegName] = useState("");
  const [regUsername, setRegUsername] = useState("");
  const [regPassword, setRegPassword] = useState("");
  const [regEmail, setRegEmail] = useState("");

  const switchTab = (t) => {
    setTab(t);
    setError("");
  };

  const submitLogin = async (e) => {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      const user = await login(username, password);
      navigate(homeRoute(user.role), { replace: true });
    } catch (err) {
      setError(err.message || "ورود ناموفق بود.");
    } finally {
      setBusy(false);
    }
  };

  const submitRegister = async (e) => {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      const user = await register({
        username: regUsername,
        password: regPassword,
        full_name: regName,
        email: regEmail,
      });
      navigate(homeRoute(user.role), { replace: true });
    } catch (err) {
      // Flatten field errors for a friendly message.
      const msg =
        (err.data &&
          Object.entries(err.data)
            .filter(([, v]) => Array.isArray(v))
            .map(([, v]) => v[0])
            .join(" ")) ||
        err.message ||
        "ثبت‌نام ناموفق بود.";
      setError(msg);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="login-wrap">
      <div className="login-card">
        <div className="brand">
          <div className="logo">TechFlow</div>
          <div className="sub">سامانه عملیات و پایش تیم فناوری</div>
        </div>

        <div className="tabs">
          <button
            type="button"
            className={tab === "login" ? "tab active" : "tab"}
            onClick={() => switchTab("login")}
          >
            ورود
          </button>
          <button
            type="button"
            className={tab === "register" ? "tab active" : "tab"}
            onClick={() => switchTab("register")}
          >
            ثبت‌نام
          </button>
        </div>

        {tab === "login" ? (
          <form onSubmit={submitLogin}>
            <div className="field">
              <label>نام کاربری</label>
              <input
                className="input"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                autoFocus
                required
              />
            </div>
            <div className="field">
              <label>رمز عبور</label>
              <input
                className="input"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
            {error && <div className="error-box">{error}</div>}
            <div className="form-actions">
              <button
                className="btn btn-primary"
                type="submit"
                disabled={busy}
                style={{ width: "100%", justifyContent: "center" }}
              >
                {busy ? "در حال ورود..." : "ورود به سامانه"}
              </button>
            </div>
          </form>
        ) : (
          <form onSubmit={submitRegister}>
            <div className="field">
              <label>نام و نام خانوادگی</label>
              <input
                className="input"
                value={regName}
                onChange={(e) => setRegName(e.target.value)}
                autoFocus
                required
              />
            </div>
            <div className="field">
              <label>نام کاربری</label>
              <input
                className="input"
                value={regUsername}
                onChange={(e) => setRegUsername(e.target.value)}
                required
                minLength={3}
              />
            </div>
            <div className="field">
              <label>رمز عبور</label>
              <input
                className="input"
                type="password"
                value={regPassword}
                onChange={(e) => setRegPassword(e.target.value)}
                required
                minLength={8}
              />
              <small className="muted">حداقل ۸ کاراکتر</small>
            </div>
            <div className="field">
              <label>ایمیل (اختیاری)</label>
              <input
                className="input"
                type="email"
                value={regEmail}
                onChange={(e) => setRegEmail(e.target.value)}
              />
            </div>
            {error && <div className="error-box">{error}</div>}
            <div className="form-actions">
              <button
                className="btn btn-primary"
                type="submit"
                disabled={busy}
                style={{ width: "100%", justifyContent: "center" }}
              >
                {busy ? "در حال ثبت‌نام..." : "ثبت‌نام و ورود"}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
