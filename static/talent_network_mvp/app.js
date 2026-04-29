const STORAGE_KEY = "dragonne_talent_network_mvp_submissions_v2";
const ACCOUNT_KEY = "dragonne_talent_network_mvp_accounts_v1";
const SESSION_KEY = "dragonne_talent_network_mvp_session_v1";
const SETTINGS_KEY = "dragonne_talent_network_mvp_settings_v1";

// Opcional: setea un webhook para notificar "cuenta creada".
// Se puede configurar guardando en localStorage[SETTINGS_KEY] = {"notifyWebhookUrl":"https://..."}
function getSettings() {
  try {
    const raw = localStorage.getItem(SETTINGS_KEY);
    if (!raw) return { notifyWebhookUrl: "" };
    const parsed = JSON.parse(raw);
    return { notifyWebhookUrl: String(parsed?.notifyWebhookUrl || "") };
  } catch {
    return { notifyWebhookUrl: "" };
  }
}

function $(sel, root = document) {
  return root.querySelector(sel);
}
function $all(sel, root = document) {
  return Array.from(root.querySelectorAll(sel));
}

function readAccounts() {
  try {
    const raw = localStorage.getItem(ACCOUNT_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function writeAccounts(items) {
  localStorage.setItem(ACCOUNT_KEY, JSON.stringify(items, null, 2));
}

function getSession() {
  try {
    const raw = localStorage.getItem(SESSION_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    if (!parsed?.email) return null;
    return { email: String(parsed.email) };
  } catch {
    return null;
  }
}

function setSession(email) {
  localStorage.setItem(SESSION_KEY, JSON.stringify({ email }, null, 2));
}

function readStore() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function writeStore(items) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(items, null, 2));
}

function formToObject(form) {
  const fd = new FormData(form);
  const out = {};

  // Simple fields
  for (const [k, v] of fd.entries()) {
    if (k === "stack" || k === "segments" || k === "languages" || k === "skills") continue;
    out[k] = typeof v === "string" ? v.trim() : v;
  }

  // Multi-selects (checkbox groups)
  out.stack = fd.getAll("stack").map(String);
  out.segments = fd.getAll("segments").map(String);
  out.languages = fd.getAll("languages").map(String);
  out.skills = fd.getAll("skills").map(String);

  return out;
}

function openModal(title, bodyHtml) {
  const modal = $("#modal");
  $("#modalTitle").textContent = title;
  $("#modalBody").innerHTML = bodyHtml;

  if (typeof modal.showModal === "function") modal.showModal();
  else modal.setAttribute("open", "true");
}

function closeModal() {
  const modal = $("#modal");
  if (typeof modal.close === "function") modal.close();
  else modal.removeAttribute("open");
}

function openRegisterModal() {
  const modal = $("#registerModal");
  if (!modal) return;
  if (typeof modal.showModal === "function") modal.showModal();
  else modal.setAttribute("open", "true");
}

function closeRegisterModal() {
  const modal = $("#registerModal");
  if (!modal) return;
  if (typeof modal.close === "function") modal.close();
  else modal.removeAttribute("open");
}

function openHotelModal() {
  const modal = $("#hotelModal");
  if (!modal) return;
  if (typeof modal.showModal === "function") modal.showModal();
  else modal.setAttribute("open", "true");
}

function closeHotelModal() {
  const modal = $("#hotelModal");
  if (!modal) return;
  if (typeof modal.close === "function") modal.close();
  else modal.removeAttribute("open");
}

function esc(s) {
  return String(s ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function humanList(arr) {
  const a = (arr || []).filter(Boolean);
  if (!a.length) return "—";
  return a.map(esc).join(", ");
}

function wireTabs() {
  const tabs = $all(".tab");
  const panels = $all(".panel");

  function activate(key) {
    tabs.forEach((t) => {
      const on = t.dataset.tab === key;
      t.classList.toggle("is-active", on);
      t.setAttribute("aria-selected", on ? "true" : "false");
    });
    panels.forEach((p) => p.classList.toggle("is-active", p.dataset.panel === key));
  }

  tabs.forEach((t) => t.addEventListener("click", () => activate(t.dataset.tab)));
}

async function notifyAccountCreated({ email }) {
  const { notifyWebhookUrl } = getSettings();
  if (!notifyWebhookUrl) return { ok: false, skipped: true };

  try {
    const res = await fetch(notifyWebhookUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        event: "account_created",
        createdAt: new Date().toISOString(),
        email,
        source: "static_talent_network_mvp",
      }),
    });
    return { ok: res.ok, status: res.status };
  } catch (e) {
    return { ok: false, error: String(e?.message || e) };
  }
}

function wireAccountAndProfile() {
  const accountForm = $("#accountForm");
  const profileForm = $("#profileForm");
  const hint = $("#accountHint");

  const step1 = document.querySelector('[data-stepdot="1"]');
  const step2 = document.querySelector('[data-stepdot="2"]');

  function setStep(n) {
    step1?.classList.toggle("is-active", n === 1);
    step2?.classList.toggle("is-active", n === 2);
    profileForm?.classList.toggle("is-locked", n !== 2);
    profileForm?.classList.toggle("is-disabled", n !== 2);
  }

  const session = getSession();
  if (session?.email) {
    setStep(2);
    const emailInput = accountForm?.querySelector('input[name="email"]');
    if (emailInput) emailInput.value = session.email;
  } else {
    setStep(1);
  }

  accountForm?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const fd = new FormData(accountForm);
    const email = String(fd.get("email") || "").trim().toLowerCase();
    const password = String(fd.get("password") || "");

    if (!email || !password) return;

    const accounts = readAccounts();
    const exists = accounts.some((a) => String(a.email).toLowerCase() === email);
    if (!exists) {
      accounts.unshift({
        id: crypto?.randomUUID ? crypto.randomUUID() : String(Date.now()),
        email,
        createdAt: new Date().toISOString(),
      });
      writeAccounts(accounts);
      addSubmission("account_created", { email });
    }

    setSession(email);
    setStep(2);

    const n = await notifyAccountCreated({ email });
    if (hint) {
      if (n?.skipped) hint.textContent = "Cuenta creada. (Notificación: pendiente de configurar webhook)";
      else if (n?.ok) hint.textContent = "Cuenta creada. Notificación enviada.";
      else hint.textContent = "Cuenta creada. Notificación no enviada (revisa webhook).";
    }

    openModal(
      "Cuenta creada",
      `
      <p><strong>${esc(email)}</strong> ya tiene cuenta.</p>
      <p class="muted tiny">Ahora completa tu perfil para entrar al pipeline.</p>
      `
    );
  });

  profileForm?.addEventListener("submit", (e) => {
    e.preventDefault();
    const sessionNow = getSession();
    if (!sessionNow?.email) {
      openModal("Primero crea tu cuenta", "<p>Necesitas crear una cuenta con tu email antes de completar el perfil.</p>");
      return;
    }

    const data = formToObject(profileForm);
    data.email = sessionNow.email;

    addSubmission("revenue_profile", data);
    openModal("Solicitud enviada", "<p>Listo. Tu perfil quedó enviado para revisión.</p>");
    closeRegisterModal();
  });
}

