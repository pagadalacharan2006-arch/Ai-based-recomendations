import { escapeHtml } from "../components/item-card.js";

export function preferencesPage(categories, interests) {
  const selected = new Map(interests.map((interest) => [
    Number(interest.category_id),
    Number(interest.interest_weight),
  ]));
  const cards = categories.map((category) => {
    const weight = selected.get(Number(category.category_id));
    const checked = weight !== undefined;
    return `
      <label class="interest-card ${checked ? "is-selected" : ""}">
        <input type="checkbox" name="category_id" value="${category.category_id}" ${checked ? "checked" : ""}>
        <span class="interest-check" aria-hidden="true">✓</span>
        <span class="interest-name">${escapeHtml(category.name)}</span>
        <span class="interest-description">${escapeHtml(category.description || "Discover more in this topic.")}</span>
        <span class="weight-control">
          <span>How much?</span>
          <input type="range" min="0.1" max="1" step="0.05" value="${checked ? weight : "0.5"}"
            name="weight_${category.category_id}" aria-label="Interest strength for ${escapeHtml(category.name)}"
            ${checked ? "" : "disabled"}>
          <output>${checked ? `${Math.round(weight * 100)}%` : "Off"}</output>
        </span>
      </label>
    `;
  }).join("");

  return `
    <section class="page-intro">
      <span class="eyebrow">TUNE YOUR GRAPH</span>
      <h2>Tell us what draws you in.</h2>
      <p>Choose categories and set their strength. The graph follows these paths when it looks for your next great find.</p>
    </section>
    <form class="interests-form" id="interests-form">
      <div class="interest-grid">${cards}</div>
      <div class="form-actions">
        <span>Selected interests become weighted links in your graph.</span>
        <button class="button button-primary" type="submit">Save interests <span aria-hidden="true">↗</span></button>
      </div>
    </form>
  `;
}
