import { ArrowUpRight, GitCompare, Search } from "lucide-react";
import { Link } from "react-router-dom";
import { useEffect, useMemo, useState } from "react";
import { getAlgorithms } from "../api";
import type { AlgorithmMetadata } from "../types";
import { SectionHeading } from "../components/SectionHeading";

export function AlgorithmsPage() {
  const [algorithms, setAlgorithms] = useState<AlgorithmMetadata[]>([]);
  const [query, setQuery] = useState("");
  const [catalogError, setCatalogError] = useState(false);
  useEffect(() => {
    getAlgorithms().then(setAlgorithms).catch(() => { setAlgorithms([]); setCatalogError(true); });
  }, []);
  const cards = algorithms.filter((algorithm) => `${algorithm.name} ${algorithm.category} ${algorithm.description}`.toLowerCase().includes(query.trim().toLowerCase()));
  const groups = useMemo(() => {
    const grouped = new Map<string, AlgorithmMetadata[]>();
    cards.forEach((algorithm) => {
      const category = algorithm.category || "Other algorithms";
      grouped.set(category, [...(grouped.get(category) ?? []), algorithm]);
    });
    return [...grouped.entries()];
  }, [cards]);
  const comparisonReady = algorithms.some((algorithm) => algorithm.supports_comparison);
  return <section className="page-width section page-top">
    <SectionHeading eyebrow="ALGORITHM LIBRARY" title="Explore the systems behind the decisions." body="Browse the registered engines, then open a module to inspect its real execution trace. Search by name, family, or concept." />
    <div className="library-toolbar" role="search">
      <label className="search-field"><Search size={16} aria-hidden="true" /><span className="sr-only">Search algorithms</span><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search algorithms" aria-label="Search algorithms" /></label>
      <span className="library-count mono" aria-live="polite">{cards.length.toString().padStart(2, "0")} MODULES</span>
    </div>
     {comparisonReady && <aside className="library-discovery" aria-label="Heuristic analysis"><div className="library-discovery-icon"><GitCompare size={18} /></div><div><strong>Want to see estimates change the search?</strong><p>Run Manhattan, Euclidean, Chebyshev, and Dijkstra on one shared problem.</p></div><Link className="text-link" to="/compare/astar-heuristics">Open heuristic analysis <ArrowUpRight size={14} /></Link></aside>}
    <div className="algorithm-groups">
      {groups.map(([category, categoryAlgorithms]) => <section className="algorithm-group" key={category} aria-labelledby={`group-${category.replace(/\W+/g, "-").toLowerCase()}`}>
        <div className="algorithm-group-heading"><div><span className="eyebrow">ALGORITHM FAMILY</span><h2 id={`group-${category.replace(/\W+/g, "-").toLowerCase()}`}>{category}</h2></div><span className="mono">{categoryAlgorithms.length.toString().padStart(2, "0")} MODULES</span></div>
        <div className="algorithm-list">{categoryAlgorithms.map((algorithm, index) => <article className="algorithm-card" key={algorithm.id}>
          <div className="card-index">{String(index + 1).padStart(2, "0")}</div>
          <div className="algorithm-card-content"><div className="eyebrow">{algorithm.difficulty}{algorithm.supports_step_execution ? " · STEP READY" : ""}</div><h3>{algorithm.name}</h3><p>{algorithm.description}</p><div className="algorithm-card-actions"><Link className="text-link" to={`/algorithms/${algorithm.id}`}>View module <ArrowUpRight size={14} /></Link>{algorithm.supports_comparison && <span className="card-capability"><GitCompare size={13} /> Comparable</span>}</div></div>
          <div className="card-chip">{algorithm.visualization_type}</div>
        </article>)}</div>
      </section>)}
      {cards.length === 0 && <div className="empty-state">{catalogError ? "The catalog endpoint is unavailable. Start the backend to load the registered algorithms." : "No registered algorithms match this search."}</div>}
    </div>
  </section>;
}
