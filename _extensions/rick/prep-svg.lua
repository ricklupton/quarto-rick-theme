-- Render an Inkscape SVG into the slide, using its layers as reveal.js
-- fragments. Usage in a .qmd:
--
--     ```{.prep-svg src="diagram.svg"}
--     hide  background notes
--     frag 0 first stage
--     frag 1 second stage
--     ```

-- Resolve prep_svg.py relative to this filter, so it is found wherever the
-- extension was installed: _extensions/rick (copied by hand) or
-- _extensions/ricklupton/rick (installed via `quarto add`/`use template`).
local script_dir = PANDOC_SCRIPT_FILE:match("^(.*)[/\\][^/\\]*$") or "."
local prep_svg_py = script_dir .. "/prep_svg.py"

-- Paths routinely contain spaces (talk folders are named by date and title).
local function shellquote(s)
  return "'" .. tostring(s):gsub("'", "'\\''") .. "'"
end

local function prepSvg(src, commands)
  local temp_filename = os.tmpname()
  local cmd = string.format(
    "python3 -u %s %s %s",
    shellquote(prep_svg_py), shellquote(src), shellquote(temp_filename)
  )
  local p = assert(io.popen(cmd, "w"))
  p:write(commands)
  assert(p:close())

  local temp_f = assert(io.open(temp_filename, "rb"))
  local output = temp_f:read("*all")
  temp_f:close()
  os.remove(temp_filename)
  return output
end

function CodeBlock(el)
  if el.attr.classes:find("prep-svg") then
    local src = el.attr.attributes["src"]
    quarto.log.output("prep-svg: " .. src)
    return pandoc.RawBlock("html", prepSvg(src, el.text))
  end
end
