import { api } from "./services/api.js";
import { escapeHtml } from "./components/item-card.js";
import { authPage } from "./pages/auth.js";
import { dashboardPage } from "./pages/dashboard.js";
import { explorePage } from "./pages/explore.js";
import { historyPage } from "./pages/history.js";
import { preferencesPage } from "./pages/preferences.js";
import { savedPage } from "./pages/saved.js";

const pageContent = document.querySelector("#page-content");
const dialog = document.querySelector("#item-dialog");
const dialogContent = document.querySelector("#dialog-content");
const toastRegion = document.querySelector("#toast-region");

const pageNames = {
  dashboard: ["YOUR SPACE", "Overview"],
  explore: ["DISCOVER", "Explore"],
  saved: ["YOUR COLLECTION", "Saved items"],
  history: ["YOUR GRAPH", "Recommendation history"],
  preferences: ["PERSONALIZE", "Your interests"],
};

const state = {
  categories: [],
  user: null,
  userId: null,
  authMode: "login",
  view: "dashboard",
  pageData: null,
  activeItem: null,
  draftRating: 0,
  filters: { search: "", category_id: "", sort: "recommended" },
  searchTimer: null,
};

function currentUser() {
  return state.user;
}

function setConnectionStatus(online, label) {
  const status = document.querySelector("#connection-status");
  status.classList.toggle("is-offline", !online);
  status.innerHTML = `<span class="status-dot"></span><span>${escapeHtml(label)}</span>`;
}

async function handleAuthSubmit(event) {
  if (event.target.id !== "auth-form") return;
  event.preventDefault();
  const form = event.target;
  const formData = new FormData(form);
  const submitButton = form.querySelector('button[type="submit"]');
  submitButton.disabled = true;
  submitButton.textContent = form.dataset.mode === "register" ? "Creating account…" : "Signing in…";

  try {
    const result = form.dataset.mode === "register"
      ? await api.register({
        username: formData.get("username"),
        email: formData.get("email"),
        display_name: formData.get("display_name"),
        password: formData.get("password"),
      })
      : await api.login(formData.get("identifier"), formData.get("password"));
    state.user = result.user;
    state.userId = Number(result.user.user_id);
    updateAccount();
    showToast(form.dataset.mode === "register" ? "Your account is ready." : "Welcome back.");
    await loadView("dashboard");
  } catch (error) {
    showAuthPage(form.dataset.mode, error.message);
  }
}

function showToast(message, isError = false) {
  const toast = document.createElement("div");
  toast.className = `toast${isError ? " is-error" : ""}`;
  toast.textContent = message;
  toastRegion.append(toast);
  window.setTimeout(() => toast.remove(), 3600);
}

function showLoadError(message, title = "We couldn’t load this view") {
  pageContent.innerHTML = `
    <section class="error-panel" role="alert">
      <span class="eyebrow">CONNECTION ISSUE</span>
      <h2>${escapeHtml(title)}</h2>
      <p>${escapeHtml(message)}</p>
      <p>Check that MySQL is running and that <code>DB_HOST</code>, <code>DB_USER</code>, <code>DB_PASSWORD</code>, and <code>DB_NAME</code> in your root <code>.env</code> match your local setup. See <code>README.md</code> for setup instructions.</p>
      <button class="button button-retry" type="button" data-action="refresh">Try again</button>
    </section>
  `;
}

function updateAccount() {
  const user = currentUser();
  const shell = document.querySelector(".app-shell");
  shell.classList.toggle("is-logged-out", !user);
  document.querySelector("#account-name").textContent = user ? user.display_name : "Signed out";
  document.querySelector("#account-email").textContent = user
    ? user.email
    : "Sign in to keep your graph private.";
  document.querySelector("#logout-button").hidden = !user;
  document.querySelector("#user-avatar").textContent = user
    ? user.display_name.split(/\s+/).slice(0, 2).map((part) => part[0]).join("").toUpperCase()
    : "W";
}

function showAuthPage(mode = state.authMode, message = "") {
  state.authMode = mode;
  state.user = null;
  state.userId = null;
  state.pageData = null;
  updateAccount();
  document.querySelector("#page-kicker").textContent = "GRAPH DISCOVERY";
  document.querySelector("#page-title").textContent = "Welcome";
  pageContent.innerHTML = authPage(mode, message);
}

