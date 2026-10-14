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