function wireProfilePreviewBinding() {
  const profileForm = $("#profileForm");
  const preview = $("#profilePreview");
  if (!profileForm || !preview) return;

  function toChipsHtml(input, max = 10) {
    const raw = String(input || "").trim();
    if (!raw) return "";

    const parts = raw
      .split(/[\n,;|•]+/g)
      .map((s) => s.trim())
      .filter(Boolean);

    const uniq = [];
    const seen = new Set();
    for (const p of parts) {
      const key = p.toLowerCase();
      if (seen.has(key)) continue;
      seen.add(key);
      uniq.push(p);
      if (uniq.length >= max) break;
    }

    return uniq.map((t) => `<span class="tag">${esc(t)}</span>`).join("");
  }

  function update() {
    const data = formToObject(profileForm);
    const bind = (name) => preview.querySelector(`[data-bind="${name}"]`);
    const bindList = (name) => preview.querySelector(`[data-bindlist="${name}"]`);

    const fullName = (data.fullName || "").trim();
    if (fullName && bind("fullName")) bind("fullName").textContent = fullName;
    if (data.role && bind("role")) bind("role").textContent = data.role;
    if (data.bio && bind("bio")) {
      const el = bind("bio");
      if (el?.classList?.contains("profile-chips")) el.innerHTML = toChipsHtml(data.bio) || el.innerHTML;
      else el.textContent = data.bio;
    }

    if (Array.isArray(data.skills) && data.skills.length && bindList("skills")) {
      bindList("skills").textContent = data.skills.join(", ");
    }
    if (Array.isArray(data.stack) && data.stack.length && bindList("stack")) {
      bindList("stack").textContent = data.stack.slice(0, 6).join(", ");
    }
  }

  profileForm.addEventListener("input", update);
  profileForm.addEventListener("change", update);
  update();
}

