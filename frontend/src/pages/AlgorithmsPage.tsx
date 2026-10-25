import { ArrowUpRight, Search } from "lucide-react";
import { Link } from "react-router-dom";
import { useEffect, useState } from "react";
import { getAlgorithms } from "../api";
import type { AlgorithmMetadata } from "../types";
import { SectionHeading } from "../components/SectionHeading";

export function AlgorithmsPage() {
  const [algorithms, setAlgorithms] = useState<AlgorithmMetadata[]>([]);
  const [query, setQuery] = useState("");
  useEffect(() => { getAlgorithms().then(setAlgorithms).catch(() => setAlgorithms([])); }, []);
  const cards = algorithms.filter((algorithm) => `${algorithm.name} ${algorithm.category}`.toLowerCase().includes(query.toLowerCase()));
  return <section className="page-width section page-top"><SectionHeading eyebrow="ALGORITHM LIBRARY" title="Explore the systems behind the decisions." body="A growing catalogue of interactive, inspectable AI algorithms. Start with the first production slice: A* grid pathfinding." /><div className="library-toolbar"><div className="search-field"><Search size={16} /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search algorithms" /></div><span className="mono">{cards.length.toString().padStart(2, "0")} MODULES</span></div><div className="algorithm-list">{cards.map((algorithm, index) => <article className="algorithm-card" key={algorithm.id}><div className="card-index">0{index + 1}</div><div className="algorithm-card-content"><div className="eyebrow">{algorithm.category} · {algorithm.difficulty}</div><h3>{algorithm.name}</h3><p>{algorithm.description}</p><Link className="text-link" to={`/algorithms/${algorithm.id}`}>View module <ArrowUpRight size={14} /></Link></div><div className="card-chip">{algorithm.visualization_type}</div></article>)}{cards.length === 0 && <div className="empty-state">The catalog endpoint is unavailable or no algorithms match this search. Start the backend to load the registry.</div>}</div></section>;
}
