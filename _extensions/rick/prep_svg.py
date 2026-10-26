from collections import defaultdict
from xml.dom.minidom import parse
from uuid import uuid4
import sys
import re

# XML namespaces
INKSCAPE = 'http://www.inkscape.org/namespaces/inkscape'
XLINK = 'http://www.w3.org/1999/xlink'

# https://github.com/iconfu/svg-inject/blob/master/src/svg-inject.js This
# function appends a suffix to IDs of referenced elements in the <defs> in
# order to to avoid ID collision between multiple injected SVGs. The suffix has
# the form "--inject-X", where X is a running number which is incremented with
# each injection. References to the IDs are adjusted accordingly. We assume tha
# all IDs within the injected SVG are unique, therefore the same suffix can be
# used for all IDs of one injected SVG. If the onlyReferenced argument is set
# to true, only those IDs will be made unique that are referenced from within
# the SVG.
ID_SUFFIX = '-injected-'

# def elements_with_id(node):
#     if node.getAttribute('id'):
#         yield node
#     for n in node.childNodes:
#         yield from elements_with_id(n)

IRI_attrs = [
    'clip-path',
    'color-profile',
    'cursor',
    'filter',
    'fill',
    'stroke',
    'marker',
    'marker-end',
    'marker-mid',
    'marker-start',
    'mask',
    'style',
]

def remove_root_dimensions(root):
    svgElem = root.getElementsByTagName('svg')
    for elem in svgElem:
        elem.removeAttribute('width')
        elem.removeAttribute('height')

def make_ids_unique(svgElem):
    idSuffix = ID_SUFFIX + str(uuid4())

    # Regular expression for functional notations of an IRI references. This
    # will find occurences in the form url(#anyId) or url("#anyId") (for
    # Internet Explorer) and capture the referenced ID
    funcIriRegex = re.compile(r'url\("?#([a-zA-Z][\w:.-]*)"?\)')

    def replacement_func(match):
        return 'url(#' + match[1] + idSuffix + ')'

    for elem in svgElem.getElementsByTagName('*'):
        # Change the ID
        orig_id = elem.getAttribute('id')
        if orig_id:
            elem.setAttribute('id', orig_id + idSuffix)

        # Look for properties that need updating
        for attr in IRI_attrs:
            orig = elem.getAttribute(attr)
            if orig:
                elem.setAttribute(attr, funcIriRegex.sub(replacement_func, orig))

        # Also update IDs in xlink:ref and href attributes, as long as they
        # start with #
        orig = elem.getAttributeNS(XLINK, 'href')
        if orig and orig.startswith('#'):
            elem.setAttributeNS(XLINK, 'href', orig + idSuffix)

        if elem.tagName == 'image':
            # This seems required for images?
            href = elem.getAttributeNS(XLINK, 'href')
            if not href.startswith("data:"):
                import os, os.path, pathlib
                orig_href = pathlib.Path(sys.argv[1]).resolve().parent / href
                rel_href = os.path.relpath(orig_href) #.relative_to(os.getcwd())
                # raise ValueError('orig: %s; rel: %s' % (orig_href, rel_href))
                elem.setAttributeNS(XLINK, 'href', str(rel_href))

        # TODO Also update in <style> tags' textContent

dom = parse(sys.argv[1])

# A label selects every group with that Inkscape label or id.  Several groups
# can share one: matplotlib, for example, writes each artist with a given gid
# as its own <g id="...">, interleaved with other artists according to their
# z-order.  Rather than moving them together, which would change what's drawn
# on top of what, each command applies to all of them where they are.
groups = dom.getElementsByTagName('g')
layers = defaultdict(list)
for g in groups:
    if g.getAttributeNS(INKSCAPE, 'groupmode') == 'layer' or g.getAttribute('id'):
        layers[g.getAttributeNS(INKSCAPE, 'label') or g.getAttribute('id')].append(g)

def find_layers(label):
    if label not in layers:
        raise ValueError('No layer or group with label or id "%s"' % label)
    return layers[label]

def set_fragment(label):
    match = re.match(r'^(\d*)\s*(.*)$', label)
    assert match
    index = match[1]
    targets = find_layers(match[2])
    if len(targets) > 1 and index == '':
        # reveal.js would show each group on a separate click, and only an
        # index keeps them together -- but adding one here would move this
        # fragment ahead of every unindexed fragment on the slide.
        raise ValueError(
            '"%s" matches %d groups: give it a fragment index (e.g. "frag 1 %s") '
            'so that they appear together' % (match[2], len(targets), match[2]))
    for layer in targets:
        if index != '':
            layer.setAttribute('data-fragment-index', index)
        layer.setAttribute('class', layer.getAttribute('class') + ' fragment')
    set_visible(match[2], True)

def set_visible(label, visible):
    for layer in find_layers(label):
        style = layer.getAttribute('style')
        if not style:
            style = "display:none"
        if visible:
            style = re.sub(r'display:\s*none', 'display:inline', style)
        else:
            style = re.sub(r'display:\s*inline', 'display:none', style)
        layer.setAttribute('style', style)

def make_duplicate_ids_distinct(svgElem):
    """Number the second and later uses of an id: "a", "a-2", "a-3", ...

    Only for ids that nothing refers to, such as matplotlib's per-artist groups.
    """
    seen = defaultdict(int)
    for elem in svgElem.getElementsByTagName('*'):
        orig_id = elem.getAttribute('id')
        if orig_id:
            seen[orig_id] += 1
            if seen[orig_id] > 1:
                elem.setAttribute('id', '%s-%d' % (orig_id, seen[orig_id]))


for line in sys.stdin:
    parts = line.strip().split(maxsplit=1)
    if len(parts) != 2:
        raise ValueError('Expected line: {command} {label}, but got "%s"' % line)

    cmd, label = parts
    if cmd == 'frag':
        set_fragment(label)
    elif cmd == 'show':
        set_visible(label, True)
    elif cmd == 'hide':
        set_visible(label, False)
    else:
        raise ValueError('Unknown command: {}'.format(cmd))

make_duplicate_ids_distinct(dom)
make_ids_unique(dom)
remove_root_dimensions(dom)

if len(sys.argv) > 2:
    f_out = open(sys.argv[2], "wt")
else:
    f_out = sys.stdout

dom.writexml(f_out)
f_out.write("\n")
