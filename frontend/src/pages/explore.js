import { escapeHtml, itemCard } from "../components/item-card.js";

export function explorePage(data, categories, filters) {
  const categoryOptions = categories.map((category) => `
    <option value="${category.category_id}" ${String(filters.category_id) === String(category.category_id) ? "selected" : ""}>
      ${escapeHtml(category.name)}
    </option>
  `).join("");
  const cards = data.items.map((item) => itemCard(item)).join("");

  return `
    <section class="page-intro">
      <span class="eyebrow">A COLLECTION WITH CONNECTIONS</span>
      <h2>Find your next favorite.</h2>
      <p>Browse the collection. Every view, save, and rating helps your graph make more thoughtful suggestions.</p>
    </section>
    <section class="filter-panel" aria-label="Filter items">
      <label class="search-field">
        <span aria-hidden="true">⌕</span>
        <input id="catalog-search" type="search" value="${escapeHtml(filters.search)}" placeholder="Search books, gear, courses…" aria-label="Search items">
      </label>
      <label class="filter-select">
        <span class="sr-only">Category</span>
        <select id="category-filter"><option value="">All categories</option>${categoryOptions}</select>
      </label>
      <label class="filter-select">
        <span class="sr-only">Sort by</span>
        <select id="sort-filter">
          <option value="recommended" ${filters.sort === "recommended" ? "selected" : ""}>Recommended</option>
          <option value="popular" ${filters.sort === "popular" ? "selected" : ""}>Most popular</option>
          <option value="rating" ${filters.sort === "rating" ? "selected" : ""}>Top rated</option>
          <option value="newest" ${filters.sort === "newest" ? "selected" : ""}>Recently added</option>
        </select>
      </label>
      <span class="results-count">${data.count} ${data.count === 1 ? "item" : "items"}</span>
    </section>
    ${data.items.length
      ? `<div class="item-grid">${cards}</div>`
      : `<div class="empty-state"><span class="empty-icon">⌕</span><h3>No matches yet</h3><p>Try a different search or category.</p></div>`}
  `;
}
