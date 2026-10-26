# quarto-rick-theme

Reveal.js presentation theme.  Provides the `rick-revealjs` Quarto format.

## Starting a new talk

```sh
mkdir "2026-11-01 Some Conference" && cd "2026-11-01 Some Conference"
quarto use template ricklupton/quarto-rick-theme
```

This installs the extension, writes a `_quarto.yml` (with `output-dir: public`),
and creates a starter file named after the folder.  The slides render to `public/index.html`.

## Adding to an existing project

```sh
quarto add ricklupton/quarto-rick-theme     # then set `format: rick-revealjs`
quarto update ricklupton/quarto-rick-theme  # pull in later theme changes
```

Note that `quarto use template` needs a more-or-less empty directory; use
`quarto add` for a deck that already exists.

## Using SVG layers as fragments

Export an SVG with named layers, then:

````markdown
```{.prep-svg src="diagram.svg"}
hide  scaffolding
frag 0 first stage
frag 1 second stage
```
````

`show`/`hide` set a layer's initial visibility; `frag [n] label` reveals a layer
as a fragment, optionally at fragment index `n`.

## Styling helpers

- `.compact` on a slide tightens list spacing.

## Maths

`rick-revealjs` typesets maths with KaTeX when the deck is rendered, not in
the browser, using the embedded
[katex-prerender](https://github.com/ricklupton/quarto-katex-prerender)
extension. With `embed-resources: true`, a deck is then one file that shows
its maths offline, from a USB stick or a VLE, with nothing beside it. KaTeX's
HTML extension is on, so `\htmlClass{fragment}{...}` makes part of an
equation a reveal.js fragment, and a TeX error stops the render. See that
extension's README for the details, and to use it in documents and books.

Needs Quarto 1.9.18 or later. To update the embedded copy, from this
repository:

```sh
quarto add ricklupton/quarto-katex-prerender --embed rick
```
