import { escapeHtml } from "../components/item-card.js";

export function historyPage(data) {
  const history = data.history || [];
  const rows = history.map((entry) => `
    <article class="history-row">
      <span class="history-rank">#${entry.rank_position}</span>
      <div class="history-item">
        <strong>${escapeHtml(entry.title)}</strong>
        <span>${escapeHtml(entry.category_name)} · ${escapeHtml(entry.item_type)}</span>
      </div>
      <span class="history-score">${Number(entry.score).toFixed(3)}<small>GRAPH SCORE</small></span>
      <span class="history-algorithm">${escapeHtml(entry.algorithm_name.replaceAll("_", " "))}</span>
      <time>${new Date(entry.generated_at).toLocaleString()}</time>
    </article>
  `).join("");

  return `
    <section class="page-intro">
      <span class="eyebrow">YOUR DISCOVERY TRAIL</span>
      <h2>Recommendations, remembered.</h2>
      <p>Each time your graph generates a list, its ranked suggestions are recorded here.</p>
    </section>
    ${history.length
      ? `<section class="history-list" aria-label="Recommendation history">${rows}</section>`
      : `<div class="empty-state"><span class="empty-icon">◷</span><h3>No recommendations recorded yet</h3><p>Visit your overview to generate the first list from your graph.</p><button class="button button-primary" type="button" data-view="dashboard">Go to overview</button></div>`}
  `;
}
