import { useEffect, useState } from "react";
import { Link, NavLink, useLocation } from "react-router-dom";
import { applyTheme, getStoredTheme, type ThemeMode } from "../lib/theme";
import { useDevice } from "./DeviceContext";
import { IconGithub, IconMenu, IconMonitor, IconMoon, IconSun, Logo } from "./Icons";

export const REPO_URL = "https://github.com/nxtkim-1/hand-dynamometer";

const LINKS = [
  { to: "/", label: "Project", end: true },
  { to: "/test", label: "Grip test" },
  { to: "/results", label: "Results" },
  { to: "/how-it-works", label: "How it works" },
];

const NEXT_THEME: Record<ThemeMode, ThemeMode> = {
  auto: "light",
  light: "dark",
  dark: "auto",
};

const THEME_LABEL: Record<ThemeMode, string> = {
  auto: "System theme",
  light: "Light theme",
  dark: "Dark theme",
};

export function Header() {
  const { status } = useDevice();
  const [open, setOpen] = useState(false);
  const [theme, setTheme] = useState<ThemeMode>(getStoredTheme);
  const { pathname } = useLocation();
  useEffect(() => setOpen(false), [pathname]);

  function cycleTheme() {
    const next = NEXT_THEME[theme];
    setTheme(next);
    applyTheme(next);
  }

  return (
    <header className="site-header">
      <div className="container">
        <Link to="/" className="brand" aria-label="GripCheck home">
          <Logo />
          GripCheck
        </Link>
        <nav id="site-nav" className={`nav${open ? " open" : ""}`} aria-label="Main">
          {LINKS.map((l) => (
            <NavLink key={l.to} to={l.to} end={l.end} className={({ isActive }) => (isActive ? "active" : undefined)}>
              {l.label}
            </NavLink>
          ))}
        </nav>
        <div className="header-actions">
          <Link to="/test" className={`device-pill${status === "connected" ? " on" : ""}`} title="Dynamometer connection">
            <span className="dot" aria-hidden="true" />
            {status === "connected" ? "Device connected" : "No device"}
          </Link>
          <button
            type="button"
            className="btn btn-ghost icon-btn"
            onClick={cycleTheme}
            title={`${THEME_LABEL[theme]} (click to switch)`}
            aria-label={`${THEME_LABEL[theme]} (click to switch)`}
          >
            {theme === "light" ? <IconSun /> : theme === "dark" ? <IconMoon /> : <IconMonitor />}
          </button>
        </div>
        <button
          className="btn btn-ghost menu-btn"
          aria-label="Menu"
          aria-expanded={open}
          aria-controls="site-nav"
          onClick={() => setOpen((o) => !o)}
        >
          <IconMenu />
        </button>
      </div>
    </header>
  );
}

export function Footer() {
  return (
    <footer className="site-footer">
      <div className="container">
        <div style={{ display: "grid", gap: 12 }}>
          <Link to="/" className="brand" style={{ color: "var(--ink)" }}>
            <Logo size={24} />
            GripCheck
          </Link>
          <p>
            An open, 3D-printed grip dynamometer and the software that runs it. Educational project: not a medical
            device, and not for diagnosis.
          </p>
          <p className="small">Software MIT. Hardware, docs and images CC BY 4.0.</p>
        </div>
        <div>
          <h3>Site</h3>
          <ul>
            {LINKS.map((l) => (
              <li key={l.to}>
                <Link to={l.to}>{l.label}</Link>
              </li>
            ))}
            <li>
              <Link to="/results/sample-demo">Sample report</Link>
            </li>
          </ul>
        </div>
        <div>
          <h3>Source</h3>
          <ul>
            <li>
              <a href={REPO_URL} target="_blank" rel="noreferrer" style={{ display: "inline-flex", gap: 6, alignItems: "center" }}>
                <IconGithub size={15} /> hand-dynamometer
              </a>
            </li>
            <li>
              <a href="https://doi.org/10.1371/journal.pone.0113637" target="_blank" rel="noreferrer">
                Dodds et al. (2014) norms
              </a>
            </li>
          </ul>
        </div>
      </div>
    </footer>
  );
}
