export function EditorialRiftVisual({ compact = false }: { compact?: boolean }) {
  return (
    <figure className={`v2-rift${compact ? " v2-rift--compact" : ""}`}>
      <svg viewBox="0 0 860 520" role="img" aria-labelledby="v2-rift-title v2-rift-desc">
        <title id="v2-rift-title">The Capability–Deployment–Effect Rift</title>
        <desc id="v2-rift-desc">A restrained landscape showing capability and deployment on the left, a sequence of uncertain bridges across a rift, and behavioural and democratic consequences on the right.</desc>
        <defs>
          <linearGradient id="v2-sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#fbfaf6" /><stop offset="1" stopColor="#ece8df" /></linearGradient>
          <linearGradient id="v2-cliff-left" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#d7ded8" /><stop offset="1" stopColor="#66736d" /></linearGradient>
          <linearGradient id="v2-cliff-mid" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#eadfca" /><stop offset="1" stopColor="#9b7440" /></linearGradient>
          <linearGradient id="v2-cliff-right" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#eadbdd" /><stop offset="1" stopColor="#864353" /></linearGradient>
          <filter id="v2-shadow" x="-30%" y="-30%" width="160%" height="180%"><feDropShadow dx="0" dy="11" stdDeviation="10" floodOpacity=".15" /></filter>
        </defs>
        <rect width="860" height="520" rx="18" fill="url(#v2-sky)" />
        <g className="v2-rift-headings">
          <text x="92" y="54">Capability</text><line x1="178" y1="49" x2="244" y2="49" /><path d="M238 43 L246 49 L238 55" />
          <text x="268" y="54">Deployment</text><line x1="366" y1="49" x2="433" y2="49" /><path d="M427 43 L435 49 L427 55" />
          <text x="478" y="54">Behavioural effect</text><line x1="615" y1="49" x2="672" y2="49" /><path d="M666 43 L674 49 L666 55" />
          <text x="696" y="54">Democratic consequence</text>
        </g>
        <g filter="url(#v2-shadow)">
          <path d="M34 350 C47 274 58 177 94 119 C129 91 204 91 242 126 C264 178 255 282 268 350 L234 452 L79 452Z" fill="url(#v2-cliff-left)" />
          <path d="M271 344 C282 254 291 196 323 155 C355 132 406 136 437 164 C449 213 450 277 458 344 L428 420 L305 420Z" fill="url(#v2-cliff-mid)" />
          <path d="M675 350 C687 257 705 182 743 130 C777 99 830 120 844 155 L844 452 L707 452Z" fill="url(#v2-cliff-right)" />
        </g>
        <g className="v2-rift-land">
          <path d="M38 350 C83 331 211 329 267 350" /><path d="M274 344 C320 329 411 330 457 344" /><path d="M677 350 C728 329 805 331 844 350" />
        </g>
        <g className="v2-rift-icons" aria-hidden="true">
          <path d="M86 274 L86 216 L146 216 L146 274 M102 216 L102 184 L130 184 L130 216 M80 274 H153" />
          <circle cx="183" cy="225" r="35" /><path d="M160 225 H206 M183 202 V248 M166 207 C184 220 184 233 166 244 M200 207 C182 220 182 233 200 244" />
          <rect x="305" y="228" width="45" height="62" rx="4" /><rect x="361" y="214" width="45" height="76" rx="4" /><path d="M315 242 H340 M315 254 H340 M315 266 H340 M371 230 H396 M371 243 H396 M371 256 H396" />
          <path d="M326 196 C347 177 374 177 397 196" /><path d="M350 196 V168 M382 196 V168" />
          <path d="M737 267 V206 H799 V267 M725 267 H811 M746 206 V184 H790 V206 M751 227 H785 M751 242 H785" />
          <path d="M724 294 C744 274 769 274 789 294 C806 310 819 310 833 299" />
        </g>
        <g className="v2-rift-bridges">
          <path d="M455 248 C494 221 524 223 550 248 C574 270 598 273 624 252 C644 236 660 238 679 254" />
          {[496, 548, 601, 651].map((x, index) => <g key={x}><circle cx={x} cy={255 + index * 23} r="20" /><text x={x} y={262 + index * 23} textAnchor="middle">?</text></g>)}
        </g>
        <g className="v2-rift-fog" aria-hidden="true"><ellipse cx="558" cy="357" rx="126" ry="83" /><ellipse cx="614" cy="331" rx="92" ry="61" /><ellipse cx="513" cy="318" rx="73" ry="48" /></g>
        <g className="v2-rift-evidence">
          <text x="65" y="478">Upstream evidence: comparatively stronger</text>
          <line x1="329" y1="473" x2="425" y2="473" />
          <text x="461" y="478">Missing bridges</text>
          <line x1="571" y1="473" x2="653" y2="473" />
          <text x="684" y="478">Downstream evidence: weak and diffuse</text>
        </g>
      </svg>
      <figcaption>Capability is not deployment; delivery is not authentic exposure; exposure is not durable effect. The rift is a standard of proof, not a claim that nothing happens downstream.</figcaption>
    </figure>
  );
}

