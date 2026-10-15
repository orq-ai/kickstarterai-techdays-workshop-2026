// ⌘K / Ctrl+K focuses the Material search box (Material binds /, s, f natively).
document.addEventListener("keydown", function (e) {
  if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
    var input = document.querySelector(".md-search__input");
    if (input) {
      e.preventDefault();
      var toggle = document.querySelector("[data-md-toggle=search]");
      if (toggle && !toggle.checked) toggle.checked = true; // open drawer on mobile
      input.focus();
    }
  }
});

// The button sits outside Termynal because animation and restart replace its contents.
document.addEventListener("click", async function (event) {
  const button = event.target.closest(".terminal-copy");
  if (!button) return;
  const session = button.closest(".terminal-session");
  const status = session.querySelector(".terminal-copy-status");
  try {
    await navigator.clipboard.writeText(session.dataset.terminalCommand);
    status.textContent = "Command copied";
    button.title = "Copied!";
    setTimeout(() => { button.title = "Copy command"; status.textContent = ""; }, 2000);
  } catch (error) {
    status.textContent = "Copy failed. Select and copy the command manually.";
    button.title = "Copy failed";
  }
});

// Termynal's built-in `.termy` scan starts every block during page load. The
// MkDocs hook renames those nodes so their animation can begin when visible.
(function () {
  var started = new WeakSet();
  var observing = new Set();
  var observer = null;

  function start(node) {
    if (started.has(node) || typeof Termynal === "undefined") return;
    started.add(node);
    new Termynal(node, { noInit: true, lineDelay: 500 }).init();
  }

  function scan() {
    if (typeof Termynal === "undefined") return;
    var nodes = document.querySelectorAll(".terminal-animation");
    if ("IntersectionObserver" in window) {
      if (!observer) {
        observer = new IntersectionObserver(function (entries) {
          entries.forEach(function (entry) {
            if (!entry.isIntersecting) return;
            observer.unobserve(entry.target);
            observing.delete(entry.target);
            start(entry.target);
          });
        }, { threshold: 0 });
      }

      observing.forEach(function (node) {
        if (!node.isConnected) {
          observer.unobserve(node);
          observing.delete(node);
        }
      });
      nodes.forEach(function (node) {
        if (started.has(node) || observing.has(node)) return;
        observing.add(node);
        observer.observe(node);
      });
      return;
    }

    nodes.forEach(start);
  }

  document.addEventListener("DOMContentLoaded", scan);
  if (typeof document$ !== "undefined") document$.subscribe(scan);
})();
