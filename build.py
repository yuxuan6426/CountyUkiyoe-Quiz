"""Build the quiz and its public result pages with Python's standard library."""

import argparse
from collections import Counter
from hashlib import sha256
from html import escape
from itertools import combinations_with_replacement
import json
from pathlib import Path
import re
import shutil
from string import Template
import subprocess
from urllib.parse import urlsplit

from vendor.qrcodegen import QrCode

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
TITLE = "县城隐藏属性测试"
SOURCE = "https://github.com/yuxuan6426/CountyUkiyoe-Quiz"
GALLERY_SOURCE = "https://github.com/yuxuan6426/CountyUkiyoe"
GALLERY = "https://yuxuan6426.github.io/CountyUkiyoe/"
LICENSE = "https://creativecommons.org/licenses/by-nc-nd/4.0/deed.zh-hans"
DEFAULT_URL = "https://yuxuan6426.github.io/CountyUkiyoe-Quiz/"
DEFAULT_PLAY_URL = "https://yuxuan6426.github.io/CountyUkiyoe-Play/"


def web_base(value):
    parts = urlsplit(value)
    if (parts.scheme not in {"http", "https"} or not parts.hostname
            or parts.username or parts.password or parts.query or parts.fragment
            or not re.fullmatch(r"(/[A-Za-z0-9._~-]+)*/?", parts.path)
            or any(segment in {".", ".."} for segment in parts.path.split("/"))
            or (parts.scheme == "http" and parts.hostname not in {"localhost", "127.0.0.1"})):
        raise ValueError("Use an HTTPS base URL with a simple path, or HTTP localhost for preview.")
    return value.rstrip("/") + "/"


def load_deck():
    deck = json.loads((SRC / "deck.json").read_text(encoding="utf-8"))
    version = deck["version"]
    roles = deck["roles"]
    if not re.fullmatch(r"v[1-9][0-9]*", version) or len(roles) != 8:
        raise ValueError("Expected a versioned deck with eight roles.")
    for role_id, role in roles.items():
        if (not re.fullmatch(r"[0-9]{4}", role_id)
                or not re.fullmatch(rf"{role_id}-[a-z0-9]+(?:-[a-z0-9]+)*", role["slug"])
                or not re.fullmatch(r"#[0-9a-f]{6}", role["accent"])
                or any(not role[key].strip() for key in ("name", "title", "prop", "line", "description"))):
            raise ValueError(f"Invalid role: {role_id}")
        portrait = SRC / "portraits" / f"{role_id}.jpg"
        if sha256(portrait.read_bytes()).hexdigest() != role["sha256"]:
            raise ValueError(f"Portrait differs from the public gallery: {portrait.name}")
    counts = Counter()
    if len(deck["questions"]) != 8:
        raise ValueError("Expected eight questions.")
    for item in deck["questions"]:
        options = item["options"]
        if (len(options) != 4 or len({role for role, _ in options}) != 4
                or any(role not in roles or not label.strip() for role, label in options)
                or not item["scene"].strip() or not item["title"].strip()):
            raise ValueError(f"Expected four distinct valid choices: {item['scene']}")
        counts.update(role for role, _ in options)
    if counts != {role_id: 4 for role_id in roles}:
        raise ValueError("Every role must appear in four choices across the quiz.")
    expected = {"-".join(pair) for pair in combinations_with_replacement(sorted(roles), 2)}
    if (deck["pairs"].keys() != expected
            or any(len(card) != 4 or any(not field.strip() for field in card)
                   for card in deck["pairs"].values())):
        raise ValueError("Expected a title, two parts and a line for all 36 pairs.")
    return deck


