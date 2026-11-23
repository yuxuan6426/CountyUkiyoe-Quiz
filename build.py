"""Build the quiz and its public result pages with Python's standard library."""

import argparse
from collections import Counter
from hashlib import sha256
from html import escape
import json
from pathlib import Path
import re
import shutil
from string import Template
import subprocess
from urllib.parse import urlsplit

from catalog import load_catalog, STYLES
from vendor.qrcodegen import QrCode

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
TITLE = "县城隐藏属性测试"
VERSION = "v2"
SOURCE = "https://github.com/yuxuan6426/CountyUkiyoe-Quiz"
GALLERY = "https://xian.yuxuan.wiki/"
LICENSE = "https://creativecommons.org/licenses/by-nc-nd/4.0/deed.zh-hans"
DEFAULT_URL = "https://quiz.yuxuan.wiki/"
DEFAULT_PLAY_URL = "https://card.yuxuan.wiki/"
PAGES_ROOT = "https://yuxuan6426.github.io/"
PAGES_GALLERY = PAGES_ROOT + "CountyUkiyoe/"
PAGES_PLAY = PAGES_ROOT + "CountyUkiyoe-Play/"


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
    for key, card in deck["pairs"].items():
        ids = key.split("-")
        if (len(ids) != 2 or ids != sorted(ids) or any(role_id not in roles for role_id in ids)
                or len(card) != 4 or any(not field.strip() for field in card)):
            raise ValueError(f"Invalid archived pair: {key}")
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


def gallery_portrait_url(role, gallery_url):
    return f'{gallery_url}gallery/characters/{role["slug"]}/portrait.jpg'


def portrait(role_id, role, base, gallery_url, *, eager=False, versioned=False):
    loading = "eager" if eager else "lazy"
    backup = gallery_portrait_path(role_id) if versioned else f"portraits/{role_id}.jpg"
    return (f'<img src="{gallery_portrait_url(role, gallery_url)}" data-backup="{base}{backup}" '
            f'alt="{escape(role["name"])}的图鉴肖像" '
            f'width="864" height="1152" loading="{loading}" decoding="async">')


def gallery_card_url(role, gallery_url):
    return f"{gallery_url}site/character.html?card={role['slug']}"


def linked_portrait(role, image, gallery_url):
    return (f'<a class="portrait-link" href="{gallery_card_url(role, gallery_url)}" '
            f'aria-label="查看{escape(role["name"])}的图鉴卡">{image}</a>')


def archive(role, gallery_url):
    return f'<a class="archive" href="{gallery_card_url(role, gallery_url)}">查看图鉴卡 ↗</a>'


def home(roles, gallery_url):
    featured = (("1105", "left"), ("1053", "right"), ("0206", "center"))
    prints = []
    for role_id, position in featured:
        role = roles[role_id]
        image = linked_portrait(role, portrait(role_id, role, "./", gallery_url, eager=position == "center"), gallery_url)
        prints.append(f'<div class="print print-{position}">{image}<span>{escape(role["name"])}</span></div>')
    return f"""
    <section id="landing" class="landing">
      <div class="intro">
        <p id="invite" class="invite" hidden></p>
        <h1>你在县城<br>有什么<em>隐藏属性</em>？</h1>
        <p class="intro-copy">从饭局、夜市、同学群里抽几道题，翻一张县城人物卡。</p>
        <p class="start-row"><a class="button primary" id="start" href="#quiz">开始测评 <span aria-hidden="true">↗</span></a><span>每轮 6 题，答 1 题就能翻卡</span></p>
        <p class="hint">也可以喊朋友来，各翻一张卡。</p>
        <noscript><p class="hint">开启 JavaScript 就能开始答题。</p></noscript>
      </div>
      <div class="hero-art">
        <div class="portrait-stage">
          {"".join(prints)}
          <div class="hero-stamp" aria-hidden="true">熟人局<br>验明正身</div>
        </div>
        <p>选自<a href="{gallery_url}">县城浮世绘人物图鉴</a></p>
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
          <button type="button" class="button quiet" id="next">跳过本题</button>
          <button type="submit" class="button primary" id="finish" disabled>翻开我的卡</button>
        </div>
        <p class="hint" id="finish-hint">选一个答案就可以翻卡。</p>
      </form>
    </section>
    """