function setPageHeading(view) {
  const [kicker, title] = pageNames[view] || pageNames.dashboard;
  document.querySelector("#page-kicker").textContent = kicker;
  document.querySelector("#page-title").textContent = title;
  document.querySelectorAll("[data-view].nav-link").forEach((link) => {
    link.classList.toggle("active", link.dataset.view === view);
  });
  document.querySelector(".app-shell").classList.remove("is-logged-out");
  document.querySelector("#sidebar").classList.remove("is-open");
}

function renderPage() {
  if (!state.pageData) return;
  if (state.view === "dashboard") {
    pageContent.innerHTML = dashboardPage(state.pageData);
  } else if (state.view === "explore") {
    pageContent.innerHTML = explorePage(state.pageData, state.categories, state.filters);
  } else if (state.view === "saved") {
    pageContent.innerHTML = savedPage(state.pageData);
  } else if (state.view === "history") {
    pageContent.innerHTML = historyPage(state.pageData);
  } else if (state.view === "preferences") {
    pageContent.innerHTML = preferencesPage(state.categories, state.pageData.interests);
  }
}

async function loadView(view = state.view) {
  state.view = view;
  setPageHeading(view);
  if (!state.userId) {
    showAuthPage();
    return;
  }
  pageContent.innerHTML = '<div class="loading-state"><span class="spinner"></span><span>Following your graph…</span></div>';

  try {
    if (view === "dashboard") {
      state.pageData = await api.dashboard(state.userId);
    } else if (view === "explore") {
      state.pageData = await api.catalog(state.userId, {
        search: state.filters.search,
        category_id: state.filters.category_id,
        sort: state.filters.sort,
      });
    } else if (view === "saved") {
      state.pageData = await api.savedItems(state.userId);
    } else if (view === "history") {
      state.pageData = await api.history(state.userId);
    } else if (view === "preferences") {
      state.pageData = await api.interests(state.userId);
    }
    renderPage();
  } catch (error) {
    if (error.status >= 500) setConnectionStatus(false, "Database unavailable");
    showLoadError(error.message);
  }
}

function refreshItemInPage(updatedItem) {
  const data = state.pageData;
  if (!data) return;
  for (const key of ["items", "recommendations"]) {
    if (Array.isArray(data[key])) {
      const index = data[key].findIndex((item) => Number(item.item_id) === Number(updatedItem.item_id));
      if (index >= 0) data[key][index] = { ...data[key][index], ...updatedItem };
    }
  }
}

function findCurrentItem(itemId) {
  const data = state.pageData;
  if (!data) return null;
  for (const key of ["items", "recommendations"]) {
    const item = data[key]?.find((entry) => Number(entry.item_id) === Number(itemId));
    if (item) return item;
  }
  return null;
}

function dialogMarkup(item) {
  const rating = Number(item.user_rating || 0);
  return `
    <div class="dialog-visual visual-${item.category_id % 6}">
      <span class="visual-glyph" aria-hidden="true">${escapeHtml(item.title.slice(0, 1).toUpperCase())}</span>
      <span class="item-type">${escapeHtml(item.item_type)}</span>
      <span class="item-category">${escapeHtml(item.category_name)}</span>
      <button class="dialog-close" type="button" data-action="close-dialog" aria-label="Close">×</button>
    </div>
    <div class="dialog-body">
      <span class="eyebrow">${escapeHtml(item.category_name)}</span>
      <h2 id="dialog-title">${escapeHtml(item.title)}</h2>
      <p>${escapeHtml(item.description || "A new discovery from your graph.")}</p>
      <div class="dialog-meta">
        <span><span class="star">★</span> ${Number(item.average_rating || 0).toFixed(1)} (${item.rating_count || 0} ratings)</span>
        <span>${Number(item.interaction_count || 0)} graph signals</span>
      </div>
      <div class="dialog-actions">
        <button class="button button-outline" type="button" data-action="save" data-item-id="${item.item_id}">
          ${item.is_saved ? "♥ Saved" : "♡ Save item"}
        </button>
        <div class="rating-control" role="group" aria-label="Rate this item">
          <span>${rating ? `Your rating: ${rating}` : "Your rating"}</span>
          ${[1, 2, 3, 4, 5].map((value) => `
            <button class="rating-star ${value <= (state.draftRating || rating) ? "is-active" : ""}"
              type="button" data-action="select-rating" data-rating="${value}"
              aria-label="Rate ${value} out of 5 stars">★</button>
          `).join("")}
        </div>
      </div>
      <div class="dialog-submit-row">
        <button class="button button-primary" type="button" data-action="submit-rating">Save rating</button>
      </div>
    </div>
  `;
}