function wirePhotoPreview() {
  const input = $("#photoInput");
  const img = $("#profilePhotoPreview");
  const fallback = $("#profilePhotoFallback");
  const photoWrap = img?.closest?.(".profile-photo");
  if (!input || !img || !photoWrap) return;

  input.addEventListener("change", () => {
    const file = input.files?.[0];
    if (!file) return;
    const url = URL.createObjectURL(file);
    img.src = url;
    photoWrap.classList.add("has-img");
    fallback?.setAttribute("aria-hidden", "true");
  });
}

function wireScrollReveal() {
  const prefersReduced =
    typeof window !== "undefined" &&
    typeof window.matchMedia === "function" &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (prefersReduced) return;

  const targets = [
    ...document.querySelectorAll(".hero-copy, .hero-card, .section, .footer-card, .product.card"),
  ].filter(Boolean);

  targets.forEach((el) => el.setAttribute("data-reveal", "true"));

  if (typeof IntersectionObserver !== "function") {
    targets.forEach((el) => el.setAttribute("data-revealed", "true"));
    return;
  }

  const io = new IntersectionObserver(
    (entries) => {
      entries.forEach((e) => {
        if (!e.isIntersecting) return;
        e.target.setAttribute("data-revealed", "true");
        io.unobserve(e.target);
      });
    },
    { threshold: 0.12, rootMargin: "0px 0px -10% 0px" }
  );

  targets.forEach((el) => io.observe(el));
}

// (Feed eliminado) — este MVP es landing + aplicación + perfil.

function addSubmission(type, payload) {
  const items = readStore();
  items.unshift({
    id: crypto?.randomUUID ? crypto.randomUUID() : String(Date.now()),
    type,
    createdAt: new Date().toISOString(),
    payload,
  });
  writeStore(items);
  return items[0];
}

function wireRevenueManagerForm() {
  // Deprecated (reemplazado por onboarding con cuenta + perfil).
}

function wireHotelForm() {
  const form = $("#hotelForm");
  form?.addEventListener("submit", (e) => {
    e.preventDefault();
    const data = formToObject(form);
    addSubmission("hotel_request", data);
    openModal(
      "Solicitud recibida",
      `
      <p><strong>Gracias, ${esc(data.name || "equipo")}</strong>. Recibimos tu solicitud.</p>
      <p class="muted">Te conectamos con el perfil adecuado una vez que confirmemos el alcance.</p>
      `
    );
    form.reset();
    closeHotelModal();
  });
}

function wireFooterActions() {
  // Footer actions removed to keep landing professional.
}

function wireModal() {
  $("#closeModal")?.addEventListener("click", closeModal);
  $("#okModal")?.addEventListener("click", closeModal);
  $("#modal")?.addEventListener("click", (e) => {
    if (e.target?.id === "modal") closeModal();
  });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeModal();
  });
}

document.addEventListener("DOMContentLoaded", () => {
  const footerYear = document.getElementById("footerYear");
  if (footerYear) footerYear.textContent = String(new Date().getFullYear());

  wireAccountAndProfile();
  wireProfilePreviewBinding();
  wirePhotoPreview();
  wireScrollReveal();
  wireHotelForm();
  wireFooterActions();
  wireModal();

  $("#openRegisterTop")?.addEventListener("click", openRegisterModal);
  $("#openRegisterHero")?.addEventListener("click", openRegisterModal);
  $("#openRegisterBottom")?.addEventListener("click", openRegisterModal);
  $("#openRegisterHow")?.addEventListener("click", openRegisterModal);
  $("#openRegisterMockFooter")?.addEventListener("click", openRegisterModal);
  $("#openRegisterFooter")?.addEventListener("click", openRegisterModal);

  $("#openHotelTop")?.addEventListener("click", openHotelModal);
  $("#openHotelHero")?.addEventListener("click", openHotelModal);
  $("#openHotelBottom")?.addEventListener("click", openHotelModal);
  $("#openHotelFooter")?.addEventListener("click", openHotelModal);

  $("#closeRegisterModal")?.addEventListener("click", closeRegisterModal);
  $("#dismissRegisterModal")?.addEventListener("click", closeRegisterModal);

  $("#closeHotelModal")?.addEventListener("click", closeHotelModal);
  $("#dismissHotelModal")?.addEventListener("click", closeHotelModal);
});

