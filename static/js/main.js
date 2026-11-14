(function () {
  "use strict";
  var root = document.documentElement;

  function store(key, val) { try { localStorage.setItem(key, val); } catch (e) {} }
  function read(key) { try { return localStorage.getItem(key); } catch (e) { return null; } }
  function cookie(name) {
    var m = document.cookie.match("(^|;)\\s*" + name + "\\s*=\\s*([^;]+)");
    return m ? decodeURIComponent(m[2]) : "";
  }

  // Light / dark theme (initial value is applied in <head> to avoid flashing)
  var themeBtn = document.getElementById("theme-toggle");
  function syncThemeIcon() {
    if (!themeBtn) return;
    var dark = root.getAttribute("data-bs-theme") === "dark";
    themeBtn.querySelector("i").className = "bi " + (dark ? "bi-sun" : "bi-moon-stars");
    themeBtn.setAttribute("aria-label", dark ? "Switch to light theme" : "Switch to dark theme");
  }
  if (themeBtn) {
    themeBtn.addEventListener("click", function () {
      var next = root.getAttribute("data-bs-theme") === "dark" ? "light" : "dark";
      root.setAttribute("data-bs-theme", next);
      store("hive-theme", next);
      syncThemeIcon();
    });
    syncThemeIcon();
  }

  // Card vs. Compact view
  var feed = document.getElementById("feed");
  var viewBtns = document.querySelectorAll("[data-view]");
  function setView(view) {
    if (!feed) return;
    feed.classList.toggle("compact", view === "compact");
    viewBtns.forEach(function (b) { b.classList.toggle("active", b.dataset.view === view); });
    store("hive-view", view);
  }
  if (feed) {
    setView(read("hive-view") === "compact" ? "compact" : "card");
    viewBtns.forEach(function (b) { b.addEventListener("click", function () { setView(b.dataset.view); }); });
  }

  // Optimistic upvote / downvote: update UI instantly, then sync; revert on failure
  document.querySelectorAll(".vote-btn").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var col = btn.closest(".vote-col");
      var scoreEl = col.querySelector(".vote-score");
      var prevVote = parseInt(col.dataset.vote, 10) || 0;
      var prevScore = parseInt(scoreEl.textContent, 10) || 0;
      var value = parseInt(btn.dataset.value, 10);
      var nextVote = prevVote === value ? 0 : value;

      function paint(vote, score) {
        col.dataset.vote = vote;
        scoreEl.textContent = score;
        col.querySelector('[data-value="1"]').classList.toggle("active-up", vote === 1);
        col.querySelector('[data-value="-1"]').classList.toggle("active-down", vote === -1);
      }
      paint(nextVote, prevScore + (nextVote - prevVote));

      fetch(col.dataset.url, {
        method: "POST",
        headers: { "X-CSRFToken": cookie("csrftoken"), "Content-Type": "application/x-www-form-urlencoded" },
        body: "value=" + value,
        credentials: "same-origin"
      }).then(function (r) {
        if (!r.ok) throw new Error("vote failed");
        return r.json();
      }).then(function (d) { paint(d.user_vote, d.score); })
        .catch(function () { paint(prevVote, prevScore); });
    });
  });

  // Reopen the right comment section when linked via #post-N
  if (location.hash && location.hash.indexOf("#post-") === 0) {
    var el = document.querySelector(location.hash + " .collapse");
    if (el && window.bootstrap) bootstrap.Collapse.getOrCreateInstance(el, { toggle: false }).show();
  }
})();