def verify_gallery(deck, gallery):
    def read_at_commit(path):
        return subprocess.check_output(
            ["git", "-C", str(gallery), "show", f"{deck['galleryCommit']}:{path}"]
        )

    cards = json.loads(read_at_commit("gallery/index.json").decode("utf-8-sig"))["cards"]
    cards = {str(card["id"]).zfill(4): card for card in cards if not card.get("merged_into")}
    for role_id, role in deck["roles"].items():
        card = cards[role_id]
        if card["slug"] != role["slug"] or card["name"] != role["name"]:
            raise ValueError(f"Gallery metadata mismatch: {role_id}")
        directory = f"gallery/characters/{role['slug']}"
        read_at_commit(f"{directory}/dossier.md")
        if sha256(read_at_commit(f"{directory}/portrait.jpg")).hexdigest() != role["sha256"]:
            raise ValueError(f"Gallery source hash mismatch: {role_id}")


def result_path(version, ids):
    kind = "r" if len(ids) == 1 else "duo"
    return f"{kind}/{version}/{'-'.join(sorted(ids))}/"


def portrait(role_id, role, base, *, eager=False):
    loading = "eager" if eager else "lazy"
    return (f'<img src="{base}portraits/{role_id}.jpg" alt="{escape(role["name"])}的图鉴肖像" '
            f'width="864" height="1152" loading="{loading}" decoding="async">')


def archive(role):
    slug = role["slug"]
    return f'<a class="archive" href="{GALLERY}gallery/characters/{slug}/dossier.md">读图鉴档案 ↗</a>'


def home(roles):
    featured = (("1105", "left"), ("1053", "right"), ("0206", "center"))
    prints = []
    for role_id, position in featured:
        role = roles[role_id]
        image = portrait(role_id, role, "./", eager=position == "center")
        prints.append(f'<div class="print print-{position}">{image}<span>{escape(role["name"])}</span></div>')
    return f"""
    <section id="landing" class="landing">
      <div class="intro">
        <p id="invite" class="invite" hidden></p>
        <h1>你在县城<br>有什么<em>隐藏属性</em>？</h1>
        <p class="intro-copy">八道熟人局情境题，测测饭局、夜市和同学群里，大家会给你封个什么称号。</p>
        <p class="start-row"><a class="button primary" id="start" href="#quiz">开始测评 <span aria-hidden="true">↗</span></a><span>8 道题，约 2 分钟</span></p>
        <p class="hint">领完卡还能喊朋友来搭伙。</p>
        <noscript><p class="hint">开启 JavaScript 就能开始答题。</p></noscript>
      </div>
      <div class="hero-art">
        <div class="portrait-stage">
          {"".join(prints)}
          <div class="hero-stamp" aria-hidden="true">熟人局<br>验明正身</div>
        </div>
        <p>选自<a href="{GALLERY}">县城浮世绘人物图鉴</a></p>
      </div>
    </section>
    <section id="quiz" class="question-sheet" aria-labelledby="question-title" hidden>
      <div class="question-top">
        <span id="scene" class="ticket"></span>
        <p id="progress"></p>
      </div>
      <div id="progress-track" class="progress-track" aria-hidden="true"></div>
      <h1 id="question-title" tabindex="-1"></h1>
      <form id="question-form">
        <fieldset><legend class="visually-hidden">你会先怎么做？</legend><div id="options"></div></fieldset>
        <div class="question-controls">
          <button type="button" class="button quiet" id="previous">上一题</button>
          <button type="submit" class="button primary" id="next" disabled>下一题</button>
        </div>
      </form>
    </section>
    """


def quiz_link(base, role_id, label, css="button primary"):
    return f'<a class="{css}" href="{base}?with={role_id}#quiz">{label}</a>'


def role_result(role_id, role, base):
    return f"""
    <article class="result role-result">
      <figure class="result-portrait">{portrait(role_id, role, base, eager=True)}
        <figcaption>图鉴原型 {role_id} · {escape(role["name"])}</figcaption>
      </figure>
      <div class="result-copy">
        <p class="ticket">隐藏属性卡</p>
        <h1>{escape(role["title"])}</h1>
        <p class="punchline">{escape(role["line"])}</p>
        <p>{escape(role["description"])}</p>
        <p class="prop"><strong>随身道具</strong> {escape(role["prop"])} <span aria-hidden="true">/</span> {archive(role)}</p>
        <div class="result-actions">
          {quiz_link(base, role_id, "跟 TA 搭伙")}
          <a class="button secondary" href="{base}#quiz">我也测一张</a>
        </div>
        {share_actions()}
      </div>
    </article>
    """


