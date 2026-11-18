import { escapeHtml } from "../components/item-card.js";

export function authPage(mode = "login", message = "") {
  const registering = mode === "register";
  const fields = registering
    ? `
      <label class="auth-field">Display name
        <input name="display_name" type="text" maxlength="120" autocomplete="name" required>
      </label>
      <label class="auth-field">Username
        <input name="username" type="text" minlength="3" maxlength="50" pattern="[A-Za-z0-9._\\-]+"
          autocomplete="username" required>
        <small>3–50 characters: letters, numbers, dot, underscore, or hyphen.</small>
      </label>
      <label class="auth-field">Email
        <input name="email" type="email" maxlength="254" autocomplete="email" required>
      </label>
    `
    : `
      <label class="auth-field">Username or email
        <input name="identifier" type="text" autocomplete="username" required>
      </label>
    `;

  return `
    <section class="auth-layout">
      <div class="auth-story">
        <span class="eyebrow eyebrow-light">DISCOVERY, CONNECTED</span>
        <h2>Find the thread that leads to something good.</h2>
        <p>Weave connects your interests, the things you explore, and patterns across the community to surface your next discovery.</p>
        <div class="auth-graph" aria-hidden="true">
          <svg viewBox="0 0 360 245" fill="none">
            <path d="m75 120 68-76 80 38 72 69-94 57-84-30-42-58Zm68-76 58 164m22-126-22 126m22-126 72 69m-72-69L75 120m220 31-178 27" />
            <circle cx="75" cy="120" r="13" /><circle cx="143" cy="44" r="15" />
            <circle cx="223" cy="82" r="20" /><circle cx="295" cy="151" r="14" />
            <circle cx="201" cy="208" r="23" /><circle cx="117" cy="178" r="11" />
            <circle class="auth-center" cx="201" cy="208" r="34" />
          </svg>
          <span>people <i></i> interests <i></i> discoveries</span>
        </div>
      </div>
      <div class="auth-card">
        <span class="auth-card-mark">w</span>
        <span class="eyebrow">${registering ? "START YOUR GRAPH" : "WELCOME BACK"}</span>
        <h2>${registering ? "Create your account" : "Sign in to Weave"}</h2>
        <p>${registering ? "Your recommendations get better as your graph grows." : "Your personal graph is ready when you are."}</p>
        ${message ? `<div class="auth-error" role="alert">${escapeHtml(message)}</div>` : ""}
        <form id="auth-form" data-mode="${registering ? "register" : "login"}">
          ${fields}
          <label class="auth-field">Password
            <input name="password" type="password" minlength="12" maxlength="128"
              autocomplete="${registering ? "new-password" : "current-password"}" required>
            ${registering ? "<small>Use at least 12 characters.</small>" : ""}
          </label>
          <button class="button button-primary auth-submit" type="submit">${registering ? "Create account" : "Sign in"} <span aria-hidden="true">↗</span></button>
        </form>
        <div class="auth-switch">
          <span>${registering ? "Already have an account?" : "New to Weave?"}</span>
          <button type="button" data-action="auth-mode" data-mode="${registering ? "login" : "register"}">
            ${registering ? "Sign in" : "Create an account"}
          </button>
        </div>
        ${registering ? "" : `
          <div class="demo-credentials">
            <strong>Local demo account</strong>
            <span>maya_chen</span>
            <span>WeaveDemo!2026</span>
          </div>
        `}
      </div>
    </section>
  `;
}
