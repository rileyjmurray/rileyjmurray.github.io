// Renders the note draft in the URL fragment (base64 or base64url of UTF-8
// Markdown) the way the site will: kramdown-style $$...$$ math becomes
// \(...\) inline and \[...\] on its own line, and MathJax typesets it.
(function () {
  const target = document.getElementById("note-preview");
  const timeEl = document.getElementById("note-preview-time");

  function decodeFragment(hash) {
    let s = decodeURIComponent(hash.replace(/^#/, "")).replace(/\s+/g, "").replace(/-/g, "+").replace(/_/g, "/");
    while (s.length % 4) s += "=";
    const bytes = Uint8Array.from(atob(s), (c) => c.charCodeAt(0));
    return new TextDecoder().decode(bytes);
  }

  function escapeHtml(s) {
    return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  // Match kramdown's handling of $$...$$ so the preview agrees with the build.
  const kramdownMath = {
    extensions: [
      {
        name: "displayMath",
        level: "block",
        start: (src) => src.match(/^\$\$/m)?.index,
        tokenizer(src) {
          const m = /^\$\$([\s\S]+?)\$\$[ \t]*(?:\n|$)/.exec(src);
          if (m) return { type: "displayMath", raw: m[0], tex: m[1] };
        },
        renderer: (token) => `<p>\\[${escapeHtml(token.tex)}\\]</p>\n`,
      },
      {
        name: "inlineMath",
        level: "inline",
        start: (src) => src.indexOf("$$"),
        tokenizer(src) {
          const m = /^\$\$([\s\S]+?)\$\$/.exec(src);
          if (m) return { type: "inlineMath", raw: m[0], tex: m[1] };
        },
        renderer: (token) => `\\(${escapeHtml(token.tex)}\\)`,
      },
    ],
  };
  marked.use({ gfm: true, breaks: false }, kramdownMath);

  function typeset() {
    if (window.MathJax && MathJax.typesetPromise) {
      MathJax.typesetClear([target]);
      MathJax.typesetPromise([target]);
    }
  }

  function render() {
    if (!location.hash || location.hash === "#") return;
    try {
      const markdown = decodeFragment(location.hash).replace(/^---\n[\s\S]*?\n---\n/, "");
      target.innerHTML = marked.parse(markdown);
    } catch (err) {
      target.innerHTML = `<p class="note-empty">Could not decode this draft: ${escapeHtml(String(err))}</p>`;
      return;
    }
    const now = new Date();
    timeEl.textContent =
      now.toLocaleDateString("en-US", { month: "long", day: "numeric", year: "numeric" }) +
      " · " +
      now.toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit" });
    typeset();
  }

  render();
  window.addEventListener("hashchange", render);
  // MathJax loads deferred; typeset again once it is ready.
  window.addEventListener("load", typeset);
})();