function openItem(item) {
  state.activeItem = item;
  state.draftRating = Number(item.user_rating || 0);
  dialogContent.innerHTML = dialogMarkup(item);
  dialog.showModal();
  api.recordInteraction(state.userId, item.item_id, "click")
    .catch((error) => showToast(error.message, true));
}

async function toggleSaved(itemId) {
  const item = findCurrentItem(itemId);
  if (!item) return;
  const saved = !item.is_saved;
  try {
    if (saved) {
      await api.saveItem(state.userId, itemId);
    } else {
      await api.unsaveItem(state.userId, itemId);
    }
    const updated = { ...item, is_saved: saved };
    refreshItemInPage(updated);
    if (state.view === "saved" && !saved) {
      state.pageData.items = state.pageData.items.filter((entry) => Number(entry.item_id) !== Number(itemId));
    }
    if (state.pageData.stats) {
      state.pageData.stats.saved_count = Math.max(
        0,
        state.pageData.stats.saved_count + (saved ? 1 : -1),
      );
    }
    renderPage();
    if (state.activeItem && Number(state.activeItem.item_id) === Number(itemId) && dialog.open) {
      state.activeItem = updated;
      dialogContent.innerHTML = dialogMarkup(updated);
    }
    showToast(saved ? "Added to your saved collection." : "Removed from your saved collection.");
  } catch (error) {
    showToast(error.message, true);
  }
}

async function submitRating() {
  if (!state.activeItem || !state.draftRating) {
    showToast("Choose a star rating first.", true);
    return;
  }
  try {
    await api.rateItem(state.userId, state.activeItem.item_id, state.draftRating);
    const updated = { ...state.activeItem, user_rating: state.draftRating };
    refreshItemInPage(updated);
    state.activeItem = updated;
    renderPage();
    dialog.close();
    showToast("Your rating has been added to the graph.");
  } catch (error) {
    showToast(error.message, true);
  }
}

async function handlePageClick(event) {
  const viewButton = event.target.closest("[data-view]");
  if (viewButton) {
    event.preventDefault();
    await loadView(viewButton.dataset.view);
    return;
  }

  const actionButton = event.target.closest("[data-action]");
  if (!actionButton) return;
  if (actionButton.dataset.action === "auth-mode") {
    showAuthPage(actionButton.dataset.mode);
    return;
  }
  const itemId = Number(actionButton.dataset.itemId);
  switch (actionButton.dataset.action) {
    case "save":
      await toggleSaved(itemId);
      break;
    case "details": {
      const item = findCurrentItem(itemId);
      if (item) openItem(item);
      break;
    }
    case "rate": {
      const item = findCurrentItem(itemId);
      if (item) openItem(item);
      break;
    }
    case "refresh":
      await loadView();
      break;
  }
}

async function handleDialogClick(event) {
  const actionButton = event.target.closest("[data-action]");
  if (!actionButton) return;
  if (actionButton.dataset.action === "close-dialog") {
    dialog.close();
  } else if (actionButton.dataset.action === "save") {
    await toggleSaved(Number(actionButton.dataset.itemId));
  } else if (actionButton.dataset.action === "select-rating") {
    state.draftRating = Number(actionButton.dataset.rating);
    if (state.activeItem) dialogContent.innerHTML = dialogMarkup(state.activeItem);
  } else if (actionButton.dataset.action === "submit-rating") {
    await submitRating();
  }
}

