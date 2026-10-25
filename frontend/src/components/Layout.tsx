import { useState } from "react";
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
  return (
    <div className={dark ? "app-shell dark" : "app-shell"}>
      <header className="topbar">
        <Link to="/" className="brand" onClick={() => setOpen(false)}>
          <span className="brand-mark"><BrainCircuit size={19} /></span>
          <span>AI<span className="brand-muted">/</span>VISUALIZER</span>
        </Link>
        <nav className={open ? "nav-links open" : "nav-links"}>
          {links.map(([label, href]) => <NavLink key={href} to={href} onClick={() => setOpen(false)}>{label}</NavLink>)}
        </nav>
        <div className="topbar-actions">
          <button className="icon-button" aria-label="Toggle colour theme" onClick={() => setDark((value) => !value)}>{dark ? <Sun size={18} /> : <Moon size={18} />}</button>
          <Link className="button button-dark button-small" to="/visualizer/astar-grid">Launch workspace <span>↗</span></Link>
          <button className="icon-button mobile-menu" aria-label="Toggle navigation" onClick={() => setOpen((value) => !value)}>{open ? <X size={19} /> : <Menu size={19} />}</button>
        </div>
      </header>
      <main>{children}</main>
      <footer className="footer"><span>AI Algorithm Visualizer</span><span className="mono">ENGINE/0.1 · EVENT DRIVEN</span></footer>
    </div>
  );
}