def duo_result(ids, roles, pair, version, base):
    title, first, second, line = pair
    cards = []
    for index, (role_id, part) in enumerate(zip(ids, (first, second)), start=1):
        role = roles[role_id]
        card_url = base + result_path(version, [role_id])
        side = f"第 {index} 位 · " if ids[0] == ids[1] else ""
        cards.append(f"""
        <section class="duo-role">
          <figure>{portrait(role_id, role, base)}
            <figcaption>{escape(role["name"])}</figcaption>
          </figure>
          <div class="duo-role-copy">
            <h2>{side}{escape(role["title"])}</h2>
            <p>{escape(part)}</p>
            <p class="duo-links"><a href="{card_url}">看个人卡</a> {archive(role)}</p>
            {quiz_link(base, role_id, "跟这位搭伙", "button secondary")}
          </div>
        </section>
        """)
    return f"""
    <article class="result duo-result">
      <div class="duo-intro">
        <p class="ticket">双人搭档卡</p>
        <h1>{escape(title)}</h1>
        <p class="punchline">{escape(line)}</p>
      </div>
      <div class="duo-cards">{"".join(cards)}</div>
      {share_actions()}
      <p class="duo-start"><a href="{base}#quiz">我也测一张</a></p>
    </article>
    """


def share_actions():
    return """
    <section class="share" aria-label="分享结果">
      <p class="share-tools">
        <button type="button" class="button solid" id="poster-open">生成分享海报</button>
        <button type="button" class="button quiet" id="copy-link">复制链接</button>
        <button type="button" class="button quiet" id="share-link" hidden>系统分享</button>
      </p>
      <label id="manual-copy" hidden>选中链接后复制
        <input id="share-url" type="url" readonly>
      </label>
      <p class="share-status" id="share-status" role="status"></p>
      <dialog id="poster-dialog" aria-labelledby="poster-title">
        <div class="poster-toolbar">
          <h2 id="poster-title">分享海报</h2>
          <form method="dialog"><button class="button quiet">关闭</button></form>
        </div>
        <p id="poster-status" class="hint" role="status"></p>
        <img id="poster-image" width="840" height="1120" alt="有回流二维码的测评海报" hidden>
        <div class="poster-actions">
          <a class="button primary" id="poster-download" hidden download>下载 PNG</a>
          <button class="button secondary" type="button" id="poster-share" hidden>分享图片</button>
        </div>
      </dialog>
    </section>
    <noscript><p class="hint">开启 JavaScript 可在这里生成分享海报。</p></noscript>
    """


def share_data(data, url):
    code = QrCode.encode_text(url, QrCode.Ecc.MEDIUM)
    size = code.get_size()
    data["url"] = url
    data["qr"] = ["".join("1" if code.get_module(x, y) else "0" for x in range(size))
                  for y in range(size)]
    json_data = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    return f'<script type="application/json" id="share-data">{json_data}</script>'


def write_page(output, path, template, site_url, play_url, *, base, title, description,
               content, script=None, og=None):
    canonical = site_url + path
    image, width, height, alt = og or ("assets/share.jpg", 1200, 630, TITLE)
    footer_play = (f'<p><a href="{escape(play_url)}">可以试试县城浮世绘 · 领卡处 ↗</a></p>'
                   if play_url else "")
    rendered = template.substitute(
        title=escape(title), description=escape(description), canonical=escape(canonical),
        og_image=escape(site_url + image), og_width=width, og_height=height, og_alt=escape(alt),
        base=escape(base), script=(f'<script type="module" src="{base}assets/{script}"></script>'
                                   if script else ""),
        content=content, gallery=GALLERY, source=SOURCE,
        gallery_source=GALLERY_SOURCE, license=LICENSE, footer_play=footer_play,
    )
    file = output / (path if path.endswith(".html") else f"{path}index.html")
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(rendered, encoding="utf-8", newline="\n")