export function MechanismStrip() {
  const items = [
    ["Capability", "Models, tools, and techniques"],
    ["Controller", "Purpose, authority, and data"],
    ["Audience", "Discovery, targeting, and timing"],
    ["Vulnerability", "Trust, identity, fears, and dependencies"],
    ["Generation", "Messages, synthetic identity, and media"],
    ["Delivery", "Platforms, telecoms, groups, and assistants"],
    ["Feedback", "Observation, testing, and adaptation"],
    ["Objective", "Attention, belief, behaviour, or institutional response"],
  ];
  return (
    <figure className="v2-mechanism-strip">
      <div role="list" aria-label="Anatomy of an AI manipulation operation">
        {items.map(([title, detail], index) => (
          <article role="listitem" key={title}>
            <span className={`v2-mechanism-glyph v2-mechanism-glyph--${index}`} aria-hidden="true"><i /><b /><em /></span>
            <h3>{title}</h3><p>{detail}</p>
          </article>
        ))}
      </div>
      <figcaption>Editorialised from the supplied anatomy illustration. These are possible joins in an influence operation, not a finding that one real system completed the sequence.</figcaption>
    </figure>
  );
}

export function BenchmarkArchipelagoVisual({ compact = false }: { compact?: boolean }) {
  const islands = [
    { x: 88, y: 89, label: "Truthfulness", tone: "green" },
    { x: 223, y: 62, label: "Persuasion", tone: "gold" },
    { x: 358, y: 102, label: "Behaviour", tone: "gold" },
    { x: 491, y: 75, label: "Misinformation", tone: "red" },
    { x: 151, y: 220, label: "APE", tone: "green" },
    { x: 325, y: 224, label: "DisElect", tone: "green" },
    { x: 492, y: 237, label: "MASK", tone: "red" },
  ];
  return (
    <figure className={`v2-archipelago${compact ? " v2-archipelago--compact" : ""}`}>
      <svg viewBox="0 0 600 320" role="img" aria-labelledby="arch-title arch-desc">
        <title id="arch-title">The Benchmark Archipelago</title>
        <desc id="arch-desc">Evaluation instruments remain separate islands because constructs, model families, release continuity, and overlap are insufficient for one pooled manipulation index.</desc>
        <defs>
          <filter id="arch-shadow" x="-40%" y="-40%" width="180%" height="180%"><feDropShadow dx="0" dy="8" stdDeviation="8" floodOpacity=".13" /></filter>
        </defs>
        <rect width="600" height="320" rx="16" fill="#f8f5ed" />
        <path d="M102 112 C172 80 245 91 307 142 C361 187 422 158 507 112" fill="none" stroke="#b27a25" strokeWidth="2" strokeDasharray="7 8" opacity=".75" />
        <path d="M159 220 C207 180 267 188 322 224" fill="none" stroke="#16594f" strokeWidth="3" opacity=".75" />
        <path d="M342 226 C397 209 442 221 490 238" fill="none" stroke="#a12636" strokeWidth="2" strokeDasharray="7 8" opacity=".65" />
        {islands.map((island, index) => {
          const fill = island.tone === "green" ? "#dce8e3" : island.tone === "red" ? "#efe0e2" : "#f1e6d2";
          const stroke = island.tone === "green" ? "#16594f" : island.tone === "red" ? "#a12636" : "#b27a25";
          return (
            <g key={island.label} transform={`translate(${island.x} ${island.y})`} filter="url(#arch-shadow)">
              <path d="M-45 13 C-35-20 29-27 47 5 C55 21 37 37 3 41 C-30 43-52 32-45 13Z" fill={fill} stroke={stroke} strokeWidth="2" />
              <path d="M-29 10 L-7-7 L9 8 L27-14 L39 14" fill="none" stroke={stroke} strokeWidth="3" strokeLinecap="round" />
              <circle cx="0" cy="21" r="4" fill={stroke} />
              <text x="0" y="59" textAnchor="middle" className="v2-archipelago-label">{island.label}</text>
              {index < 4 ? <circle cx="50" cy="0" r="8" fill="#f8f5ed" stroke={stroke} strokeWidth="2" /> : null}
            </g>
          );
        })}
        <g transform="translate(300 151)">
          <rect x="-100" y="-28" width="200" height="56" rx="7" fill="#fbf9f4" stroke="#171716" />
          <text x="0" y="-3" textAnchor="middle" className="v2-archipelago-title">No pooled index</text>
          <text x="0" y="16" textAnchor="middle" className="v2-archipelago-note">without defensible bridges</text>
        </g>
      </svg>
      <figcaption>Different instruments observe different constructs under different protocols. Missing bridges remain visible rather than being averaged away.</figcaption>
    </figure>
  );
}
