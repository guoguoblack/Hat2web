// 見やすさ設定と読み上げ
(function () {
  var root = document.documentElement;
  var KEY = "hat2-prefs";
  var defaults = { size: "m", spacing: "normal", theme: "light", easy: "off" };
  if (window.matchMedia && matchMedia("(prefers-color-scheme: dark)").matches) defaults.theme = "dark";

  function load() {
    try { return JSON.parse(localStorage.getItem(KEY) || "{}"); } catch (e) { return {}; }
  }
  var prefs = Object.assign({}, defaults, load());

  function apply() {
    Object.keys(prefs).forEach(function (k) { root.dataset[k] = prefs[k]; });
    document.querySelectorAll("[data-pref]").forEach(function (b) {
      b.setAttribute("aria-pressed", String(prefs[b.dataset.pref] === b.dataset.value));
    });
  }

  document.querySelectorAll("[data-pref]").forEach(function (b) {
    b.addEventListener("click", function () {
      prefs[b.dataset.pref] = b.dataset.value;
      try { localStorage.setItem(KEY, JSON.stringify(prefs)); } catch (e) {}
      apply();
    });
  });

  var toggle = document.querySelector(".prefs-btn");
  var panel = document.getElementById("prefs");
  toggle.addEventListener("click", function () {
    var open = panel.hidden;
    panel.hidden = !open;
    toggle.setAttribute("aria-expanded", String(open));
  });
  apply();

  var speak = document.getElementById("speak");
  if (speak && "speechSynthesis" in window) {
    speak.hidden = false;
    speak.addEventListener("click", function () {
      if (speechSynthesis.speaking) {
        speechSynthesis.cancel();
        speak.textContent = "🔊 読み上げる";
        return;
      }
      var title = document.querySelector(".article h1").textContent;
      var body = document.getElementById("read-target").innerText;
      var u = new SpeechSynthesisUtterance(title + "。" + body);
      u.lang = "ja-JP";
      u.rate = 0.95;
      u.onend = function () { speak.textContent = "🔊 読み上げる"; };
      speechSynthesis.speak(u);
      speak.textContent = "⏹ 止める";
    });
  }
})();
