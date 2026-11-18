export function escapeHtml(value = "") {
  return String(value).replace(/[&<>"']/g, (character) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  })[character]);
}

function shortType(value = "item") {
  return escapeHtml(value.replaceAll("_", " "));
}

export function itemCard(item, { showReason = false } = {}) {
  const description = item.description || "A new discovery from your graph.";
  const reason = showReason && item.reason
    ? `<div class="recommendation-reason"><span class="reason-spark">✳</span>${escapeHtml(item.reason)}</div>`
    : "";
  const ratingText = item.rating_count
    ? `${Number(item.average_rating).toFixed(1)} <span>(${item.rating_count})</span>`
    : "New";

  return `
    <article class="item-card" data-card-id="${item.item_id}">
      <div class="item-visual visual-${item.category_id % 6}">
        <span class="item-type">${shortType(item.item_type)}</span>
        <span class="item-category">${escapeHtml(item.category_name)}</span>
        <button class="save-button ${item.is_saved ? "is-saved" : ""}" type="button"
          data-action="save" data-item-id="${item.item_id}"
          aria-label="${item.is_saved ? "Remove saved item" : "Save item"}"
          title="${item.is_saved ? "Remove from saved items" : "Save item"}">
          ${item.is_saved ? "♥" : "♡"}
        </button>
        <span class="visual-glyph" aria-hidden="true">${escapeHtml(item.title.slice(0, 1).toUpperCase())}</span>
      </div>
      <div class="item-card-body">
        ${reason}
        <h3>${escapeHtml(item.title)}</h3>
        <p class="item-description">${escapeHtml(description)}</p>
        <div class="item-card-meta">
          <span class="rating-meta"><span class="star">★</span> ${ratingText}</span>
          <span class="item-category-label">${escapeHtml(item.category_name)}</span>
        </div>
        <div class="item-card-actions">
          <button class="button button-outline button-small" type="button"
            data-action="details" data-item-id="${item.item_id}">View details</button>
          ${item.user_rating
            ? `<span class="your-rating">You rated ${item.user_rating} ★</span>`
            : `<button class="text-button" type="button" data-action="rate" data-item-id="${item.item_id}">Rate it</button>`}
        </div>
      </div>
    </article>
  `;
}
