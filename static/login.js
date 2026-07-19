document.addEventListener("DOMContentLoaded", () => {
  // Redirect if already logged in
  const existing = localStorage.getItem("gt_token");
  if (existing && existing !== "null" && existing !== "undefined") {
    window.location.replace("/dashboard");
    return;
  }

  const form      = document.getElementById("loginForm");
  const errorEl   = document.getElementById("errorMsg");
  const loginBtn  = document.getElementById("loginBtn");
  const togglePw  = document.getElementById("togglePw");
  const pwInput   = document.getElementById("password");

  // Toggle password visibility
  togglePw.addEventListener("click", () => {
    const isText = pwInput.type === "text";
    pwInput.type = isText ? "password" : "text";
    togglePw.innerHTML = isText
      ? `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>`
      : `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>`;
  });

  function showError(msg) {
    errorEl.textContent = msg;
    errorEl.classList.add("visible");
  }

  function hideError() {
    errorEl.classList.remove("visible");
  }

  function setLoading(on) {
    loginBtn.disabled = on;
    loginBtn.classList.toggle("loading", on);
  }

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    hideError();

    const username = document.getElementById("username").value.trim();
    const password = document.getElementById("password").value;

    if (!username || !password) {
      showError("Please enter your username and password.");
      return;
    }

    setLoading(true);

    try {
      const res = await fetch("/api/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });

      const data = await res.json();

      if (res.ok && data.access_token) {
        localStorage.setItem("gt_token", data.access_token);
        window.location.replace("/dashboard");
      } else {
        showError(data.msg || "Login failed. Please try again.");
        setLoading(false);
      }
    } catch (err) {
      showError("Network error. Is the server running?");
      setLoading(false);
    }
  });
});
