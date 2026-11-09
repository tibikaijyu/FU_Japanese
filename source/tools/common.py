"""Read Starbound's relaxed JSON without modifying strings or comments."""
from pathlib import Path
import json
import re
import pyjson5


def sanitize(text):
    text = text.lstrip('\ufeff').replace('\r\n', '\n').replace('\r', '')
    out = []
    quote = None
    comment = None
    escaped = False
    i = 0
    while i < len(text):
        c = text[i]
        nxt = text[i + 1] if i + 1 < len(text) else ''
        if comment == 'line':
            if c == '\n':
                comment = None
                out.append(c)
            i += 1
            continue
        if comment == 'block':
            if c == '*' and nxt == '/':
                comment = None
                out.append(' ')
                i += 2
            else:
                if c == '\n':
                    out.append(c)
                i += 1
            continue
        if quote is not None:
            if escaped:
                out.append(c)
                escaped = False
            elif c == '\\':
                out.append(c)
                escaped = True
            elif c == quote:
                out.append(c)
                quote = None
            elif c == '\n':
                out.append('\\n')
            elif c == '\t':
                out.append('\\t')
            else:
                out.append(c)
        elif c in ('"', "'"):
            quote = c
            out.append(c)
        elif c == '/' and nxt in ('/', '*'):
            comment = 'line' if nxt == '/' else 'block'
            out.append(' ')
            i += 1
        else:
            out.append(c)
        i += 1
    return ''.join(out)


def read_asset(path):
    text = Path(path).read_text(encoding='utf-8-sig')
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return pyjson5.loads(sanitize(text))


def ptr(parts):
    return ''.join('/' + str(p).replace('~', '~0').replace('/', '~1') for p in parts)


def unptr(value):
    return [p.replace('~1', '/').replace('~0', '~') for p in value.split('/')[1:]]


def walk(value, parts=(), parent=None):
    if isinstance(value, dict):
        for key, child in value.items():
            yield from walk(child, parts + (str(key),), value)
    elif isinstance(value, list):
        for i, child in enumerate(value):
            yield from walk(child, parts + (str(i),), value)
    elif isinstance(value, str):
        yield parts, value, parent


def dump(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')


# These three authored passages use angle brackets as prose punctuation, not
# as Starbound replacement tags. Keep all actual placeholder names protected.
_ANGLE_PROSE_PREFIXES = (
    'There are hundreds more pages, and the deeper into the tome you get,',
    'this book appears to span centuries. There are countless entries',
    'insert subject name here>',
)
_ANGLE_TOKEN = '<(?!' + '|'.join(re.escape(s) for s in _ANGLE_PROSE_PREFIXES) + r')[^<>\n]+>'
PROTECTED = re.compile(r'%%[^\n]*?%%|\[\((?:pause|data|scramble|function|playername|instant)\)[^\]\n]*\]|\^[^;\n]*;|' + _ANGLE_TOKEN + r'|\{[^{}\n]+\}|%(?:\d+\$)?[-+0#]*\d*(?:\.\d+)?[sdifqouxXeEgGc%]|[\ue000-\uf8ff]')


def tokens(value):
    return PROTECTED.findall(value)


def has_words(value):
    cleaned = PROTECTED.sub('', value)
    return bool(re.search(r'[A-Za-z]{2}', cleaned)) and not cleaned.startswith(('/', 'root/'))
