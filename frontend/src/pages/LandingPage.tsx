import { ArrowRight, BarChart3, GitBranch, Play, Sparkles } from "lucide-react";
import { Link } from "react-router-dom";
import { SectionHeading } from "../components/SectionHeading";

export function LandingPage() {
  return <>
    <section className="hero page-width">
      <div className="hero-copy"><span className="eyebrow">INTERACTIVE AI EDUCATION PLATFORM <span className="status-dot" /></span><h1>Understand AI algorithms by <em>watching them think.</em></h1><p>Explore the internal decisions behind search, optimization, and game-playing algorithms through real, replayable execution—not pre-recorded animations.</p><div className="hero-actions"><Link className="button button-dark" to="/visualizer/astar-grid">Try A* grid <ArrowRight size={16} /></Link><Link className="text-link" to="/algorithms">Browse the library</Link></div></div>
      <div className="hero-visual"><div className="visual-header"><span><span className="status-dot" /> LIVE ENGINE PREVIEW</span><span className="mono">A* / 01</span></div><div className="mini-grid">{Array.from({ length: 120 }, (_, i) => <span key={i} className={i === 24 || i === 97 ? "mini-cell endpoint" : [34,35,36,47,59,71,72,73,84].includes(i) ? "mini-cell wall" : [25,26,27,28,29,41,53,65,77,89,101].includes(i) ? "mini-cell trail" : "mini-cell"} />)}</div><div className="visual-footer"><span>Finding an optimal route</span><span className="mono">f(n) = g(n) + h(n)</span></div></div>
    </section>
    <section className="stats-strip"><div><strong>01</strong><span>shared event engine</span></div><div><strong>20</strong><span>planned algorithm modules</span></div><div><strong>∞</strong><span>ways to learn by doing</span></div></section>
    <section className="page-width section"><SectionHeading eyebrow="WHY THIS EXISTS" title="See the reasoning, not just the answer." body="Every visual state is generated from the backend algorithm engine. Inspect frontiers, heuristics, costs, cutoffs, and decisions at your own pace." /><div className="feature-grid"><article><GitBranch size={20} /><h3>Replayable by design</h3><p>Pause, step, rewind, and inspect any event in the execution timeline.</p></article><article><BarChart3 size={20} /><h3>Metrics with meaning</h3><p>Compare frontier size, nodes expanded, solution quality, and runtime signals.</p></article><article><Sparkles size={20} /><h3>Learn in context</h3><p>Educational annotations explain why the algorithm selected its next move.</p></article></div></section>
    <section className="callout page-width"><div><span className="eyebrow">START WITH THE CORE PATTERN</span><h2>One engine. Many algorithms.</h2><p>Build intuition with A* today, then carry the same mental model into greedy search, hill climbing, alpha-beta, and annealing.</p></div><Link className="button button-light" to="/learn">Open learning center <Play size={15} /></Link></section>
  </>;
}
