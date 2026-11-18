import { itemCard, escapeHtml } from "../components/item-card.js";

function statCard(label, value, note, symbol, color) {
  return `
    <article class="stat-card">
      <span class="stat-symbol ${color}">${symbol}</span>
      <span class="stat-label">${label}</span>
      <strong>${value}</strong>
      <span class="stat-note">${note}</span>
    </article>
  `;
}

export function dashboardPage(data) {
  const firstName = escapeHtml(data.user.display_name.split(" ")[0]);
  const stats = data.stats;
  const recommendations = data.recommendations || [];

  return `
    <section class="welcome-banner">
      <div class="welcome-copy">
        <span class="eyebrow eyebrow-light">YOUR PERSONAL DISCOVERY GRAPH</span>
        <h2>Good to see you, ${firstName}.</h2>
        <p>Your interests connect to people, topics, and things worth discovering. Here’s what your graph found today.</p>
        <button class="button button-light" type="button" data-view="explore">Explore the collection <span aria-hidden="true">↗</span></button>
      </div>
      <div class="graph-illustration" aria-hidden="true">
        <svg viewBox="0 0 260 210" fill="none">
          <path class="graph-line" d="m49 111 51-60 61 19 45 63-66 37-69-27-22-32Zm51-60 28 92m61-73-61 73m61-73 45 63m-45-63-111 34m111 29-88-10" />
          <circle class="graph-node node-main" cx="130" cy="143" r="20" />
          <circle class="graph-node node-accent" cx="49" cy="111" r="12" />
          <circle class="graph-node node-soft" cx="100" cy="51" r="13" />
          <circle class="graph-node node-soft" cx="161" cy="70" r="16" />
          <circle class="graph-node node-accent" cx="206" cy="133" r="13" />
          <circle class="graph-node node-soft" cx="140" cy="180" r="10" />
          <circle class="graph-node node-soft" cx="71" cy="153" r="9" />
          <circle class="graph-halo" cx="130" cy="143" r="33" />
        </svg>
        <span class="graph-caption">your graph, growing</span>
      </div>
    </section>

    <section class="stats-grid" aria-label="Your activity">
      ${statCard("Graph signals", stats.interaction_count, "Meaningful interactions", "↗", "stat-violet")}
      ${statCard("Saved for later", stats.saved_count, "Items in your collection", "♡", "stat-coral")}
      ${statCard("Your ratings", stats.rating_count, "Helping your graph learn", "★", "stat-amber")}
      ${statCard("Interest paths", stats.interest_count, "Topics shaping discovery", "⌘", "stat-mint")}
    </section>

    <section class="section-block">
      <div class="section-heading">
        <div>
          <span class="eyebrow">MAPPED TO YOUR GRAPH</span>
          <h2>Picked for you</h2>
          <p>Recommendations blend similar-user paths, your interests, and community ratings.</p>
        </div>
        <span class="algorithm-badge"><span></span> ${escapeHtml(data.algorithm.replaceAll("_", " "))}</span>
      </div>
      ${recommendations.length
        ? `<div class="item-grid">${recommendations.map((item) => itemCard(item, { showReason: true })).join("")}</div>`
        : `<div class="empty-state"><span class="empty-icon">✳</span><h3>Your graph is ready to grow</h3><p>Explore a few items, save favorites, or choose interests to get your first personalized recommendations.</p><button class="button button-primary" type="button" data-view="preferences">Set your interests</button></div>`}
    </section>
  `;
}