def quiz_link(base, role_id, label, css="button primary"):
    return f'<a class="{css}" href="{base}?with={role_id}#quiz">{label}</a>'


def invite_actions(base, role_id):
    return f"""
    <button class="button primary" type="button" id="invite-open" disabled>邀请好友翻卡</button>
    <dialog id="invite-dialog" aria-labelledby="invite-title">
      <div class="poster-toolbar">
        <h2 id="invite-title">邀请好友翻卡</h2>
        <form method="dialog"><button class="button quiet">关闭</button></form>
      </div>
      <div id="invite-options">
        <p>你们想线上一起玩，还是当面答题？</p>
        <div class="result-actions">
          <button class="button primary" type="button" id="invite-online">线上邀请</button>
          <a class="button secondary" href="{base}?with={role_id}#quiz">线下当面答</a>
        </div>
      </div>
      <div id="invite-online-tools" hidden>
        <p>把邀请发给好友。每位好友答完，都会与你生成一张双人卡。</p>
        <div class="result-actions">
          <button class="button primary" type="button" id="copy-invite">复制邀请文案</button>
          <button class="button secondary" type="button" id="invite-poster">生成邀请海报</button>
        </div>
        <label id="invite-manual" hidden>复制选中的邀请文案
          <textarea id="invite-copy" rows="4" readonly></textarea>
        </label>
        <p class="share-status" id="invite-status" role="status"></p>
      </div>
    </dialog>
    """


def role_result(role_id, role, base, gallery_url):
    return f"""
    <article class="result role-result">
      <figure class="result-portrait">{linked_portrait(role, portrait(role_id, role, base, gallery_url, eager=True), gallery_url)}
        <figcaption>图鉴原型 {role_id} · {escape(role["name"])}</figcaption>
      </figure>
      <div class="result-copy">
        <p class="ticket">隐藏属性卡</p>
        <h1>{escape(role["title"])}</h1>
        <p class="punchline">{escape(role["line"])}</p>
        <p>{escape(role["description"])}</p>
        <p class="prop"><strong>随身道具</strong> {escape(role["prop"])} <span aria-hidden="true">/</span> {archive(role, gallery_url)}</p>
        <div class="result-actions">
          {invite_actions(base, role_id)}
          <a class="button secondary" href="{base}#quiz">我也测一张</a>
        </div>
        {share_actions()}
      </div>
    </article>
    """


