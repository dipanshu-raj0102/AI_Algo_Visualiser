import { useEffect, useState } from "react";
import { Link, NavLink } from "react-router-dom";
import { BrainCircuit, Menu, Moon, Sun, X } from "lucide-react";

const links = [
  ["Explore", "/algorithms"],
  ["Compare", "/comparison"],
  ["Learn", "/learn"],
  ["Dashboard", "/dashboard"],
  ["About", "/about"],
];

export function Layout({ children }: { children: React.ReactNode }) {
  const [open, setOpen] = useState(false);
  const [dark, setDark] = useState(false);
  useEffect(() => {
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") setOpen(false);
    };
    window.addEventListener("keydown", closeOnEscape);
    return () => window.removeEventListener("keydown", closeOnEscape);
  }, []);
  return (
    <div className={dark ? "app-shell dark" : "app-shell"}>
      <header className="topbar">
        <Link to="/" className="brand" onClick={() => setOpen(false)}>
          <span className="brand-mark" aria-hidden="true"><BrainCircuit size={19} /></span>
          <span>AI<span className="brand-muted">/</span>VISUALIZER</span>
        </Link>
        <nav id="primary-navigation" className={open ? "nav-links open" : "nav-links"} aria-label="Primary navigation">
          {links.map(([label, href]) => <NavLink key={href} to={href} onClick={() => setOpen(false)}>{label}</NavLink>)}
        </nav>
        <div className="topbar-actions">
          <button className="icon-button" type="button" aria-label={dark ? "Switch to light theme" : "Switch to dark theme"} aria-pressed={dark} onClick={() => setDark((value) => !value)}>{dark ? <Sun size={18} /> : <Moon size={18} />}</button>
          <Link className="button button-dark button-small" to="/visualizer/astar-grid">Launch workspace <span>↗</span></Link>
          <button className="icon-button mobile-menu" type="button" aria-label={open ? "Close navigation" : "Open navigation"} aria-expanded={open} aria-controls="primary-navigation" onClick={() => setOpen((value) => !value)}>{open ? <X size={19} /> : <Menu size={19} />}</button>
        </div>
      </header>
      <main>{children}</main>
      <footer className="footer"><span>AI Algorithm Visualizer</span><span className="mono">ENGINE/0.1 · EVENT DRIVEN</span></footer>
    </div>
  );
}
