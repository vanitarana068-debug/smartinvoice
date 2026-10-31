(() => {
  "use strict";

  const NAV = [
    { id: "dashboard", label: "Dashboard", section: "WORKSPACE", icon: "grid" },
    { id: "invoices", label: "Invoices", icon: "file" },
    { id: "customers", label: "Customers", icon: "users" },
    { id: "revenue", label: "Revenue", section: "MONEY", icon: "trend" },
    { id: "expenses", label: "Expenses", icon: "receipt" },
    { id: "profit-loss", label: "Profit & loss", icon: "pie" },
    { id: "cash-flow", label: "Cash flow", icon: "waves" },
    { id: "payments", label: "Payments", icon: "card" },
    { id: "reminders", label: "Reminders", icon: "bell" },
    { id: "analytics", label: "Analytics", section: "INTELLIGENCE", icon: "chart" },
    { id: "ai-insights", label: "AI Business Insights", icon: "sparkle" },
    { id: "reports", label: "Reports", section: "ACCOUNT", icon: "report" },
    { id: "settings", label: "Settings", icon: "settings" },
  ];
  const ICONS = {
    grid: '<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/>',
    file: '<path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"/><path d="M13 2v7h7M8 13h8M8 17h8"/>',
    users: '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8zM22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/>',
    trend: '<path d="m22 7-8.5 8.5-5-5L2 17"/><path d="M16 7h6v6"/>',
    receipt: '<path d="M4 3v18l3-2 3 2 3-2 3 2 4-2V3H4z"/><path d="M8 8h8M8 12h8"/>',
    pie: '<path d="M21 12a9 9 0 1 1-9-9v9z"/><path d="M16 3.5A9 9 0 0 1 20.5 8H16z"/>',
    waves: '<path d="M2 12h3l3-9 5 18 3-9h3l2 4h3"/>',
    card: '<rect x="2" y="5" width="20" height="14" rx="2"/><path d="M2 10h20"/>',
    bell: '<path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9"/><path d="M10 21h4"/>',
    chart: '<path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-5 5"/>',
    sparkle: '<path d="m12 3 1.9 5.8L20 11l-6.1 2.2L12 19l-1.9-5.8L4 11l6.1-2.2L12 3z"/><path d="m19 14 .9 2.1L22 17l-2.1.9L19 20l-.9-2.1L16 17l2.1-.9L19 14z"/>',
    report: '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6M8 13h8M8 17h8"/>',
    settings: '<circle cx="12" cy="12" r="3"/><path d="m19.4 15 .1.1 1.4 1.1-1.4 2.4-1.7-.7a8.6 8.6 0 0 1-1.7 1L16 21h-3l-.3-1.9a8.6 8.6 0 0 1-1.7-1l-1.7.7-1.4-2.4 1.4-1.1a7.1 7.1 0 0 1 0-2l-1.4-1.1 1.4-2.4 1.7.7a8.6 8.6 0 0 1 1.7-1L13 7h3l.3 1.9a8.6 8.6 0 0 1 1.7 1l1.7-.7 1.4 2.4-1.4 1.1a7.1 7.1 0 0 1-.3 2.3z" transform="translate(-1 -2)"/>',
    plus: '<path d="M12 5v14M5 12h14"/>',
    search: '<circle cx="11" cy="11" r="7"/><path d="m20 20-4-4"/>',
    chevron: '<path d="m9 18 6-6-6-6"/>',
    arrow: '<path d="M7 17 17 7M7 7h10v10"/>',
    download: '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3"/>',
    clock: '<circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>',
    check: '<path d="m5 12 4 4L19 6"/>',
    close: '<path d="m18 6-12 12M6 6l12 12"/>',
    menu: '<path d="M3 6h18M3 12h18M3 18h18"/>',
    calendar: '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M16 3v4M8 3v4M3 11h18"/>',
    bank: '<path d="m3 10 9-7 9 7M4 10h16M6 10v9M10 10v9M14 10v9M18 10v9M3 21h18"/>',
    warning: '<path d="m10.3 3.9-8.1 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.7-3.1l-8.1-14a2 2 0 0 0-3.3 0z"/><path d="M12 9v4M12 17h.01"/>',
  };
  const state = { user: null, settings: { currency: "USD", business_name: "" }, page: "dashboard",
    collapsed: localStorage.getItem("sidebar-collapsed") === "1", modalCustomer: null, search: "" };
  const app = document.getElementById("app");
  const modal = document.getElementById("modal");

  function icon(name, cls = "") {
    return `<svg class="icon ${cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${ICONS[name] || ""}</svg>`;
  }
  function esc(value) {
    return String(value ?? "").replace(/[&<>"']/g, (c) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
    })[c]);
  }
  function currency(value, compact = false) {
    const number = Number(value || 0);
    try {
      return new Intl.NumberFormat(undefined, {
        style: "currency", currency: state.settings.currency || "USD",
        notation: compact && Math.abs(number) >= 10000 ? "compact" : "standard",
        maximumFractionDigits: 2,
      }).format(number);
    } catch {
      return `${state.settings.currency || "USD"} ${number.toLocaleString(undefined, { maximumFractionDigits: 2 })}`;
    }
  }
  function dateLabel(value) {
    if (!value) return "—";
    return new Intl.DateTimeFormat(undefined, { month: "short", day: "numeric", year: "numeric" })
      .format(new Date(`${value.slice(0, 10)}T12:00:00`));
  }
  async function api(path, options = {}) {
    const response = await fetch(`/api/${path}`, {
      credentials: "same-origin", ...options,
      headers: { ...(options.body ? { "Content-Type": "application/json" } : {}),
        ...(options.headers || {}) },
    });
    if (response.status === 204) return null;
    const type = response.headers.get("content-type") || "";
    if (!type.includes("application/json")) {
      if (!response.ok) throw new Error("The request could not be completed.");
      return response;
    }
    const data = await response.json();
    if (!response.ok || data.error) throw new Error(data.error || "Something went wrong. Please try again.");
    return data;
  }
  function toast(message, type = "success") {
    const region = document.getElementById("toast-region");
    const node = document.createElement("div");
    node.className = `toast toast-${type}`;
    node.innerHTML = `${icon(type === "error" ? "warning" : "check")}<span>${esc(message)}</span>`;
    region.append(node);
    window.setTimeout(() => node.remove(), 3900);
  }
  async function refreshUser() {
    try {
      const data = await api("me");
      state.user = data.user;
      state.settings = data.settings;
      renderShell();
      await renderPage();
    } catch {
      renderAuth("login");
    }
  }
  function renderAuth(mode = "login") {
    const register = mode === "register";
    app.innerHTML = `
      <main class="auth-page">
        <section class="auth-story">
          <a class="brand brand-light" href="/" aria-label="Smart Invoice AI home"><span class="brand-mark">s.</span><span class="brand-copy"><strong>smart invoice <span class="brand-ai">AI</span></strong><small>by your side, in the numbers</small></span></a>
          <div class="story-content">
            <div class="eyebrow eyebrow-dark"><span class="live-dot"></span> YOUR BUSINESS, IN BETTER SHAPE</div>
            <h1>Make room<br>for <span>what's next.</span></h1>
            <p>Invoices, expenses and the big picture—all in one calm, clear place.</p>
            <div class="story-preview">
              <div class="preview-top"><span class="preview-label">YOUR CASH FLOW</span><span class="preview-pill">↗ Looking healthy</span></div>
              <div class="preview-value">$24,680<span>.00</span></div>
              <svg class="preview-chart" viewBox="0 0 520 100" preserveAspectRatio="none" aria-label="Rising business cash-flow chart"><defs><linearGradient id="preview-fill" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="#83a6ff" stop-opacity=".32"/><stop offset="1" stop-color="#83a6ff" stop-opacity="0"/></linearGradient></defs><path d="M0 81 C40 78 52 68 90 72 S140 81 175 59 S228 63 254 44 S300 56 342 37 S395 43 425 20 S480 34 520 8 L520 100 L0 100Z" fill="url(#preview-fill)"/><path d="M0 81 C40 78 52 68 90 72 S140 81 175 59 S228 63 254 44 S300 56 342 37 S395 43 425 20 S480 34 520 8" fill="none" stroke="#a9c1ff" stroke-width="3" stroke-linecap="round"/></svg>
              <div class="preview-months"><span>JAN</span><span>FEB</span><span>MAR</span><span>APR</span><span>MAY</span><span>JUN</span></div>
            </div>
            <div class="story-foot"><span class="story-avatar">S</span><span>Built for the people<br>building something.</span><span class="story-stars">★★★★★</span></div>
          </div>
          <div class="story-orb story-orb-one"></div><div class="story-orb story-orb-two"></div>
          <p class="story-bottom">Thoughtful tools for the business you're growing.</p>
        </section>
        <section class="auth-main">
          <div class="auth-topline">ALREADY A CUSTOMER? <button class="text-button" data-auth-mode="${register ? "login" : "register"}">${register ? "Sign in" : "Create account"}</button></div>
          <form id="auth-form" class="auth-form">
            <div class="auth-icon">${icon(register ? "sparkle" : "bank")}</div>
            <div class="eyebrow">YOUR FINANCES, FINALLY IN SYNC</div>
            <h2>${register ? "Your next chapter starts here." : "Welcome back."}</h2>
            <p class="auth-subtitle">${register ? "Set up your free workspace. No credit card, no spreadsheets." : "Sign in to pick up right where you left off."}</p>
            ${register ? `<label class="field-label">Your name<input class="field-input" name="name" autocomplete="name" placeholder="Alex Morgan" required maxlength="80"></label>` : ""}
            <label class="field-label">Work email<input class="field-input" type="email" name="email" autocomplete="email" placeholder="you@company.com" required maxlength="254"></label>
            <label class="field-label">Password<input class="field-input" type="password" name="password" autocomplete="${register ? "new-password" : "current-password"}" placeholder="${register ? "At least 8 characters" : "Enter your password"}" minlength="${register ? "8" : "1"}" required></label>
            ${register ? `<p class="password-note">Use at least 8 characters. Your data is private to your account.</p>` : ""}
            <div id="auth-error" class="auth-error" role="alert"></div>
            <button type="submit" class="button button-primary auth-submit">${register ? "Create your workspace" : "Sign in to your workspace"} ${icon("chevron")}</button>
            <div class="auth-divider"><span>YOUR BUSINESS DATA STAYS YOURS</span></div>
            <p class="auth-privacy">${icon("check")} Private to your workspace—never shared with other accounts.</p>
          </form>
          <footer class="auth-footer"><span>© ${new Date().getFullYear()} Smart Invoice AI</span><span>Built for independent business</span></footer>
        </section>
      </main>`;
    app.querySelector("[data-auth-mode]").addEventListener("click", (event) => {
      renderAuth(event.currentTarget.dataset.authMode);
    });
    app.querySelector("#auth-form").addEventListener("submit", async (event) => {
      event.preventDefault();
      const form = new FormData(event.currentTarget);
      const button = event.currentTarget.querySelector('[type="submit"]');
      const error = app.querySelector("#auth-error");
      button.disabled = true;
      button.textContent = register ? "Creating your workspace…" : "Signing you in…";
      error.textContent = "";
      try {
        const data = await api(register ? "register" : "login", {
          method: "POST", body: JSON.stringify(Object.fromEntries(form.entries())),
        });
        state.user = data.user;
        state.settings = data.settings;
        state.page = "dashboard";
        renderShell();
        await renderPage();
      } catch (err) {
        error.textContent = err.message;
        button.disabled = false;
        button.innerHTML = `${register ? "Create your workspace" : "Sign in to your workspace"} ${icon("chevron")}`;
      }
    });
  }
  function renderShell() {
    const current = NAV.find((item) => item.id === state.page) || NAV[0];
    app.innerHTML = `
      <div class="app-shell ${state.collapsed ? "is-collapsed" : ""}">
        <aside class="sidebar" id="sidebar">
          <a class="brand brand-light sidebar-brand" href="#" data-page="dashboard"><span class="brand-mark">s.</span><span class="brand-copy"><strong>smart invoice <span class="brand-ai">AI</span></strong><small>FINANCE, IN FOCUS</small></span></a>
          <button class="workspace-switch" type="button" data-page="settings"><span class="workspace-avatar">${esc((state.settings.business_name || state.user.name).slice(0, 1).toUpperCase())}</span><span class="workspace-info"><strong>${esc(state.settings.business_name || "Your workspace")}</strong><small>Free workspace</small></span>${icon("chevron", "workspace-chevron")}</button>
          <nav class="side-nav" aria-label="Main navigation">
            ${NAV.map((item) => `${item.section ? `<div class="nav-section">${esc(item.section)}</div>` : ""}
              <button class="nav-item ${state.page === item.id ? "active" : ""}" type="button" data-page="${item.id}" title="${esc(item.label)}">
                ${icon(item.icon)}<span>${esc(item.label)}</span>${item.id === "ai-insights" ? '<span class="nav-new">AI</span>' : ""}
              </button>`).join("")}
          </nav>
          <div class="sidebar-bottom">
            <div class="sidebar-help"><div class="help-icon">${icon("sparkle")}</div><strong>A clearer picture starts here.</strong><p>Get the insights you need to make your next move.</p><button type="button" data-page="ai-insights">Explore AI insights ${icon("arrow")}</button></div>
            <button type="button" class="collapse-button" id="collapse-sidebar" aria-label="Collapse sidebar">${icon("chevron")}<span>Collapse menu</span></button>
            <div class="user-card"><div class="user-avatar">${esc(initials(state.user.name))}</div><div class="user-details"><strong>${esc(state.user.name)}</strong><small>${esc(state.user.email)}</small></div><button class="user-menu-button" type="button" id="logout-button" title="Sign out" aria-label="Sign out">${icon("arrow")}</button></div>
          </div>
        </aside>
        <main class="main-area">
          <header class="topbar">
            <div class="topbar-left"><button class="mobile-menu" id="mobile-menu" aria-label="Toggle navigation">${icon("menu")}</button><span class="breadcrumb">Workspace</span>${icon("chevron", "breadcrumb-chevron")}<span class="breadcrumb-current">${esc(current.label)}</span></div>
            <div class="topbar-right">
              <label class="search-wrap">${icon("search")}<input type="search" id="global-search" placeholder="Search anything..." autocomplete="off" aria-label="Search current page"><kbd>Ctrl K</kbd></label>
              <span class="today-label">${new Intl.DateTimeFormat(undefined, { weekday: "short", month: "short", day: "numeric" }).format(new Date())}</span>
              <button type="button" class="button button-primary top-create" data-create="invoice">${icon("plus")}<span>New invoice</span></button>
            </div>
          </header>
          <div id="page-content" class="page-content"><div class="page-loading"><i></i> Loading your finances…</div></div>
        </main>
      </div>`;
    app.querySelector("#collapse-sidebar").addEventListener("click", () => {
      state.collapsed = !state.collapsed;
      localStorage.setItem("sidebar-collapsed", state.collapsed ? "1" : "0");
      app.querySelector(".app-shell").classList.toggle("is-collapsed", state.collapsed);
    });
    app.querySelector("#mobile-menu").addEventListener("click", () => {
      app.querySelector(".sidebar").classList.toggle("mobile-open");
    });
    app.querySelector("#logout-button").addEventListener("click", async () => {
      try {
        await api("logout", { method: "POST" });
        state.user = null;
        renderAuth();
      } catch (err) { toast(err.message, "error"); }
    });
    app.querySelector("#global-search").addEventListener("input", (event) => {
      state.search = event.target.value.trim().toLowerCase();
      filterRows();
    });
  }
  function initials(name) {
    return String(name || "").split(/[\s@._-]+/).filter(Boolean).slice(0, 2).map((part) => part[0]).join("").toUpperCase() || "S";
  }
  function pageTitle(title, subtitle, action = "") {
    return `<div class="page-heading"><div><div class="eyebrow">${esc(title === "Dashboard" ? "YOUR BUSINESS AT A GLANCE" : "FINANCIAL WORKSPACE")}</div><h1>${esc(title)}</h1><p>${esc(subtitle)}</p></div><div class="heading-actions">${action}</div></div>`;
  }
  function button(label, options = {}) {
    return `<button type="button" class="button ${options.className || "button-secondary"}" ${options.create ? `data-create="${esc(options.create)}"` : ""} ${options.action ? `data-action="${esc(options.action)}"` : ""}>${options.icon ? icon(options.icon) : ""}${esc(label)}</button>`;
  }
  function metric(label, value, note, iconName, tone, extra = "") {
    return `<article class="metric-card"><div class="metric-top"><span class="metric-label">${esc(label)}</span><span class="metric-icon metric-${tone}">${icon(iconName)}</span></div><div class="metric-value">${value}</div><div class="metric-note">${extra}${esc(note)}</div></article>`;
  }
  function badge(status) {
    const classes = { paid: "badge-success", sent: "badge-blue", draft: "badge-neutral", overdue: "badge-danger" };
    const labels = { paid: "Paid", sent: "Awaiting payment", draft: "Draft", overdue: "Overdue" };
    return `<span class="status-badge ${classes[status] || "badge-neutral"}"><i></i>${labels[status] || esc(status)}</span>`;
  }
  function emptyState(iconName, title, copy, create, label) {
    return `<div class="empty-state"><div class="empty-icon">${icon(iconName)}</div><h3>${esc(title)}</h3><p>${esc(copy)}</p>${create ? `<button class="button button-primary" type="button" data-create="${esc(create)}">${icon("plus")}${esc(label)}</button>` : ""}</div>`;
  }
  function table(headers, rows, empty) {
    return rows.length
      ? `<div class="table-scroll"><table><thead><tr>${headers.map((header) => `<th>${header}</th>`).join("")}</tr></thead><tbody>${rows.join("")}</tbody></table></div>`
      : empty;
  }
  function initialsTone(str = "") {
    return ["avatar-blue", "avatar-purple", "avatar-teal", "avatar-orange", "avatar-pink"][Array.from(str).reduce((sum, char) => sum + char.charCodeAt(0), 0) % 5];
  }
  function customerAvatar(name) {
    return `<span class="customer-avatar ${initialsTone(name)}">${esc(initials(name))}</span>`;
  }
  function chartSvg(months, type = "both", height = 220) {
    const width = 720;
    const pad = { top: 15, right: 12, bottom: 34, left: 12 };
    const innerW = width - pad.left - pad.right;
    const innerH = height - pad.top - pad.bottom;
    const values = months.flatMap((m) => type === "revenue" ? [m.revenue] : type === "expenses" ? [m.expenses] : [m.revenue, m.expenses]);
    const max = Math.max(...values, 1) * 1.18;
    const step = innerW / Math.max(months.length, 1);
    const y = (v) => pad.top + innerH - Number(v || 0) / max * innerH;
    const grid = [0.25, 0.5, 0.75, 1].map((p) => `<line x1="${pad.left}" y1="${pad.top + innerH * (1 - p)}" x2="${width - pad.right}" y2="${pad.top + innerH * (1 - p)}" stroke="#eef0f4" stroke-dasharray="4 5"/>`).join("");
    const bars = months.map((month, i) => {
      const center = pad.left + step * (i + 0.5);
      const barW = Math.min(20, step * 0.24);
      const revenue = type === "expenses" ? 0 : Number(month.revenue);
      const expense = type === "revenue" ? 0 : Number(month.expenses);
      const barsHtml = type === "both"
        ? `<rect class="chart-bar-revenue" x="${center - barW - 2}" y="${y(revenue)}" width="${barW}" height="${Math.max(1, pad.top + innerH - y(revenue))}" rx="4"><title>${esc(month.month)} revenue: ${esc(currency(revenue))}</title></rect><rect class="chart-bar-expense" x="${center + 2}" y="${y(expense)}" width="${barW}" height="${Math.max(1, pad.top + innerH - y(expense))}" rx="4"><title>${esc(month.month)} expenses: ${esc(currency(expense))}</title></rect>`
        : `<rect class="${type === "revenue" ? "chart-bar-revenue" : "chart-bar-expense"}" x="${center - Math.min(26, step * 0.29) / 2}" y="${y(type === "revenue" ? revenue : expense)}" width="${Math.min(26, step * 0.29)}" height="${Math.max(1, pad.top + innerH - y(type === "revenue" ? revenue : expense))}" rx="4"><title>${esc(month.month)}: ${esc(currency(type === "revenue" ? revenue : expense))}</title></rect>`;
      return `${barsHtml}<text x="${center}" y="${height - 8}" text-anchor="middle" fill="#98a2b3" font-size="11">${esc(month.month)}</text>`;
    }).join("");
    return `<svg class="chart-svg" viewBox="0 0 ${width} ${height}" role="img" aria-label="Six-month cash flow chart">${grid}${bars}</svg>`;
  }
  function chartLegend(items) {
    return `<div class="chart-legend">${items.map(([name, color]) => `<span><i style="--legend-color:${color}"></i>${esc(name)}</span>`).join("")}</div>`;
  }
  function sectionHeader(title, linkPage = "") {
    return `<div class="card-title-row"><h2>${esc(title)}</h2>${linkPage ? `<button class="link-button" type="button" data-page="${linkPage}">View all ${icon("chevron")}</button>` : ""}</div>`;
  }
  async function renderPage() {
    const content = app.querySelector("#page-content");
    if (!content) return;
    content.innerHTML = '<div class="page-loading"><i></i> Loading your finances…</div>';
    try {
      const page = state.page;
      let html;
      if (page === "dashboard") html = await renderDashboard();
      else if (page === "invoices") html = await renderInvoices();
      else if (page === "customers") html = await renderCustomers();
      else if (page === "expenses") html = await renderExpenses();
      else if (page === "payments") html = await renderPayments();
      else if (page === "reminders") html = await renderReminders();
      else if (page === "revenue") html = await renderFinancePage("revenue");
      else if (page === "profit-loss") html = await renderFinancePage("profit-loss");
      else if (page === "cash-flow") html = await renderFinancePage("cash-flow");
      else if (page === "analytics") html = await renderAnalytics();
      else if (page === "ai-insights") html = await renderInsights();
      else if (page === "reports") html = renderReports();
      else if (page === "settings") html = await renderSettings();
      else html = await renderDashboard();
      if (app.querySelector("#page-content")) {
        content.innerHTML = html;
        filterRows();
      }
    } catch (err) {
      content.innerHTML = `<div class="error-panel">${icon("warning")}<div><strong>We couldn't load this page.</strong><p>${esc(err.message)}</p><button class="button button-secondary" data-action="refresh">Try again</button></div></div>`;
    }
  }
  function changeLabel(value, current) {
    if (value === null) return current ? "New activity this month" : "No change from last month";
    const change = Number(value);
    return change === 0 ? "No change from last month" : `${change > 0 ? "Up" : "Down"} ${Math.abs(change)}% from last month`;
  }
  async function renderDashboard() {
    const d = await api("dashboard");
    const rev = Number(d.revenue);
    const spend = Number(d.expenses);
    const profit = Number(d.profit);
    const estimatedCash = d.estimated_cash_balance;
    const recent = d.recent.map((item) => `<tr data-searchable><td><span class="activity-kind ${item.type === "payment" ? "kind-income" : "kind-expense"}">${icon(item.type === "payment" ? "arrow" : "receipt")}</span><span class="row-main">${esc(item.label)}<small>${esc(item.detail || (item.type === "payment" ? "Client payment" : "Business expense"))}</small></span></td><td>${dateLabel(item.date)}</td><td><span class="${item.type === "payment" ? "amount-in" : "amount-out"}">${item.type === "payment" ? "+" : "−"}${currency(item.amount)}</span></td></tr>`);
    const attention = d.attention.map((item) => `<div class="attention-row">${customerAvatar(item.customer_name)}<div class="attention-info"><strong>${esc(item.customer_name)}</strong><small>${esc(item.number)} · due ${dateLabel(item.due_date)}</small></div><div class="attention-right"><strong>${currency(item.balance)}</strong>${badge("overdue")}</div><button class="icon-button reminder-one" data-invoice="${item.id}" aria-label="Record reminder sent">${icon("bell")}</button></div>`);
    const top = d.top_customers.filter((c) => Number(c.collected) > 0).slice(0, 4);
    return `<div class="page-wrap">
      ${pageTitle("Dashboard", `Here's where things stand for ${esc(d.month)}.`, `<button class="button button-secondary" data-action="refresh">${icon("calendar")} ${esc(d.month)}</button>`)}
      <div class="welcome-banner"><div class="welcome-mark">${icon("sparkle")}</div><div><span>YOUR FINANCIAL SNAPSHOT</span><h2>A little more clarity. A lot more confidence.</h2><p>Every number, payment, and opportunity—right where you need it.</p></div><div class="banner-orb"></div><button class="banner-action" data-page="ai-insights">Explore your insights ${icon("arrow")}</button></div>
      <div class="metrics-grid metrics-five">
        ${metric("Collected this month", currency(rev, true), changeLabel(d.revenue_change, rev), "trend", "blue", `<span class="${Number(d.revenue_change) > 0 ? "positive" : Number(d.revenue_change) < 0 ? "negative" : ""}">${d.revenue_change === null ? "✦ " : Number(d.revenue_change) > 0 ? "↗ " : Number(d.revenue_change) < 0 ? "↘ " : "· "}</span>`)}
        ${metric("Expenses this month", currency(spend, true), changeLabel(d.expense_change, spend), "receipt", "orange", `<span class="${Number(d.expense_change) < 0 ? "positive" : Number(d.expense_change) > 0 ? "negative" : ""}">${d.expense_change === null ? "✦ " : Number(d.expense_change) > 0 ? "↗ " : Number(d.expense_change) < 0 ? "↘ " : "· "}</span>`)}
        ${metric("Net profit", `<span class="${profit < 0 ? "negative" : ""}">${currency(profit, true)}</span>`, "Collections minus business expenses", "pie", profit < 0 ? "red" : "green", "")}
        ${metric("Awaiting payment", currency(d.outstanding, true), `${d.overdue_count} overdue · ${currency(d.overdue_amount)} past due`, "clock", d.overdue_count ? "red" : "cyan", `<span class="${d.overdue_count ? "negative" : "positive"}">● </span>`)}
        ${estimatedCash === null ? metric("Estimated cash", "Not set", "Add an opening balance in Settings", "bank", "cyan", "") : metric("Estimated cash", currency(estimatedCash, true), d.low_cash_balance ? "Below one month of recorded costs" : "Opening balance plus transactions", "bank", d.low_cash_balance ? "red" : "cyan", "")}
      </div>
      <div class="dashboard-grid">
        <section class="card chart-card"><div class="card-heading">${sectionHeader("Cash flow over time", "cash-flow")}<div class="chart-caption">Collected revenue vs. expenses · last 6 months</div></div>${chartLegend([["Collected", "#3978f6"], ["Expenses", "#e7a14d"]])}${chartSvg(d.months)}<div class="chart-footnote">${icon("bank")} Based on real payments received and expenses recorded.</div></section>
        <section class="card attention-card">${sectionHeader("Needs your attention", "reminders")}${attention.length ? `<div class="attention-list">${attention.join("")}</div><button class="text-action" data-page="reminders">See all reminders ${icon("chevron")}</button>` : `<div class="calm-state"><div class="calm-icon">${icon("check")}</div><strong>You're all caught up.</strong><p>No overdue invoices to chase right now.</p></div>`}</section>
      </div>
      <div class="dashboard-grid lower-grid">
        <section class="card table-card">${sectionHeader("Recent activity", "payments")}${table(["TRANSACTION", "DATE", "AMOUNT"], recent, emptyState("waves", "Your story starts here.", "Once you record a payment or expense, you'll see it right here.", "invoice", "Create an invoice"))}</section>
        <section class="card customers-card">${sectionHeader("Your best customers", "customers")}${top.length ? `<div class="top-customer-list">${top.map((c, i) => `<div class="top-customer-row">${customerAvatar(c.name)}<div class="top-customer-info"><strong>${esc(c.name)}</strong><small>${c.invoice_count} invoice${c.invoice_count === 1 ? "" : "s"}</small></div><div class="top-customer-total"><strong>${currency(c.collected)}</strong><span>collected</span></div><span class="customer-rank">0${i + 1}</span></div>`).join("")}</div>` : `<div class="calm-state"><div class="calm-icon">${icon("users")}</div><strong>Your next great client starts here.</strong><p>Add a customer and record a payment to discover who's driving your growth.</p><button class="button button-secondary" data-create="customer">${icon("plus")} Add a customer</button></div>`}</section>
      </div>
      <div class="footnote">${icon("check")} Your dashboard uses cash-basis accounting: revenue is recorded when payments are received.</div>
    </div>`;
  }
  async function renderInvoices() {
    const [{ invoices }, { customers }] = await Promise.all([api("invoices"), api("customers")]);
    const sent = invoices.filter((i) => i.status !== "draft");
    const overdue = invoices.filter((i) => i.status === "overdue");
    const open = invoices.filter((i) => i.status === "sent");
    const rows = invoices.map((i) => `<tr data-searchable><td><div class="invoice-num">${esc(i.number)}<small>${esc(i.description || i.service_category)}</small></div></td><td>${customerAvatar(i.customer_name)}<span class="table-customer">${esc(i.customer_name)}</span></td><td>${dateLabel(i.issue_date)}</td><td>${dateLabel(i.due_date)}</td><td class="amount-cell">${currency(i.amount)}</td><td>${badge(i.status)}</td><td><strong class="balance-cell">${currency(i.balance)}</strong></td><td><div class="invoice-actions"><button class="icon-button" data-preview-invoice="${i.id}" title="View and print invoice" aria-label="View and print ${esc(i.number)}">${icon("file")}</button>${i.status !== "draft" && i.balance > 0 ? `<button class="icon-button" data-pay-invoice="${i.id}" title="Record a payment" aria-label="Record a payment for ${esc(i.number)}">${icon("plus")}</button>` : i.status === "draft" ? `<button class="icon-button send-invoice" data-send-invoice="${i.id}" title="Mark invoice as sent" aria-label="Mark ${esc(i.number)} as sent">${icon("arrow")}</button><button class="icon-button danger-icon" data-delete-invoice="${i.id}" title="Delete draft invoice" aria-label="Delete draft invoice">${icon("close")}</button>` : ""}</div></td></tr>`);
    return `<div class="page-wrap">${pageTitle("Invoices", "A clear record of every project, payment and due date.", button("New invoice", { create: "invoice", icon: "plus", className: "button-primary" }))}
      <div class="metrics-grid metrics-compact">
        ${metric("Total invoices", sent.length, "Sent to your customers", "file", "blue", "")}
        ${metric("Needs a nudge", overdue.length, currency(overdue.reduce((sum, i) => sum + Number(i.balance), 0)) + " overdue", "bell", overdue.length ? "red" : "green", "")}
        ${metric("Awaiting payment", open.length, "Sent, not yet overdue", "clock", "cyan", "")}
      </div>
      <section class="card full-table-card"><div class="table-toolbar">${sectionHeader("All invoices")}<div class="toolbar-filter" role="group" aria-label="Filter invoices"><button class="filter-chip selected" data-filter="all">All <span>${invoices.length}</span></button><button class="filter-chip" data-filter="sent">Open <span>${open.length}</span></button><button class="filter-chip" data-filter="overdue">Overdue <span>${overdue.length}</span></button><button class="filter-chip" data-filter="paid">Paid <span>${invoices.filter(i => i.status === "paid").length}</span></button></div></div>
      ${table(["INVOICE", "CUSTOMER", "ISSUED", "DUE DATE", "TOTAL", "STATUS", "BALANCE", ""], rows, emptyState("file", "No invoices yet.", "Create your first invoice and start keeping your projects and payments in sync.", "invoice", "Create your first invoice"))}</section>
      ${customers.length ? `<div class="footnote">${icon("check")} Partial payments are tracked automatically. Paid invoices stay in your financial history.</div>` : ""}</div>`;
  }
  async function renderCustomers() {
    const { customers } = await api("customers");
    const rows = customers.map((c) => `<tr data-searchable><td>${customerAvatar(c.name)}<span class="table-customer"><strong>${esc(c.name)}</strong><small>${esc(c.company || "Independent client")}</small></span></td><td>${esc(c.email || "—")}</td><td>${c.invoice_count}</td><td>${currency(c.collected)}</td><td><button class="icon-button" data-edit-customer="${c.id}" title="Edit customer" aria-label="Edit ${esc(c.name)}">${icon("settings")}</button><button class="icon-button danger-icon" data-delete-customer="${c.id}" title="Delete customer" aria-label="Delete ${esc(c.name)}">${icon("close")}</button></td></tr>`);
    const total = customers.reduce((sum, c) => sum + Number(c.collected), 0);
    return `<div class="page-wrap">${pageTitle("Customers", "The people and businesses behind your progress.", button("Add customer", { create: "customer", icon: "plus", className: "button-primary" }))}
      <div class="metrics-grid metrics-compact">${metric("Customer relationships", customers.length, "Clients in your workspace", "users", "blue", "")}${metric("Revenue collected", currency(total), "Across all customers", "trend", "green", "")}${metric("Active this month", customers.filter((c) => Number(c.collected) > 0).length, "Customers who've paid you", "check", "cyan", "")}</div>
      <section class="card full-table-card">${sectionHeader("Your customers")}${table(["CUSTOMER", "EMAIL", "INVOICES", "COLLECTED", ""], rows, emptyState("users", "Your clients, all in one place.", "Add a customer once, then connect them to every project and invoice.", "customer", "Add your first customer"))}</section></div>`;
  }
  async function renderExpenses() {
    const { expenses } = await api("expenses");
    const total = expenses.reduce((sum, item) => sum + Number(item.amount), 0);
    const categoryMap = Object.groupBy ? Object.groupBy(expenses, (e) => e.category) : expenses.reduce((map, e) => ((map[e.category] ||= []).push(e), map), {});
    const categories = Object.entries(categoryMap).map(([name, list]) => [name, list.reduce((sum, item) => sum + Number(item.amount), 0)]).sort((a, b) => b[1] - a[1]);
    const rows = expenses.map((e) => `<tr data-searchable><td><span class="expense-category-icon">${icon("receipt")}</span><span class="row-main">${esc(e.category)}<small>${esc(e.description || "Business expense")}</small></span></td><td>${dateLabel(e.expense_date)}</td><td>${esc(e.service_category || "—")}</td><td class="amount-cell">${currency(e.amount)}</td><td><button class="icon-button danger-icon" data-delete-expense="${e.id}" title="Delete expense" aria-label="Delete expense">${icon("close")}</button></td></tr>`);
    return `<div class="page-wrap">${pageTitle("Expenses", "Know what it costs to keep your business moving.", button("Add expense", { create: "expense", icon: "plus", className: "button-primary" }))}
      <div class="metrics-grid metrics-compact">${metric("Recorded expenses", expenses.length, "Business costs on file", "receipt", "orange", "")}${metric("Total expenses", currency(total), "All recorded expenses", "pie", "red", "")}${metric("Top category", categories[0] ? esc(categories[0][0]) : "Not yet", categories[0] ? currency(categories[0][1]) + " spent" : "Record your first expense", "chart", "blue", "")}</div>
      <section class="card full-table-card">${sectionHeader("Your expenses")}${table(["EXPENSE", "DATE", "SERVICE", "AMOUNT", ""], rows, emptyState("receipt", "Every business has its costs.", "Record a business expense to understand where your money goes.", "expense", "Add your first expense"))}</section></div>`;
  }
  async function renderPayments() {
    const [{ payments }, { invoices }] = await Promise.all([api("payments"), api("invoices")]);
    const rows = payments.map((p) => `<tr data-searchable><td><span class="payment-cell-icon">${icon("check")}</span><span class="row-main">${esc(p.customer_name)}<small>Invoice ${esc(p.invoice_number)}</small></span></td><td>${dateLabel(p.paid_at)}</td><td>${esc(p.method)}</td><td class="amount-in amount-cell">+${currency(p.amount)}</td></tr>`);
    const total = payments.reduce((sum, p) => sum + Number(p.amount), 0);
    return `<div class="page-wrap">${pageTitle("Payments", "Every dollar received, accounted for.", button("Record a payment", { create: "payment", icon: "plus", className: "button-primary" }))}
      <div class="metrics-grid metrics-compact">${metric("Payments received", payments.length, "Recorded transactions", "card", "green", "")}${metric("Total collected", currency(total), "Income recorded in your books", "trend", "blue", "")}${metric("Still to collect", currency(invoices.filter(i => i.status !== "draft").reduce((sum, i) => sum + Number(i.balance), 0)), "Across sent invoices", "clock", "cyan", "")}</div>
      <section class="card full-table-card">${sectionHeader("Payment history")}${table(["CUSTOMER & INVOICE", "DATE RECEIVED", "METHOD", "AMOUNT"], rows, emptyState("card", "Your first payment is a milestone.", "Record a customer payment to keep your cash flow and profit up to date.", "payment", "Record a payment"))}</section></div>`;
  }
  async function renderReminders() {
    const { reminders } = await api("reminders");
    const open = reminders.filter((item) => item.status !== "draft" && item.balance > 0);
    const overdue = open.filter((item) => item.status === "overdue");
    const rows = open.map((i) => `<tr data-searchable><td>${customerAvatar(i.customer_name)}<span class="table-customer"><strong>${esc(i.customer_name)}</strong><small>${esc(i.number)}</small></span></td><td>${dateLabel(i.due_date)}</td><td>${dateLabel(i.last_reminder)}</td><td class="amount-cell">${currency(i.balance)}</td><td>${badge(i.status)}</td><td><button class="button button-secondary button-small" data-remind="${i.id}">${icon("bell")} Record reminder</button></td></tr>`);
    return `<div class="page-wrap">${pageTitle("Payment reminders", "A gentle nudge can make all the difference.")}
      <div class="reminder-info">${icon("bell")} <span>Smart Invoice keeps a record of reminders you send. It doesn't send emails on your behalf—write to your customer using your usual email, then record it here.</span></div>
      <div class="metrics-grid metrics-compact">${metric("Open balances", open.length, "Invoices awaiting payment", "clock", "blue", "")}${metric("Past due", overdue.length, currency(overdue.reduce((sum, i) => sum + Number(i.balance), 0)) + " overdue", "warning", overdue.length ? "red" : "green", "")}${metric("Reminders recorded", reminders.reduce((sum, i) => sum + Number(i.reminder_count), 0), "For your own follow-up tracking", "bell", "cyan", "")}</div>
      <section class="card full-table-card">${sectionHeader("Follow-up list")}${table(["CUSTOMER", "DUE DATE", "LAST REMINDER", "BALANCE", "STATUS", "NEXT STEP"], rows, emptyState("check", "Nothing to chase today.", "Open invoices will show up here when a customer still has a balance.", null, ""))}</section></div>`;
  }
  async function renderFinancePage(page) {
    const [{ months, estimated_cash_balance: estimatedCash, low_cash_balance: lowCash }, { invoices }] = await Promise.all([api("analytics"), api("invoices")]);
    const collected = months.reduce((sum, m) => sum + Number(m.revenue), 0);
    const spent = months.reduce((sum, m) => sum + Number(m.expenses), 0);
    const profit = collected - spent;
    const receivable = invoices.filter((i) => i.status !== "draft").reduce((sum, i) => sum + Number(i.balance), 0);
    if (page === "revenue") {
      const { payments } = await api("payments");
      const rows = payments.slice(0, 12).map((p) => `<tr data-searchable><td>${customerAvatar(p.customer_name)}<span class="table-customer">${esc(p.customer_name)}<small>${esc(p.invoice_number)}</small></span></td><td>${dateLabel(p.paid_at)}</td><td>${esc(p.method)}</td><td class="amount-in amount-cell">+${currency(p.amount)}</td></tr>`);
      return `<div class="page-wrap">${pageTitle("Revenue", "Growth you can count on, grounded in payments received.", button("Create invoice", { create: "invoice", icon: "plus", className: "button-primary" }))}
        <div class="metrics-grid metrics-compact">${metric("Collected · 6 months", currency(collected), "Cash received from customers", "trend", "green", "")}${metric("Outstanding", currency(receivable), "On sent invoices", "clock", "cyan", "")}${metric("Best month", esc(months.reduce((best, m) => m.revenue > best.revenue ? m : best, months[0] || { month: "—", revenue: 0 }).month), "By collected revenue", "chart", "blue", "")}</div>
        <section class="card chart-card finance-chart">${sectionHeader("Revenue collected")}<p class="chart-caption">Cash actually received · last six months</p>${chartLegend([["Collected revenue", "#3978f6"]])}${chartSvg(months, "revenue", 280)}</section>
        <section class="card full-table-card">${sectionHeader("Recent payments", "payments")}${table(["CUSTOMER & INVOICE", "DATE", "METHOD", "COLLECTED"], rows, emptyState("trend", "Your revenue story starts here.", "Record payments to see your collected revenue grow.", "invoice", "Create an invoice"))}</section></div>`;
    }
    if (page === "profit-loss") {
      const rows = months.map((m) => `<tr data-searchable><td><strong>${esc(m.month)} ${m.year}</strong></td><td class="amount-in amount-cell">+${currency(m.revenue)}</td><td class="amount-out amount-cell">−${currency(m.expenses)}</td><td class="amount-cell"><strong class="${Number(m.net) < 0 ? "negative" : "positive"}">${Number(m.net) < 0 ? "−" : ""}${currency(Math.abs(Number(m.net)))}</strong></td><td>${Number(m.net) < 0 ? '<span class="status-badge badge-danger"><i></i>Loss</span>' : '<span class="status-badge badge-success"><i></i>Profit</span>'}</td></tr>`);
      return `<div class="page-wrap">${pageTitle("Profit & loss", "The bottom line—based on cash your business actually received.", `<span class="period-badge">${icon("calendar")} Last 6 months</span>`)}
        <div class="metrics-grid metrics-compact">${metric("Collected revenue", currency(collected), "Actual customer payments", "trend", "green", "")}${metric("Business expenses", currency(spent), "Recorded business costs", "receipt", "orange", "")}${metric(profit < 0 ? "Net loss" : "Net profit", currency(Math.abs(profit)), profit < 0 ? "Spending exceeded collections" : "Cash-basis operating profit", profit < 0 ? "warning" : "pie", profit < 0 ? "red" : "green", "")}${metric("Still to collect", currency(receivable), "Not counted until received", "clock", "cyan", "")}</div>
        <section class="card chart-card finance-chart">${sectionHeader("Your bottom line")}<p class="chart-caption">Revenue and expenses compared, month by month.</p>${chartLegend([["Collected revenue", "#3978f6"], ["Expenses", "#e7a14d"]])}${chartSvg(months, "both", 280)}</section>
        <section class="card full-table-card">${sectionHeader("Monthly statement")}${table(["PERIOD", "REVENUE", "EXPENSES", "NET PROFIT / LOSS", "RESULT"], rows, emptyState("pie", "Your statement is ready when you are.", "Record revenue and expenses to see your cash-basis profit and loss."))}</section>
        <div class="footnote">${icon("check")} Cash-basis view: revenue is recognized when paid; expenses on their recorded date. This is management information, not a tax filing.</div></div>`;
    }
    const tableRows = months.map((m) => `<tr data-searchable><td><strong>${esc(m.month)} ${m.year}</strong></td><td class="amount-in amount-cell">+${currency(m.revenue)}</td><td class="amount-out amount-cell">−${currency(m.expenses)}</td><td class="amount-cell"><strong class="${Number(m.net) < 0 ? "negative" : "positive"}">${Number(m.net) < 0 ? "−" : ""}${currency(Math.abs(Number(m.net)))}</strong></td><td><div class="mini-progress"><i class="${Number(m.net) < 0 ? "progress-negative" : ""}" style="--progress:${Math.min(100, Math.abs(Number(m.net)) / Math.max(1, collected, spent) * 100)}%"></i></div></td></tr>`);
    return `<div class="page-wrap">${pageTitle("Cash flow", "Follow the money in—and everything going back out.", button("Record payment", { create: "payment", icon: "plus", className: "button-primary" }))}
      <div class="metrics-grid metrics-compact metrics-five">${metric("Cash in · 6 months", currency(collected), "Payments received", "trend", "green", "")}${metric("Cash out · 6 months", currency(spent), "Recorded expenses", "receipt", "orange", "")}${metric(profit < 0 ? "Net outflow" : "Net inflow", currency(Math.abs(profit)), profit < 0 ? "More cash went out" : "More cash came in", "waves", profit < 0 ? "red" : "cyan", "")}${metric("Expected collections", currency(receivable), "Open invoice balances—not cash yet", "clock", "blue", "")}${metric("Estimated cash", estimatedCash === null ? "Not set" : currency(estimatedCash), estimatedCash === null ? "Add an opening balance in Settings" : lowCash ? "Below a month of recorded expenses" : "Opening balance plus transactions", "bank", lowCash ? "red" : "cyan", "")}</div>
      <section class="card chart-card finance-chart">${sectionHeader("Cash in vs. cash out")}<p class="chart-caption">Based on transaction dates—not invoice issue dates.</p>${chartLegend([["Cash in", "#3978f6"], ["Cash out", "#e7a14d"]])}${chartSvg(months, "both", 280)}</section>
      <section class="card full-table-card">${sectionHeader("Month-by-month cash flow")}${table(["PERIOD", "CASH IN", "CASH OUT", "NET CASH FLOW", "TREND"], tableRows, emptyState("waves", "A clearer cash flow starts with a first transaction.", "Record a customer payment or business expense to start tracking."))}</section></div>`;
  }
  async function renderAnalytics() {
    const [data, { invoices }, { customers }] = await Promise.all([api("analytics"), api("invoices"), api("customers")]);
    const months = data.months;
    const rev = months.reduce((s, m) => s + Number(m.revenue), 0);
    const spend = months.reduce((s, m) => s + Number(m.expenses), 0);
    const margin = rev ? ((rev - spend) / rev * 100) : 0;
    const revenueGrowth = growthHalf(months, "revenue");
    const customerLeaders = customers.filter((c) => Number(c.collected) > 0).sort((a, b) => b.collected - a.collected).slice(0, 4);
    const categories = await api("expenses");
    const categoryTotals = Object.values(categories.expenses.reduce((map, expense) => {
      map[expense.category] ||= { name: expense.category, total: 0 };
      map[expense.category].total += Number(expense.amount);
      return map;
    }, {})).sort((a, b) => b.total - a.total).slice(0, 4);
    return `<div class="page-wrap">${pageTitle("Analytics", "Turn the numbers into your next smart move.")}
      <div class="metrics-grid metrics-compact">${metric("Revenue growth", revenueGrowth === null ? "New" : `${revenueGrowth}%`, revenueGrowth === null ? "No prior revenue to compare" : "First half vs. second half", "trend", revenueGrowth !== null && revenueGrowth < 0 ? "red" : "green", "")}${metric("Profit margin", `${margin.toFixed(1)}%`, "Net cash flow as a share of revenue", "pie", margin < 0 ? "red" : "blue", "")}${metric("Average monthly spend", currency(spend / months.length), "Six-month average expense", "receipt", "orange", "")}${metric("Collection rate", `${collectionRate(invoices)}%`, "Collected against sent invoices", "check", "cyan", "")}</div>
      <div class="dashboard-grid">
        <section class="card chart-card">${sectionHeader("Financial performance")}<p class="chart-caption">Collections, costs and the cash left over.</p>${chartLegend([["Revenue", "#3978f6"], ["Expenses", "#e7a14d"]])}${chartSvg(months, "both", 260)}</section>
        <section class="card insight-side">${sectionHeader("A few things to notice")}<div class="signal-list">${margin < 0 ? signal("warning", "Costs are running ahead", "Recorded expenses exceed collected revenue across this period.", "signal-red") : signal("check", "You're in positive territory", "Collections are ahead of recorded expenses across this period.", "signal-green")}${invoices.filter(i => i.status === "overdue").length ? signal("bell", "There's money waiting", `${invoices.filter(i => i.status === "overdue").length} overdue invoice(s) need a follow-up.`, "signal-orange") : signal("check", "No overdue invoices", "Your current sent invoices aren't past due.", "signal-green")}${signal("sparkle", "Find your next opportunity", "Your AI business insights connect the dots across your finances.", "signal-blue", "ai-insights")}</div></section>
      </div>
      <div class="dashboard-grid lower-grid"><section class="card customers-card">${sectionHeader("Highest-revenue customers", "customers")}${customerLeaders.length ? `<div class="top-customer-list">${customerLeaders.map((c, i) => `<div class="top-customer-row">${customerAvatar(c.name)}<div class="top-customer-info"><strong>${esc(c.name)}</strong><small>${c.invoice_count} invoice${c.invoice_count === 1 ? "" : "s"}</small></div><div class="top-customer-total"><strong>${currency(c.collected)}</strong><span>collected</span></div><span class="customer-rank">0${i + 1}</span></div>`).join("")}</div>` : emptyState("users", "Your customer insights start here.", "Record payments to reveal your highest-revenue customers.")}</section>
      <section class="card customers-card">${sectionHeader("Where the money goes", "expenses")}${categoryTotals.length ? `<div class="category-list">${categoryTotals.map((c, i) => `<div class="category-row"><span class="category-dot dot-${i}"></span><span class="category-name">${esc(c.name)}</span><strong>${currency(c.total)}</strong></div>`).join("")}</div>` : emptyState("receipt", "Know where your money goes.", "Record expenses to understand your biggest costs.")}</section></div></div>`;
  }
  function growthHalf(months, key) {
    const mid = Math.floor(months.length / 2);
    const previous = months.slice(0, mid).reduce((sum, item) => sum + Number(item[key]), 0);
    const current = months.slice(mid).reduce((sum, item) => sum + Number(item[key]), 0);
    if (!previous) return current ? null : 0;
    return Math.round((current - previous) / previous * 100);
  }
  function collectionRate(invoices) {
    const sent = invoices.filter((i) => i.status !== "draft").reduce((sum, i) => sum + Number(i.amount), 0);
    const paid = invoices.filter((i) => i.status !== "draft").reduce((sum, i) => sum + Number(i.paid_amount), 0);
    return sent ? Math.round(paid / sent * 100) : 0;
  }
  function signal(iconName, title, description, tone, page) {
    return `<div class="signal-row"><span class="signal-icon ${tone}">${icon(iconName)}</span><span><strong>${esc(title)}</strong><small>${esc(description)}</small></span>${page ? `<button class="icon-button" data-page="${page}" aria-label="Open AI insights">${icon("chevron")}</button>` : ""}</div>`;
  }
  async function renderInsights() {
    const data = await api("insights");
    const insight = data.insights;
    const summary = insight.financial_summary;
    const revenueGrowth = summary.revenue_growth_percent;
    const expenseGrowth = summary.expense_growth_percent;
    const aiStatus = data.aiAvailable
      ? `<span class="connected-pill"><i></i> Gemini connected</span>`
      : `<span class="connection-note">${icon("bank")} Gemini is not connected · Add <code>GEMINI_API_KEY</code> to the server to enable AI analysis.</span>`;
    return `<div class="page-wrap insights-page">${pageTitle("AI business insights", "A second set of eyes on your real numbers.", `<button type="button" class="button button-primary" data-action="generate-ai" ${data.aiAvailable ? "" : "disabled title=\"Configure GEMINI_API_KEY on the backend first\""}>${icon("sparkle")} Ask Gemini</button>`)}
      <section class="ai-hero"><div class="ai-orb">${icon("sparkle")}</div><div class="ai-hero-text"><div class="eyebrow eyebrow-blue">SMARTER DECISIONS, GROUNDED IN YOUR DATA</div><h2>Your finances have a story.<br><span>Let's make sense of it.</span></h2><p>Every signal below comes from the actual invoices, payments and expenses in your workspace.</p></div><div class="ai-hero-note">${aiStatus}<small>Cash-basis · Last 6 months · ${esc(summary.currency)}</small></div></section>
      <div class="insight-intro">${icon("check")} <span>These financial signals are calculated directly from your records. Gemini can add written analysis when connected. Customer names and contact details are <strong>never sent to Gemini.</strong></span></div>
      <div class="metrics-grid metrics-compact metrics-five">${metric("Revenue growth", revenueGrowth === null ? "New" : `${revenueGrowth > 0 ? "+" : ""}${revenueGrowth}%`, revenueGrowth === null ? "No prior revenue to compare" : "Recent 3 months vs. prior 3 months", "trend", revenueGrowth !== null && revenueGrowth < 0 ? "red" : "green", "")}${metric("Expense growth", expenseGrowth === null ? "New" : `${expenseGrowth > 0 ? "+" : ""}${expenseGrowth}%`, expenseGrowth === null ? "No prior expenses to compare" : "Recent 3 months vs. prior 3 months", "receipt", expenseGrowth !== null && expenseGrowth > 0 ? "orange" : "green", "")}${metric("Overdue invoices", summary.overdue_invoice_count, `${currency(summary.overdue_invoice_balance)} still to collect`, "bell", summary.overdue_invoice_count ? "red" : "green", "")}${metric("Coming in · 30 days", currency(summary.upcoming_30_day_collections), "Open invoices due soon", "calendar", "cyan", "")}${metric("Estimated cash", summary.estimated_cash_balance === null ? "Not set" : currency(summary.estimated_cash_balance), summary.low_cash_balance ? "Below one month of recorded costs" : "Opening balance + recorded activity", "bank", summary.low_cash_balance ? "red" : "cyan", "")}</div>
      <div class="insights-grid">
        <section class="card signal-card">${sectionHeader("Business performance")}<p class="chart-caption">Your six-month financial pulse.</p><div class="ai-list">${insight.performance.map((s) => `<div class="ai-list-item">${icon("trend")}<span>${esc(s)}</span></div>`).join("")}</div></section>
        <section class="card signal-card">${sectionHeader("A few things to watch")}<p class="chart-caption">Potential headwinds, based on the numbers.</p><div class="ai-list">${insight.warnings.map((s) => `<div class="ai-list-item warning-item">${icon("warning")}<span>${esc(s)}</span></div>`).join("")}</div></section>
        <section class="card signal-card">${sectionHeader("Where opportunity lives")}<p class="chart-caption">Practical ideas to put the numbers to work.</p><div class="ai-list">${insight.opportunities.map((s) => `<div class="ai-list-item opportunity-item">${icon("sparkle")}<span>${esc(s)}</span></div>`).join("")}</div></section>
        <section class="card signal-card ai-response-card" id="gemini-response">${sectionHeader("A deeper look with Gemini")}<p class="chart-caption">AI-written analysis of anonymized financial aggregates only.</p><div class="gemini-placeholder"><div class="gemini-placeholder-icon">${icon("sparkle")}</div><strong>Curiosity is a good business tool.</strong><p>${data.aiAvailable ? "Ask Gemini to connect the dots in your financial trends and find specific opportunities." : "Add a Gemini API key to your server, then come back for a deeper analysis. Your private customer details stay on your device."}</p></div></section>
      </div><div class="footnote">${icon("warning")} Business insights are informational and not financial, tax, or legal advice. Check important decisions with a qualified professional.</div></div>`;
  }
  function renderReports() {
    return `<div class="page-wrap">${pageTitle("Reports", "Your numbers, ready to take wherever you need them.")}
      <section class="report-hero"><div class="report-hero-icon">${icon("report")}</div><div><div class="eyebrow eyebrow-blue">EXPORT YOUR BUSINESS DATA</div><h2>Bring your cash flow into focus.</h2><p>Download a CSV statement with real monthly collections, expenses and net cash flow for the last six months.</p><button class="button button-primary" data-action="download-report">${icon("download")} Download cash flow report</button></div><div class="report-illustration"><div class="report-paper"><span>MONTHLY REPORT</span><div class="report-scribble"></div><div class="report-scribble short"></div><div class="report-columns"><i></i><i></i><i></i><i></i><i></i><i></i></div><span>REVENUE · EXPENSES · NET</span></div></div></section>
      <section class="report-details"><div class="eyebrow">WHAT'S INCLUDED</div><div class="report-detail-grid"><div>${icon("trend")}<strong>Collected revenue</strong><span>Real payments received, by month.</span></div><div>${icon("receipt")}<strong>Business expenses</strong><span>Recorded expenses, by month.</span></div><div>${icon("pie")}<strong>Net cash flow</strong><span>Revenue minus expenses, by month.</span></div></div></section>
      <div class="report-footnote">${icon("check")} Exported directly from your workspace. Dates, amounts and currency reflect your actual financial records.</div></div>`;
  }
  async function renderSettings() {
    const { settings } = await api("settings");
    const user = state.user;
    return `<div class="page-wrap">${pageTitle("Settings", "Make your workspace feel like your business.")}
      <form class="settings-form" id="settings-form"><section class="card settings-card">${sectionHeader("Your business")}<p class="chart-caption">These details keep your workspace personal and your reports clear.</p>
        <label class="field-label">Business name<input class="field-input" name="business_name" required maxlength="120" value="${esc(settings.business_name)}" placeholder="Your business"></label>
        <label class="field-label">Report currency<select class="field-input" name="currency"><option value="USD" ${settings.currency === "USD" ? "selected" : ""}>USD — US Dollar</option><option value="CAD" ${settings.currency === "CAD" ? "selected" : ""}>CAD — Canadian Dollar</option><option value="GBP" ${settings.currency === "GBP" ? "selected" : ""}>GBP — British Pound</option><option value="EUR" ${settings.currency === "EUR" ? "selected" : ""}>EUR — Euro</option><option value="AUD" ${settings.currency === "AUD" ? "selected" : ""}>AUD — Australian Dollar</option><option value="INR" ${settings.currency === "INR" ? "selected" : ""}>INR — Indian Rupee</option><option value="NZD" ${settings.currency === "NZD" ? "selected" : ""}>NZD — New Zealand Dollar</option></select></label>
        <div class="settings-divider"></div>
        <div class="settings-field-intro"><strong>Cash balance estimate</strong><p>Enter a real opening bank balance and the date it applies. Smart Invoice then adds recorded payments and subtracts expenses from that date forward. This is an estimate, not a live bank connection.</p></div>
        <div class="form-two-col settings-opening-fields"><label class="field-label">Opening cash balance<input class="field-input" name="opening_cash_balance" type="number" step="0.01" min="-999999999.99" max="999999999.99" value="${settings.opening_cash_balance ?? ""}" placeholder="Optional"></label><label class="field-label">Balance as of<input class="field-input" name="opening_balance_date" type="date" max="${todayISO()}" value="${esc(settings.opening_balance_date)}" required></label></div>
        <div class="settings-form-end"><button class="button button-primary" type="submit">Save changes</button></div></section>
        <section class="card settings-card account-card">${sectionHeader("Account")}<div class="account-row"><span class="account-avatar">${esc(initials(user.name))}</span><span><strong>${esc(user.name)}</strong><small>Workspace owner</small></span></div><label class="field-label">Email address<input class="field-input" type="email" value="${esc(user.email)}" disabled></label></section>
        <section class="card settings-card privacy-card">${sectionHeader("Your data, your business")}<p>Financial records are private to your account. AI insights are calculated from your own workspace. When you explicitly request a Gemini analysis, only aggregated financial numbers are sent; customer names, email addresses, invoice descriptions and transaction-level records are not.</p></section>
      </form></div>`;
  }
  function filterRows() {
    const query = state.search;
    const filter = app.querySelector(".filter-chip.selected")?.dataset.filter || "all";
    app.querySelectorAll("tbody tr").forEach((row) => {
      const matchesSearch = !query || row.textContent.toLowerCase().includes(query);
      const matchesFilter = filter === "all" || row.querySelector(`.badge-${filter === "sent" ? "blue" : filter === "overdue" ? "danger" : filter === "paid" ? "success" : "neutral"}`);
      row.hidden = !(matchesSearch && matchesFilter);
    });
  }
  async function handlePageClick(event) {
    const button = event.target.closest("button");
    if (!button) return;
    if (button.dataset.create) return openModal(button.dataset.create);
    if (button.dataset.page) {
      event.preventDefault();
      state.page = button.dataset.page;
      state.search = "";
      app.querySelector(".sidebar")?.classList.remove("mobile-open");
      renderShell();
      return renderPage();
    }
    if (button.dataset.filter) {
      app.querySelectorAll(".filter-chip").forEach((chip) => chip.classList.toggle("selected", chip === button));
      filterRows();
    } else if (button.dataset.action === "refresh") {
      await renderPage();
    } else if (button.dataset.action === "print-invoice") {
      window.print();
    } else if (button.dataset.action === "download-report") {
      try {
        const response = await api("reports.csv");
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const anchor = document.createElement("a");
        anchor.href = url;
        anchor.download = "smart-invoice-cash-flow.csv";
        anchor.click();
        URL.revokeObjectURL(url);
        toast("Your cash flow report is ready.");
      } catch (err) { toast(err.message, "error"); }
    } else if (button.dataset.action === "generate-ai") {
      button.disabled = true;
      button.innerHTML = `${icon("sparkle")} Thinking through your numbers…`;
      try {
        const result = await api("insights/gemini", { method: "POST", body: "{}" });
        const target = document.querySelector("#gemini-response");
        target.innerHTML = `${sectionHeader("A deeper look with Gemini")}<p class="chart-caption">Based on anonymized financial aggregates · ${dateLabel(result.generated_at.slice(0, 10))}</p><div class="gemini-generated">${["performance", "warnings", "opportunities"].map((key) => `<div><span class="gemini-label">${key === "performance" ? "WHAT THE NUMBERS SAY" : key === "warnings" ? "KEEP AN EYE ON" : "ROOM TO GROW"}</span><ul>${result.analysis[key].map((text) => `<li>${esc(text)}</li>`).join("")}</ul></div>`).join("")}<p class="gemini-outlook">${esc(result.analysis.outlook)}</p></div>`;
        toast("Your private financial analysis is ready.");
      } catch (err) {
        toast(err.message, "error");
        button.disabled = false;
        button.innerHTML = `${icon("sparkle")} Ask Gemini`;
      }
    } else if (button.dataset.payInvoice) {
      const invoiceId = button.dataset.payInvoice;
      const { invoices } = await api("invoices");
      const invoice = invoices.find((item) => String(item.id) === invoiceId);
      if (invoice) openModal("payment", invoice);
    } else if (button.dataset.previewInvoice) {
      const { invoices } = await api("invoices");
      const invoice = invoices.find((item) => String(item.id) === button.dataset.previewInvoice);
      if (invoice) openModal("invoice-preview", invoice);
    } else if (button.dataset.sendInvoice) {
      try {
        await api(`invoices/${button.dataset.sendInvoice}`, {
          method: "PATCH", body: JSON.stringify({ status: "sent" }),
        });
        toast("Invoice marked as sent. Download or print it to share with your customer.");
        await renderPage();
      } catch (err) { toast(err.message, "error"); }
    } else if (button.classList.contains("reminder-one") || button.dataset.remind) {
      const invoiceId = button.dataset.invoice || button.dataset.remind;
      await recordReminder(invoiceId);
    } else if (button.dataset.deleteExpense) {
      if (window.confirm("Delete this expense? This also updates your cash flow and profit reports.")) {
        try { await api(`expenses/${button.dataset.deleteExpense}`, { method: "DELETE" }); toast("Expense deleted."); await renderPage(); }
        catch (err) { toast(err.message, "error"); }
      }
    } else if (button.dataset.deleteInvoice) {
      if (window.confirm("Delete this draft invoice? This cannot be undone.")) {
        try { await api(`invoices/${button.dataset.deleteInvoice}`, { method: "DELETE" }); toast("Draft invoice deleted."); await renderPage(); }
        catch (err) { toast(err.message, "error"); }
      }
    } else if (button.dataset.deleteCustomer) {
      if (window.confirm("Delete this customer? Customers with invoices cannot be deleted.")) {
        try { await api(`customers/${button.dataset.deleteCustomer}`, { method: "DELETE" }); toast("Customer deleted."); await renderPage(); }
        catch (err) { toast(err.message, "error"); }
      }
    } else if (button.dataset.editCustomer) {
      const { customers } = await api("customers");
      const customer = customers.find((item) => String(item.id) === button.dataset.editCustomer);
      if (customer) openModal("customer", customer);
    }
  }
  async function recordReminder(invoiceId) {
    try {
      await api("reminders", { method: "POST", body: JSON.stringify({ invoice_id: Number(invoiceId) }) });
      toast("Reminder recorded. Send a personal follow-up from your email.");
      await renderPage();
    } catch (err) { toast(err.message, "error"); }
  }
  function todayISO() {
    const now = new Date();
    const local = new Date(now.getTime() - now.getTimezoneOffset() * 60000);
    return local.toISOString().slice(0, 10);
  }
  function dateOffset(days) {
    const d = new Date();
    d.setDate(d.getDate() + days);
    return new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0, 10);
  }
  async function openModal(type, record = null) {
    state.modalCustomer = record;
    let body;
    let title;
    if (type === "customer") {
      title = record ? "A little customer update." : "Meet your new customer.";
      body = `<label class="field-label">Customer name<input class="field-input" name="name" value="${esc(record?.name || "")}" placeholder="Jordan Lee" required maxlength="120" autofocus></label>
        <label class="field-label">Company<input class="field-input" name="company" value="${esc(record?.company || "")}" placeholder="Acme Studio" maxlength="120"></label>
        <label class="field-label">Email address<input class="field-input" name="email" type="email" value="${esc(record?.email || "")}" placeholder="jordan@acme.com" maxlength="254"></label>
        <button class="button button-primary form-submit" type="submit">${record ? "Save customer" : "Add customer"}</button>`;
    } else if (type === "invoice") {
      const { customers } = await api("customers");
      if (!customers.length) {
        toast("Add a customer first so your invoice has somewhere to go.", "error");
        return openModal("customer");
      }
      title = "Let's get this invoice moving.";
      body = `<label class="field-label">Customer<select class="field-input" name="customer_id" required><option value="">Choose a customer…</option>${customers.map((c) => `<option value="${c.id}">${esc(c.name)}${c.company ? ` · ${esc(c.company)}` : ""}</option>`).join("")}</select></label>
        <div class="form-two-col"><label class="field-label">Amount<input class="field-input" name="amount" type="number" step="0.01" min="0.01" max="999999999.99" placeholder="2,500.00" required></label><label class="field-label">Service category<input class="field-input" name="service_category" value="General services" placeholder="Web design" maxlength="80" required></label></div>
        <label class="field-label">What's the work?<input class="field-input" name="description" placeholder="Website strategy & design" maxlength="500"></label>
        <div class="form-two-col"><label class="field-label">Issue date<input class="field-input" name="issue_date" type="date" value="${todayISO()}" required></label><label class="field-label">Due date<input class="field-input" name="due_date" type="date" value="${dateOffset(14)}" required></label></div>
        <label class="field-label">Status<select class="field-input" name="status"><option value="sent">Mark as sent</option><option value="draft">Save as draft</option></select><small class="form-help">This updates your records; no email is sent from the app.</small></label>
        <button class="button button-primary form-submit" type="submit">${icon("plus")} Create invoice</button>`;
    } else if (type === "invoice-preview") {
      title = `Invoice ${record.number}`;
      const settings = state.settings;
      body = `<article class="print-invoice"><header class="print-invoice-header"><div><span class="print-brand-mark">s.</span><strong>${esc(settings.business_name || "Your business")}</strong></div><div><span class="print-invoice-label">INVOICE</span><h2>${esc(record.number)}</h2><span class="print-status">${esc(record.status)}</span></div></header>
        <div class="print-invoice-parties"><div><span>BILL TO</span><strong>${esc(record.customer_name)}</strong><small>${esc(record.customer_company || "")}</small><small>${esc(record.customer_email || "")}</small></div><div><span>ISSUED</span><strong>${dateLabel(record.issue_date)}</strong><span>DUE DATE</span><strong>${dateLabel(record.due_date)}</strong></div></div>
        <div class="print-invoice-description"><span>DESCRIPTION</span><strong>${esc(record.description || record.service_category)}</strong><small>${esc(record.service_category)}</small></div>
        <div class="print-invoice-totals"><div><span>Invoice total</span><strong>${currency(record.amount)}</strong></div><div><span>Payments received</span><strong>−${currency(record.paid_amount)}</strong></div><div class="print-balance"><span>Balance due</span><strong>${currency(record.balance)}</strong></div></div>
        <p class="print-thanks">Thank you for your business.</p></article><button class="button button-primary form-submit" type="button" data-action="print-invoice">${icon("download")} Print or save as PDF</button>`;
    } else if (type === "expense") {
      title = "Make every cost count.";
      body = `<div class="form-two-col"><label class="field-label">Category<input class="field-input" name="category" list="expense-categories" placeholder="Software & subscriptions" required maxlength="80"><datalist id="expense-categories">${["Software & subscriptions", "Marketing", "Contractors", "Office & supplies", "Travel", "Professional services", "Equipment", "Other"].map((v) => `<option>${v}</option>`).join("")}</datalist></label><label class="field-label">Amount<input class="field-input" name="amount" type="number" step="0.01" min="0.01" max="999999999.99" placeholder="129.00" required></label></div>
        <label class="field-label">What was it for?<input class="field-input" name="description" placeholder="Monthly design tools" maxlength="500"></label>
        <div class="form-two-col"><label class="field-label">Service category<input class="field-input" name="service_category" placeholder="Optional" maxlength="80"></label><label class="field-label">Expense date<input class="field-input" name="expense_date" type="date" value="${todayISO()}" required></label></div>
        <button class="button button-primary form-submit" type="submit">${icon("plus")} Add expense</button>`;
    } else {
      title = "A great day to get paid.";
      const invoice = record;
      const { invoices } = invoice ? { invoices: [] } : await api("invoices");
      const options = invoice ? "" : invoices.filter((i) => i.status !== "draft" && Number(i.balance) > 0).map((i) => `<option value="${i.id}" data-balance="${i.balance}">${esc(i.number)} · ${esc(i.customer_name)} · ${currency(i.balance)} due</option>`).join("");
      if (!invoice && !options) {
        toast("You'll need a sent invoice with an outstanding balance first.", "error");
        state.page = "invoices";
        renderShell();
        return renderPage();
      }
      const invoiceOption = invoice ? `<input type="hidden" name="invoice_id" value="${invoice.id}"><div class="selected-invoice">${icon("file")}<span><strong>${esc(invoice.number)}</strong><small>${esc(invoice.customer_name)} · ${currency(invoice.balance)} remaining</small></span></div>` : `<label class="field-label">Invoice<select class="field-input" name="invoice_id" required><option value="">Choose an outstanding invoice…</option>${options}</select></label>`;
      body = `${invoiceOption}<div class="form-two-col"><label class="field-label">Amount received<input class="field-input" name="amount" type="number" step="0.01" min="0.01" max="999999999.99" ${invoice ? `value="${Number(invoice.balance).toFixed(2)}" max="${Number(invoice.balance).toFixed(2)}"` : ""} placeholder="1,250.00" required></label><label class="field-label">Date received<input class="field-input" name="paid_at" type="date" value="${todayISO()}" required></label></div>
        <label class="field-label">Payment method<select class="field-input" name="method">${["Bank transfer", "Credit card", "Cash", "PayPal", "Wise", "Other"].map((v) => `<option>${v}</option>`).join("")}</select></label>
        <button class="button button-primary form-submit" type="submit">${icon("check")} Record payment</button>`;
    }
    modal.innerHTML = `<div class="modal-panel"><div class="modal-header"><div><div class="eyebrow">${type === "expense" ? "RECORD A BUSINESS COST" : type === "payment" ? "RECORD A CUSTOMER PAYMENT" : type === "customer" ? "BUILD YOUR CUSTOMER LIST" : "TURN YOUR WORK INTO REVENUE"}</div><h2>${title}</h2></div><button type="button" class="icon-button modal-close" aria-label="Close dialog">${icon("close")}</button></div><p class="modal-copy">${type === "invoice" ? "Start with the details. You can record payments against it whenever they arrive." : type === "expense" ? "A complete picture includes the costs behind the work." : type === "payment" ? "Partial payments welcome. Your invoice balance will update automatically." : "Keep the people and businesses you work with close."}</p><form id="record-form" class="record-form">${body}<div class="modal-form-error" role="alert"></div></form></div>`;
    modal.showModal();
    modal.querySelector(".modal-close").addEventListener("click", () => modal.close());
    modal.addEventListener("click", (event) => {
      if (event.target === modal) modal.close();
    }, { once: true });
    const invoiceSelect = modal.querySelector('[name="invoice_id"]:not([type="hidden"])');
    const paymentAmount = modal.querySelector('[name="amount"]');
    invoiceSelect?.addEventListener("change", () => {
      const selected = invoiceSelect.selectedOptions[0];
      if (selected.dataset.balance) {
        paymentAmount.max = Number(selected.dataset.balance).toFixed(2);
        paymentAmount.placeholder = Number(selected.dataset.balance).toFixed(2);
      }
    });
    modal.querySelector("#record-form").addEventListener("submit", async (event) => {
      event.preventDefault();
      const form = new FormData(event.currentTarget);
      const data = Object.fromEntries(form.entries());
      const submit = event.currentTarget.querySelector('[type="submit"]');
      const error = event.currentTarget.querySelector(".modal-form-error");
      submit.disabled = true;
      error.textContent = "";
      const endpoint = type === "customer" ? (record ? `customers/${record.id}` : "customers")
        : type === "invoice" ? "invoices" : type === "expense" ? "expenses" : "payments";
      try {
        await api(endpoint, { method: type === "customer" && record ? "PATCH" : "POST", body: JSON.stringify(data) });
        modal.close();
        toast(type === "customer" ? (record ? "Customer updated." : "Customer added.")
          : type === "invoice" ? "Your invoice has been created."
            : type === "expense" ? "Expense added to your records." : "Payment recorded. Your numbers are up to date.");
        await renderPage();
      } catch (err) {
        error.textContent = err.message;
        submit.disabled = false;
      }
    });
    modal.querySelector("input,select")?.focus();
  }
  app.addEventListener("submit", async (event) => {
    if (event.target.id !== "settings-form") return;
    event.preventDefault();
    const button = event.target.querySelector('[type="submit"]');
    button.disabled = true;
    try {
      const data = await api("settings", { method: "PATCH", body: JSON.stringify(Object.fromEntries(new FormData(event.target).entries())) });
      state.settings = data.settings;
      toast("Your workspace settings are saved.");
      await renderPage();
    } catch (err) { toast(err.message, "error"); }
    finally { button.disabled = false; }
  });
  app.addEventListener("click", handlePageClick);
  document.addEventListener("keydown", (event) => {
    if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
      event.preventDefault();
      app.querySelector("#global-search")?.focus();
    }
    if (event.key === "Escape" && modal.open) modal.close();
  });
  refreshUser();
})();