def duo_result(ids, roles, pair, version, base, gallery_url):
    title, first, second, line = pair
    cards = []
    for index, (role_id, part) in enumerate(zip(ids, (first, second)), start=1):
        role = roles[role_id]
        card_url = base + result_path(version, [role_id])
        side = f"第 {index} 位 · " if ids[0] == ids[1] else ""
        cards.append(f"""
        <section class="duo-role">
          <figure>{linked_portrait(role, portrait(role_id, role, base, gallery_url), gallery_url)}
            <figcaption>{escape(role["name"])}</figcaption>
          </figure>
          <div class="duo-role-copy">
            <h2>{side}{escape(role["title"])}</h2>
            <p>{escape(part)}</p>
            <p class="duo-links"><a href="{card_url}">看个人卡</a> {archive(role, gallery_url)}</p>
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
        <button type="button" class="button solid" id="poster-open" disabled>生成分享海报</button>
        <button type="button" class="button quiet" id="copy-link" disabled>复制分享文案</button>
      </p>
      <label id="manual-copy" hidden>复制选中的分享文案
        <textarea id="share-copy" rows="4" readonly></textarea>
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


def gallery_portrait_path(role_id):
    return f"portraits/{VERSION}/{role_id}.jpg"


def gallery_result(role_id, role, base, gallery_url):
    image = portrait(role_id, role, base, gallery_url, eager=True, versioned=True)
    return f"""
    <article class="result role-result">
      <figure class="result-portrait">
        {linked_portrait(role, image, gallery_url)}
        <figcaption>图鉴原型 {role_id} · {escape(role['name'])}</figcaption>
      </figure>
      <div class="result-copy">
        <p class="ticket">隐藏属性卡</p>
        <h1>{escape(role['name'])}</h1>
        <p class="punchline">{escape(role['style'])}</p>
        <p>{escape(role['intro'])}</p>
        <p>{archive(role, gallery_url)}</p>
        <div class="result-actions">
          {invite_actions(base, role_id)}
          <a class="button secondary" href="{base}?new=1#quiz">再测一次</a>
        </div>
        {share_actions()}
      </div>
    </article>
    """


def pair_shell(base):
    return f"""
    <article class="result duo-result" id="pair-view" hidden>
      <div class="duo-intro">
        <h1>我们的县城人物卡</h1>
      </div>
      <div class="duo-cards" id="pair-cards"></div>
      {share_actions()}
      <p class="duo-start"><a href="{base}?new=1#quiz">我也测一张</a></p>
    </article>
    <section class="question-sheet" id="pair-missing" hidden>
      <h1>找不到这两张卡</h1>
      <p><a class="button primary" href="{base}">回到测试首页</a></p>
    </section>
    <noscript><p class="hint">开启 JavaScript 就可以打开双人卡。</p></noscript>
    """


def write_module(output, name, data):
    (output / "assets" / f"{name}.mjs").write_text(
        "export default " + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";\n",
        encoding="utf-8", newline="\n",
    )


def share_data(data, url):
    code = QrCode.encode_text(url, QrCode.Ecc.MEDIUM)
    size = code.get_size()
    data["url"] = url
    data["qr"] = ["".join("1" if code.get_module(x, y) else "0" for x in range(size))
                  for y in range(size)]
    json_data = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    return f'<script type="application/json" id="share-data">{json_data}</script>'


def write_page(output, path, template, site_url, play_url, gallery_url, *, base, title, description,
               content, script=None, og=None, stylesheet="style.css"):
    canonical = site_url + path
    image, width, height, alt = og or ("assets/share.jpg", 1200, 630, TITLE)
    image_url = image if urlsplit(image).scheme else site_url + image
    footer_play = (f'<p><a href="{escape(play_url)}">可以试试县城浮世绘 · 领卡处 ↗</a></p>'
                   if play_url else "")
    rendered = template.substitute(
        title=escape(title), description=escape(description), canonical=escape(canonical),
        og_image=escape(image_url), og_width=width, og_height=height, og_alt=escape(alt),
        base=escape(base), stylesheet=stylesheet,
        script=(f'<script type="module" src="{base}assets/{script}"></script>'
                                   if script else ""),
        content=content, gallery=gallery_url, source=SOURCE,
        license=LICENSE, footer_play=footer_play,
    )
    file = output / (path if path.endswith(".html") else f"{path}index.html")
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(rendered, encoding="utf-8", newline="\n")


def build(output, site_url, play_url, gallery_source, gallery=None, gallery_url=None):
    deck = load_deck()
    cards, pools, questions = load_catalog(gallery_source, SRC)
    if gallery:
        verify_gallery(deck, gallery)
    if output.exists() and any(output.iterdir()):
        raise ValueError(f"Choose an empty build output directory: {output}")
    site_url = web_base(site_url)
    pages = urlsplit(site_url).hostname == urlsplit(PAGES_ROOT).hostname
    gallery_url = web_base(gallery_url or (PAGES_GALLERY if pages else GALLERY))
    if play_url is None:
        play_url = PAGES_PLAY if pages else DEFAULT_PLAY_URL
    play_url = web_base(play_url) if play_url else ""
    template = Template((SRC / "page.html").read_text(encoding="utf-8"))
    for directory in ("assets", "portraits"):
        shutil.copytree(SRC / directory, output / directory)
    (output / "portraits" / VERSION).mkdir()
    for role_id, role in cards.items():
        original = Path(gallery_source) / "gallery" / "characters" / role["slug"] / "portrait.jpg"
        shutil.copyfile(original, output / gallery_portrait_path(role_id))
    shutil.copyfile(SRC / "assets/style.css", output / "assets/style-v2.css")
    for name in ("LICENSE", "ASSET-LICENSE.md"):
        shutil.copyfile(ROOT / name, output / name)
    if not (output / "assets/share.jpg").is_file():
        raise ValueError("Missing social preview image.")
    version, roles = deck["version"], deck["roles"]
    for style, ids in pools.items():
        for role_id in ids:
            cards[role_id]["style"] = STYLES[style]
    write_module(output, "questions-v2", {
        "version": VERSION, "questions": questions, "pools": pools,
        "roles": {key: card["name"] for key, card in cards.items()},
    })
    write_module(output, "cards-invite", {"cards": cards, "gallery": gallery_url,
                                   "version": VERSION, "site": site_url})
    write_page(output, "", template, site_url, play_url, gallery_url, base="./", title=TITLE,
               description="每次抽六道县城生活题，答一道就能翻开你的人物卡。也可以约朋友一起翻卡。",
               content=home(roles, gallery_url), script="quiz-entry.mjs", stylesheet="style-v2.css?v=invite")

    base = "../../../"
    for role_id, role in roles.items():
        path = result_path(version, [role_id])
        data = {"kind": "role", "title": role["title"], "detail": role["prop"],
                "role": role["name"], "id": role_id, "invite": f"{site_url}?with={role_id}"}
        content = role_result(role_id, role, base, gallery_url) + share_data(data, site_url + path)
        write_page(output, path, template, site_url, play_url, gallery_url, base=base,
                   title=f'{role["title"]}｜{TITLE}', description=role["line"],
                   content=content, script="share-invite.mjs",
                   og=(gallery_portrait_url(role, gallery_url), 864, 1152, f'{role["name"]}的图鉴肖像'),
                   stylesheet="style.css?v=invite")

    for pair_key, pair in deck["pairs"].items():
        ids = pair_key.split("-")
        path = result_path(version, ids)
        data = {"kind": "duo", "title": pair[0], "id": pair_key,
                "roles": [roles[role_id]["name"] for role_id in ids]}
        content = duo_result(ids, roles, pair, version, base, gallery_url) + share_data(data, site_url + path)
        write_page(output, path, template, site_url, play_url, gallery_url, base=base,
                   title=f"{pair[0]}｜{TITLE}", description=pair[3], content=content,
                   script="share-invite.mjs", stylesheet="style.css?v=invite")

    for role_id, role in cards.items():
        path = result_path(VERSION, [role_id])
        data = {"kind": "role", "title": role["name"], "role": role["name"],
                "detail": role["style"], "id": role_id, "invite": f"{site_url}?with={role_id}"}
        content = gallery_result(role_id, role, base, gallery_url) + share_data(data, site_url + path)
        write_page(output, path, template, site_url, play_url, gallery_url, base=base,
                   title=f'{role["name"]}｜{TITLE}', description=role["intro"],
                   content=content, script="share-invite.mjs", stylesheet="style-v2.css?v=invite",
                   og=(gallery_portrait_url(role, gallery_url),
                       864, 1152, f'{role["name"]}的图鉴肖像'))

    pair_base = "../../"
    write_page(output, f"duo/{VERSION}/", template, site_url, play_url, gallery_url, base=pair_base,
               title=f"我们的县城人物卡｜{TITLE}", description="一起看看朋友抽到了哪两位县城人物。",
               content=pair_shell(pair_base), script="pair-invite.mjs", stylesheet="style-v2.css?v=invite")

    fallback = escape(urlsplit(site_url).path)
    write_page(output, "404.html", template, site_url, play_url, gallery_url, base=fallback,
               title=f"找不到这张卡｜{TITLE}", description="回到测试首页领一张新的县城属性卡。",
               content=f'<section class="question-sheet"><h1>找不到这张卡</h1>'
                       f'<p>可以回首页领一张新的。</p><a class="button primary" href="{fallback}">回首页</a></section>')
    (output / ".nojekyll").touch()
    print(f"Built {len(cards)} v2 role pages, one v2 pair page and "
          f"{len(roles) + len(deck['pairs'])} archived result pages in {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "dist", help="empty output directory")
    parser.add_argument("--site-url", default=DEFAULT_URL, help="public URL used in cards and QR codes")
    parser.add_argument("--play-url", help="AI card site URL, inferred from --site-url by default")
    parser.add_argument("--gallery-url", help="gallery URL, inferred from --site-url by default")
    parser.add_argument("--gallery-source", type=Path, default=ROOT / ".gallery-source",
                        help="public CountyUkiyoe checkout at the revision pinned in catalog.py")
    parser.add_argument("--verify-gallery", type=Path, help="public gallery checkout for provenance verification")
    args = parser.parse_args()
    build(args.output.resolve(), args.site_url, args.play_url, args.gallery_source,
          args.verify_gallery, args.gallery_url)