async function handleInterestSubmit(event) {
  if (event.target.id !== "interests-form") return;
  event.preventDefault();
  const selections = [...event.target.querySelectorAll('input[name="category_id"]:checked')];
  const interests = selections.map((checkbox) => ({
    category_id: Number(checkbox.value),
    weight: Number(event.target.querySelector(`[name="weight_${checkbox.value}"]`).value),
  }));
  const submitButton = event.target.querySelector('button[type="submit"]');
  submitButton.disabled = true;
  submitButton.textContent = "Saving…";
  try {
    state.pageData = await api.updateInterests(state.userId, interests);
    renderPage();
    showToast("Your interest paths have been updated.");
  } catch (error) {
    showToast(error.message, true);
    submitButton.disabled = false;
    submitButton.textContent = "Save interests";
  }
}

function handleInterestInput(event) {
  const card = event.target.closest(".interest-card");
  if (!card) return;
  if (event.target.matches('input[type="checkbox"]')) {
    card.classList.toggle("is-selected", event.target.checked);
    const slider = card.querySelector('input[type="range"]');
    slider.disabled = !event.target.checked;
    const output = card.querySelector("output");
    output.textContent = event.target.checked ? `${Math.round(Number(slider.value) * 100)}%` : "Off";
  } else if (event.target.matches('input[type="range"]')) {
    card.querySelector("output").textContent = `${Math.round(Number(event.target.value) * 100)}%`;
  }
}

async function loadCatalogFromFilters() {
  if (state.view === "explore") await loadView("explore");
}

function handlePageInput(event) {
  if (event.target.id === "catalog-search") {
    state.filters.search = event.target.value;
    window.clearTimeout(state.searchTimer);
    state.searchTimer = window.setTimeout(loadCatalogFromFilters, 250);
  } else {
    handleInterestInput(event);
  }
}

async function handlePageChange(event) {
  if (event.target.id === "category-filter") {
    state.filters.category_id = event.target.value;
    await loadCatalogFromFilters();
  } else if (event.target.id === "sort-filter") {
    state.filters.sort = event.target.value;
    await loadCatalogFromFilters();
  } else {
    handleInterestInput(event);
  }
}

async function initialize() {
  pageContent.innerHTML = '<div class="loading-state"><span class="spinner"></span><span>Connecting your graph…</span></div>';
  try {
    const health = await api.health();
    setConnectionStatus(true, `MySQL ${health.mysql_version}`);
    await api.csrf();
    const [authData, categoriesData] = await Promise.all([api.me(), api.categories()]);
    state.categories = categoriesData.categories;
    if (!authData.authenticated) {
      showAuthPage("login");
      return;
    }
    state.user = authData.user;
    state.userId = Number(authData.user.user_id);
    updateAccount();
    await loadView("dashboard");
  } catch (error) {
    setConnectionStatus(false, "Database unavailable");
    showLoadError(error.message, "We couldn’t connect to MySQL");
  }
}

pageContent.addEventListener("click", handlePageClick);
pageContent.addEventListener("input", handlePageInput);
pageContent.addEventListener("change", handlePageChange);
pageContent.addEventListener("submit", (event) => {
  if (event.target.id === "auth-form") {
    handleAuthSubmit(event);
  } else {
    handleInterestSubmit(event);
  }
});
dialog.addEventListener("click", handleDialogClick);
dialog.addEventListener("click", (event) => {
  if (event.target === dialog) dialog.close();
});
document.querySelector("#refresh-button").addEventListener("click", () => loadView());
document.querySelector("#mobile-menu").addEventListener("click", () => {
  document.querySelector("#sidebar").classList.toggle("is-open");
});
document.querySelector("#logout-button").addEventListener("click", async () => {
  try {
    await api.logout();
    await api.csrf();
    state.user = null;
    state.userId = null;
    showAuthPage("login", "You’ve signed out safely.");
  } catch (error) {
    showToast(error.message, true);
  }
});
document.querySelector("#sidebar").addEventListener("click", async (event) => {
  const viewButton = event.target.closest("[data-view]");
  if (!viewButton) return;
  await loadView(viewButton.dataset.view);
});
document.addEventListener("click", (event) => {
  const sidebar = document.querySelector("#sidebar");
  if (
    sidebar.classList.contains("is-open")
    && !sidebar.contains(event.target)
    && !event.target.closest("#mobile-menu")
  ) {
    sidebar.classList.remove("is-open");
  }
});

updateAccount();
initialize();
