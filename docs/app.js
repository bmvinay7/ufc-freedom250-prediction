/* Renders the UFC Freedom 250 dashboard from window.PREDICTIONS (data.js).
   Single model (XGBoost): probabilities come straight from predictions.json;
   the Monte Carlo (card-level) is recomputed in-browser with a seeded RNG. */
(function () {
  const D = window.PREDICTIONS;
  if (!D) { document.body.innerHTML = "<p style='padding:40px;font-family:sans-serif'>Missing data.js — run the pipeline.</p>"; return; }

  const pct = (x) => (x * 100).toFixed(1) + "%";
  const N = D.n_sims || 10000;
  const ev = D.event;

  // ---- hero ----
  const dt = new Date(ev.date + "T00:00:00");
  const dstr = dt.toLocaleDateString("en-US", { month: "long", day: "numeric", year: "numeric" }).toUpperCase();
  document.getElementById("hero-venue").textContent = `${ev.venue} · ${ev.city}`.toUpperCase();
  document.getElementById("hero-sub").textContent = `${ev.subtitle} · ${dstr}`.toUpperCase();
  document.getElementById("badge-acc").textContent = pct(D.model.test_accuracy);
  document.getElementById("badge-sims").textContent = (N / 1000) + "K";

  // ---- fights ----
  const wrap = document.getElementById("fights");
  D.fights.forEach((f, i) => {
    const redFav = f.p_red >= 0.5;
    const mp = f.method_probs;
    const methods = [
      ["KO/TKO", mp["KO/TKO"] || 0, "ko"],
      ["SUBMISSION", mp["Submission"] || 0, "sub"],
      ["DECISION", mp["Decision"] || 0, "dec"],
    ];
    const favLast = f.favorite.split(" ").slice(-1)[0];
    const el = document.createElement("article");
    el.className = "fight" + (f.title ? " title-fight" : "");
    el.style.animationDelay = (i * 90) + "ms";
    el.innerHTML = `
      <div class="fight-top">
        <span class="billing">${f.billing}</span>
        <span class="wc-tag">${f.weight_class} · ${f.scheduled_rounds}&nbsp;Rounds</span>
        <span class="belt">${f.title ? "★ " + f.title : ""}</span>
      </div>
      <div class="tape">
        <div class="corner red ${redFav ? "favored" : ""}">
          <span class="corner-tag">Red Corner</span>
          <span class="fighter-name">${f.red}</span>
          <span class="fighter-meta">Elo ${f.elo_red}</span>
          <span class="win-flag">Projected Winner</span>
        </div>
        <div class="vs">VS</div>
        <div class="corner blue ${redFav ? "" : "favored"}">
          <span class="corner-tag">Blue Corner</span>
          <span class="fighter-name">${f.blue}</span>
          <span class="fighter-meta">Elo ${f.elo_blue}</span>
          <span class="win-flag">Projected Winner</span>
        </div>
      </div>
      <div class="prob">
        <div class="prob-bar">
          <div class="prob-red" data-w="${f.p_red * 100}"><span>${pct(f.p_red)}</span></div>
          <div class="prob-mid"></div>
          <div class="prob-blue" data-w="${f.p_blue * 100}"><span>${pct(f.p_blue)}</span></div>
        </div>
      </div>
      <div class="detail">
        <div class="blk">
          <h4>Predicted Method</h4>
          ${methods.map(([lab, v, c]) => `
            <div class="method-row">
              <span class="ml">${lab}</span>
              <span class="method-track"><span class="method-fill ${c}" data-w="${v * 100}"></span></span>
              <span class="mv">${Math.round(v * 100)}%</span>
            </div>`).join("")}
        </div>
        <div class="blk center">
          <h4>Projected Outcome</h4>
          ${f.likely_method === "Decision"
            ? `<div class="round-big">DEC</div><div class="round-cap">Goes the distance · ${f.scheduled_rounds} rds</div>`
            : `<div class="round-big">R${f.likely_round}</div><div class="round-cap">${f.likely_method} finish</div>`}
        </div>
        <div class="blk center">
          <h4>Forecast Confidence</h4>
          <div class="conf-tier ${tierClass(f.fav_prob)}">${f.confidence}</div>
          <div class="round-cap">${favLast} · Elo edge +${f.elo_edge}</div>
        </div>
      </div>`;
    wrap.appendChild(el);
  });

  function tierClass(p) {
    return p >= 0.75 ? "t-heavy" : p >= 0.65 ? "t-clear" : p >= 0.55 ? "t-lean" : "t-toss";
  }

  // ---- Monte Carlo (card-level), seeded for stability ----
  function mulberry32(a) {
    return function () {
      a |= 0; a = (a + 0x6D2B79F5) | 0;
      let t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }
  const fights = D.fights;
  const k = fights.length;
  const favProbs = fights.map((f) => f.fav_prob);
  const favIsRed = fights.map((f) => f.p_red >= 0.5);
  const rng = mulberry32(42);
  const dist = new Array(k + 1).fill(0);
  const combo = {};
  let sumFav = 0;
  for (let s = 0; s < N; s++) {
    let nf = 0, mask = 0;
    for (let i = 0; i < k; i++) { if (rng() < favProbs[i]) { nf++; mask |= (1 << i); } }
    dist[nf]++; sumFav += nf; combo[mask] = (combo[mask] || 0) + 1;
  }
  const pctile = (p) => { let c = 0; for (let i = 0; i <= k; i++) { c += dist[i]; if (c / N >= p) return i; } return k; };
  const parlay = 1 / favProbs.reduce((a, b) => a * b, 1);
  const expFav = sumFav / N;

  // ---- outlook stats ----
  const stats = [
    [expFav.toFixed(2) + " / " + k, "Expected Favorites Correct"],
    [pct(dist[k] / N), "Card Goes Full Chalk"],
    [(k - expFav).toFixed(2), "Expected Upsets"],
    [parlay.toFixed(1) + "×", "7-Leg Parlay Payout"],
  ];
  document.getElementById("outlook-stats").innerHTML = stats
    .map(([v, l]) => `<div class="stat"><div class="v">${v}</div><div class="l">${l}</div></div>`).join("");

  // ---- histogram ----
  const probDist = dist.map((c) => c / N);
  const maxv = Math.max(...probDist);
  const peak = probDist.indexOf(maxv);
  document.getElementById("histo").innerHTML = probDist.map((v, j) => `
    <div class="hbar ${j === peak ? "peak" : ""}">
      <span class="hk">${j}/${k}</span>
      <span class="htrack"><span class="hfill" data-w="${(v / maxv) * 100}"></span></span>
      <span class="hv">${pct(v)}</span>
    </div>`).join("");
  document.getElementById("histo-note").textContent =
    `Most likely: ${peak} of ${k} favorites win (${pct(probDist[peak])}). 95% interval ${pctile(0.025)}–${pctile(0.975)}.`;

  // ---- most likely combos ----
  const topMasks = Object.keys(combo).map(Number).sort((a, b) => combo[b] - combo[a]).slice(0, 4);
  document.getElementById("combos").innerHTML = topMasks.map((mask) => {
    let upsets = 0;
    const chips = fights.map((f, i) => {
      const favWon = (mask >> i) & 1;
      if (!favWon) upsets++;
      const fav = favIsRed[i] ? f.red : f.blue;
      const dog = favIsRed[i] ? f.blue : f.red;
      const w = (favWon ? fav : dog).split(" ").slice(-1)[0];
      return `<span class="chip ${favWon ? "" : "upset"}">${w}</span>`;
    }).join("");
    return `
      <div class="combo">
        <div class="combo-top">
          <span>${upsets === 0 ? "Full Chalk" : upsets + " Upset" + (upsets > 1 ? "s" : "")}</span>
          <span class="combo-prob">${pct(combo[mask] / N)}</span>
        </div>
        <div class="combo-win">${chips}</div>
      </div>`;
  }).join("");

  // ---- animate bars ----
  requestAnimationFrame(() => setTimeout(() => {
    document.querySelectorAll(".prob-red,.prob-blue,.method-fill,.hfill").forEach((b) => {
      b.style.width = b.dataset.w + "%";
    });
  }, 200));
})();
