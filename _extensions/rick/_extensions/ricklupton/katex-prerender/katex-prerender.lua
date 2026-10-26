-- Typeset the maths when the document is rendered, rather than in the
-- reader's browser.
--
-- Quarto's own `html-math-method: katex` leaves the TeX in the page and adds a
-- script that loads KaTeX and typesets it when the page opens.  That script
-- builds its <link> and <script> tags at page load, so `embed-resources`
-- cannot inline them: a self-contained file still needs KaTeX beside it, or
-- a CDN.  Here every equation is turned into KaTeX's HTML once, by
-- katex-render.js, and the page needs only KaTeX's stylesheet and fonts --
-- ordinary files that `embed-resources` does inline.  The page then carries
-- no KaTeX JavaScript, and its maths is there before any script runs: no
-- flash of raw TeX.
--
-- HTML formats only (revealjs included); everything else keeps the TeX.  It
-- runs `at: post-render` (see _extension.yml), after Quarto's own filters,
-- so it sees equations as cross-referencing leaves them.
--
-- KaTeX itself is vendored in vendor/katex/ beside this file (see
-- vendor-katex.sh in the extension's repository), so rendering needs no
-- network.  Not katex/: an extension that embeds this one and sets
-- `html-math-method: katex` in its _extension.yml would have Quarto read
-- that as a path to the directory.

if not quarto.doc.is_format("html") then
  return {}
end

local function add_stylesheet()
  -- katex.min.css refers to its fonts as fonts/KaTeX_*.woff2, so they keep
  -- that path beside it.
  local fonts = {}
  for _, f in ipairs(pandoc.system.list_directory(quarto.utils.resolve_path("vendor/katex/fonts"))) do
    table.insert(fonts, { name = "fonts/" .. f, path = quarto.utils.resolve_path("vendor/katex/fonts/" .. f) })
  end
  quarto.doc.add_html_dependency({
    name = "katex",
    stylesheets = { quarto.utils.resolve_path("vendor/katex/katex.min.css") },
    resources = fonts,
  })
end

-- Two passes: the first collects every equation and typesets them all in
-- one run of the script (it is `quarto run`, so about a second each), the
-- second puts each one's HTML in its place, in the same order.  (One Pandoc
-- function that re-walks the document and returns it has no effect at
-- post-render: the output keeps the TeX.)
local maths = {}
local html = {}

local collect = {
  Math = function(m)
    table.insert(maths, { tex = m.text, display = m.mathtype == "DisplayMath" })
  end,
  Pandoc = function()
    if #maths > 0 then
      html = quarto.json.decode(pandoc.pipe(
        quarto.config.cli_path(),
        { "run", quarto.utils.resolve_path("katex-render.js") },
        quarto.json.encode(maths)
      ))
      add_stylesheet()
    end
  end,
}

-- Kept in the span pandoc would have written, so the markup around each
-- equation is as before.
local i = 0
local replace = {
  Math = function(m)
    i = i + 1
    local class = maths[i].display and "math display" or "math inline"
    return pandoc.RawInline("html",
      '<span class="' .. class .. '">' .. html[i] .. "</span>")
  end,
}

return { collect, replace }
