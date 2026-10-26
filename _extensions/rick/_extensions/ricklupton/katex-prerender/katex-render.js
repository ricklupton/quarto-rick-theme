// Typeset maths with the KaTeX vendored in vendor/katex/ beside this file,
// for katex.lua.
//
// Reads a JSON list of {tex, display} on stdin and writes the matching list
// of HTML strings to stdout.  Run with Quarto's own Deno (`quarto run`), so
// rendering needs nothing that Quarto doesn't already bring.
//
// Every equation goes through one katex.renderToString() call in this one
// process, with one `macros` object shared between them, as Quarto's
// in-browser loader does: a \gdef in one equation still reaches the later
// ones.  `trust` enables KaTeX's HTML extension, so that, for example,
// \htmlClass{fragment}{...} can mark part of an equation as a reveal.js
// fragment; KaTeX turns it off by default as a defence against untrusted
// input, but the TeX here is the document's own.
//
// A TeX error stops the render, naming every bad equation, where KaTeX in the
// browser would have shown it in red on the page for a reader to find.

// katex.min.js is a UMD bundle: loaded as a module, it attaches itself to
// `self`.
globalThis.self ??= globalThis;
await import(new URL("vendor/katex/katex.min.js", import.meta.url).href);
const katex = self.katex;

const maths = JSON.parse(await new Response(Deno.stdin.readable).text());
const macros = {};
const errors = [];

const html = maths.map(({ tex, display }) => {
  try {
    return katex.renderToString(tex, {
      displayMode: display,
      throwOnError: true,
      macros,
      trust: true,
      // and don't warn about it, on every use, as not being LaTeX
      strict: (code) => (code === "htmlExtension" ? "ignore" : "warn"),
    });
  } catch (e) {
    errors.push(`  ${e.message}\n    in: ${tex.trim()}`);
    return "";
  }
});

if (errors.length) {
  console.error(`katex: ${errors.length} equation(s) failed to typeset:\n` +
                errors.join("\n"));
  Deno.exit(1);
}
console.log(JSON.stringify(html));