def build(output, site_url, play_url, gallery=None):
    deck = load_deck()
    if gallery:
        verify_gallery(deck, gallery)
    if output.exists() and any(output.iterdir()):
        raise ValueError(f"Choose an empty build output directory: {output}")
    site_url = web_base(site_url)
    play_url = web_base(play_url) if play_url else ""
    template = Template((SRC / "page.html").read_text(encoding="utf-8"))
    for directory in ("assets", "portraits"):
        shutil.copytree(SRC / directory, output / directory)
    for name in ("LICENSE", "ASSET-LICENSE.md"):
        shutil.copyfile(ROOT / name, output / name)
    if not (output / "assets/share.jpg").is_file():
        raise ValueError("Missing social preview image.")
    version, roles = deck["version"], deck["roles"]
    browser_deck = {"version": version, "questions": deck["questions"],
                    "roles": {key: role["title"] for key, role in roles.items()}}
    (output / "assets/deck.mjs").write_text(
        "export default " + json.dumps(browser_deck, ensure_ascii=False) + ";\n",
        encoding="utf-8", newline="\n",
    )
    write_page(output, "", template, site_url, play_url, base="./", title=TITLE,
               description="八道熟人局情境题。测出你的县城隐藏属性，再约朋友领一张搭档卡。",
               content=home(roles), script="quiz.mjs")

    base = "../../../"
    for role_id, role in roles.items():
        path = result_path(version, [role_id])
        data = {"kind": "role", "title": role["title"], "line": role["line"], "prop": role["prop"],
                "role": role["name"], "accent": role["accent"], "id": role_id}
        content = role_result(role_id, role, base) + share_data(data, site_url + path)
        write_page(output, path, template, site_url, play_url, base=base,
                   title=f'{role["title"]}｜{TITLE}', description=role["line"],
                   content=content, script="share.mjs",
                   og=(f"portraits/{role_id}.jpg", 864, 1152, f'{role["name"]}的图鉴肖像'))

    for pair_key, pair in deck["pairs"].items():
        ids = pair_key.split("-")
        path = result_path(version, ids)
        data = {"kind": "duo", "title": pair[0], "line": pair[3], "id": pair_key,
                "roles": [{"title": roles[role_id]["title"], "part": part}
                          for role_id, part in zip(ids, pair[1:3])]}
        content = duo_result(ids, roles, pair, version, base) + share_data(data, site_url + path)
        write_page(output, path, template, site_url, play_url, base=base,
                   title=f"{pair[0]}｜{TITLE}", description=pair[3], content=content,
                   script="share.mjs")

    fallback = escape(urlsplit(site_url).path)
    write_page(output, "404.html", template, site_url, play_url, base=fallback,
               title=f"找不到这张卡｜{TITLE}", description="回到测试首页领一张新的县城属性卡。",
               content=f'<section class="question-sheet"><h1>找不到这张卡</h1>'
                       f'<p>可以回首页领一张新的。</p><a class="button primary" href="{fallback}">回首页</a></section>')
    (output / ".nojekyll").touch()
    print(f"Built {len(roles)} role pages and {len(deck['pairs'])} duo pages in {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "dist", help="empty output directory")
    parser.add_argument("--site-url", default=DEFAULT_URL, help="public URL used in cards and QR codes")
    parser.add_argument("--play-url", default=DEFAULT_PLAY_URL, help="URL of the live AI card site")
    parser.add_argument("--verify-gallery", type=Path, help="public gallery checkout for provenance verification")
    args = parser.parse_args()
    build(args.output.resolve(), args.site_url, args.play_url, args.verify_gallery)
