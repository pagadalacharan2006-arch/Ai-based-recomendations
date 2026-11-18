import { itemCard } from "../components/item-card.js";

export function savedPage(data) {
  return `
    <section class="page-intro">
      <span class="eyebrow">YOUR PERSONAL COLLECTION</span>
      <h2>Worth coming back to.</h2>
      <p>Everything you’ve saved in one place. Your saved items also become useful paths in your recommendation graph.</p>
    </section>
    ${data.items.length
      ? `<div class="item-grid">${data.items.map((item) => itemCard(item)).join("")}</div>`
      : `<div class="empty-state"><span class="empty-icon">♡</span><h3>Your saved collection is empty</h3><p>Save something from Explore and it will be waiting here.</p><button class="button button-primary" type="button" data-view="explore">Explore items</button></div>`}
  `;
}
