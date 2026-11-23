"""Validate and finish one CountyUkiyoe static release using the standard library."""

from hashlib import sha256
from html import escape
from html.parser import HTMLParser
from pathlib import Path
import re
from urllib.parse import unquote, urljoin, urlsplit

PAGES = "https://yuxuan6426.github.io/"
WIKI = {
    "CountyUkiyoe": "https://xian.yuxuan.wiki/",
    "CountyUkiyoe-Quiz": "https://quiz.yuxuan.wiki/",
    "CountyUkiyoe-Play": "https://card.yuxuan.wiki/",
}
WIKI_HOSTS = {urlsplit(url).hostname for url in WIKI.values()}
ASSET_TYPES = {".css", ".js", ".mjs"}
VERSIONED_REFERENCE = re.compile(r"""(?P<quote>['"])(?P<ref>(?:\.\.?/|assets/)*[\w.-]+\.(?:css|m?js))(?:\?v=[\w-]+)?(?P=quote)""")


def check_vendored(root, expected):
    for name, digest in expected.items():
        if sha256((root / name).read_bytes()).hexdigest() != digest:
            raise ValueError(f"Review the provenance before replacing {name}")


def prepare_output(root, output):
    output = output.resolve()
    if output.is_relative_to(root.resolve()):
        relative = output.relative_to(root.resolve())
        if not relative.parts or relative.parts[0] not in {"dist", "artifacts"}:
            raise ValueError("Build under dist/ or artifacts/, or choose an empty external directory")
    if output.exists() and (not output.is_dir() or any(output.iterdir())):
        raise ValueError(f"Choose an empty output directory: {output}")
    output.mkdir(parents=True, exist_ok=True)
    return output


def policy(wiki):
    images = "'self' data: blob:" + (" https://xian.yuxuan.wiki" if wiki else "")
    return (
        "default-src 'self'; script-src 'self'; style-src 'self'; "
        f"img-src {images}; connect-src 'self'; "
        "object-src 'none'; base-uri 'none'; form-action 'self'"
    )


class LocalReferences(HTMLParser):
    def __init__(self):
        super().__init__()
        self.references = []
        self.policies = 0

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag == "script" and not attributes.get("src") and attributes.get("type") != "application/json":
            raise ValueError("Release HTML must load executable scripts from files")
        if any(key.startswith("on") for key in attributes):
            raise ValueError("Release HTML must use script event listeners")
        if tag == "meta" and attributes.get("http-equiv", "").lower() == "content-security-policy":
            self.policies += 1
        for key in ("href", "src", "action", "data-backup"):
            if attributes.get(key):
                self.references.append(attributes[key])
        if tag == "meta" and attributes.get("property", "") in {"og:url", "og:image"}:
            self.references.append(attributes.get("content", ""))


def check_html(file, content, output, site_url, wiki):
    parser = LocalReferences()
    parser.feed(content)
    if parser.policies != 1:
        raise ValueError(f"Expected one CSP policy in {file}")
    path = file.relative_to(output).as_posix()
    page = urljoin(site_url, path.removesuffix("index.html") if path.endswith("index.html") else path)
    current = urlsplit(site_url)
    for value in parser.references:
        if not value or value.startswith(("#", "data:", "mailto:")):
            continue
        target = urlsplit(urljoin(page, value))
        if target.scheme not in {"https", "http"}:
            raise ValueError(f"Unsupported URL scheme in {path}")
        if (wiki and target.hostname == urlsplit(PAGES).hostname) or (
                not wiki and target.hostname in WIKI_HOSTS):
            raise ValueError(f"Mixed deployment environments in {path}: {value}")
        if target.netloc != current.netloc or not target.path.startswith(current.path):
            continue
        relative = unquote(target.path[len(current.path):])
        destination = (output / relative).resolve()
        if not destination.is_relative_to(output):
            raise ValueError(f"URL leaves the release in {path}: {value}")
        if destination.is_dir():
            destination /= "index.html"
        if not destination.is_file():
            raise ValueError(f"Missing local URL in {path}: {value}")


def finish_release(output, expected, site_url, *, wiki):
    expected = set(expected)
    actual = {p.relative_to(output).as_posix() for p in output.rglob("*") if p.is_file()}
    if actual != expected:
        raise ValueError(f"Release files differ from the allowlist: missing={sorted(expected - actual)[:8]} "
                         f"unexpected={sorted(actual - expected)[:8]}")
    hashes = sha256()
    assets = [output / path for path in sorted(actual) if Path(path).suffix in ASSET_TYPES]
    for asset in assets:
        hashes.update(asset.relative_to(output).as_posix().encode() + b"\0" + asset.read_bytes() + b"\0")
    version = hashes.hexdigest()[:16]

    def version_references(text, file):
        def replace(match):
            ref, quote = match["ref"], match["quote"]
            candidate = file.parent / ref
            if not candidate.is_file():
                return match[0]
            return f"{quote}{ref}?v={version}{quote}"
        return VERSIONED_REFERENCE.sub(replace, text)

    for asset in assets:
        if asset.suffix == ".mjs":
            source = asset.read_text(encoding="utf-8")
            updated = version_references(source, asset)
            if updated != source:
                asset.write_text(updated, encoding="utf-8", newline="\n")
    content_policy = f'<meta http-equiv="Content-Security-Policy" content="{escape(policy(wiki))}">'
    for file in output.rglob("*.html"):
        source = file.read_text(encoding="utf-8")
        if "<head>" in source:
            html = source.replace("<head>", "<head>\n" + content_policy, 1)
        else:
            html = source.replace('<meta charset="utf-8">', f'<meta charset="utf-8">\n{content_policy}', 1)
        html = version_references(html, file)
        check_html(file, html, output, site_url, wiki)
        file.write_text(html, encoding="utf-8", newline="\n")

    manifest = [
        f"{sha256((output / path).read_bytes()).hexdigest()}  {path}\n" for path in sorted(actual)
    ]
    (output / "release.sha256").write_text("".join(manifest), encoding="utf-8", newline="\n")
