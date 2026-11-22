"""Load the quiz catalog from a pinned public CountyUkiyoe export."""

from hashlib import sha256
import json
from pathlib import Path
import re

GALLERY_COMMIT = "6c4154d4f5bf903d3ce6e944507a6106e23bc854"
GALLERY_INDEX_SHA256 = "34188f7d3cb8c94c4837c7b7e08453318b57d13dd8562d11e212f1f3e7563881"
STYLES = {
    "connect": "牵线搭桥",
    "plan": "理清流程",
    "try": "先试再说",
    "boundary": "守住分寸",
    "warm": "暖场接话",
    "observe": "观察线索",
    "coordinate": "现场协调",
    "fix": "动手解决",
}


def intro(card):
    blurb = (card.get("blurb") or "").strip()
    if len(blurb) >= 10:
        return blurb
    summary = card["summary"].strip()
    sentence = re.split(r"(?<=[。！？])", summary, maxsplit=1)[0]
    return sentence if len(sentence) <= 130 else sentence[:129] + "…"


def load_catalog(source, src):
    gallery = Path(source) / "gallery"
    index = (gallery / "index.json").read_bytes()
    if sha256(index).hexdigest() != GALLERY_INDEX_SHA256:
        raise ValueError(f"Expected public CountyUkiyoe gallery commit {GALLERY_COMMIT}")

    cards = {}
    for card in json.loads(index)["cards"]:
        if card.get("merged_into"):
            continue
        role_id = str(card["id"]).zfill(4)
        slug = card["slug"]
        folder = gallery / "characters" / slug
        if (role_id in cards or not re.fullmatch(r"[0-9]{4}", role_id)
                or not re.fullmatch(rf"{role_id}-[a-z0-9]+(?:-[a-z0-9]+)*", slug)
                or not card["name"].strip() or not card["summary"].strip()
                or not card["validated"] or card["image_status"] != "reviewed"
                or not all((path := folder / name).is_file() and path.stat().st_size
                           for name in ("portrait.jpg", "dossier.md", "dossier.json"))):
            raise ValueError(f"Incomplete public profile: {slug}")
        cards[role_id] = {"slug": slug, "name": card["name"], "intro": intro(card)}

    pools = json.loads((src / "pools.json").read_text(encoding="utf-8"))
    ids = [role_id for bucket in pools.values() for role_id in bucket]
    if (len(cards) != 427 or set(pools) != STYLES.keys() or not all(pools.values())
            or len(ids) != len(cards) or set(ids) != cards.keys()):
        raise ValueError("Every active gallery card must occur once in a populated quiz style")

    questions = json.loads((src / "questions.json").read_text(encoding="utf-8"))
    if len(questions) != 32 or len({question["id"] for question in questions}) != len(questions):
        raise ValueError("Expected 32 questions with unique IDs")
    covered = set()
    for question in questions:
        options = question["options"]
        styles = {style for style, _ in options}
        if (not re.fullmatch(r"q[0-9]{2}", question["id"])
                or not question["scene"].strip() or not question["title"].strip()
                or len(options) != 4 or len(styles) != 4 or not styles <= STYLES.keys()
                or not all(label.strip() for _, label in options)):
            raise ValueError(f"Invalid question: {question['id']}")
        covered.update(styles)
    if covered != STYLES.keys():
        raise ValueError("Every quiz style must occur in the question bank")
    return cards, pools, questions
