import argparse
import base64
import datetime as dt
import hashlib
import html
import json
import os
import shutil
import sys
from pathlib import Path

try:
    from cryptography.exceptions import InvalidSignature
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
except ImportError:
    sys.exit("Missing dependency: run pip install cryptography")

HERE = Path(__file__).resolve().parent
ASSETS = HERE / "assets"
MANIFEST_NAME = "ummjimalseal.manifest.json"
VERSION = 1

SITE = {
    "name": "Umm al-Jimal",
    "where": "Mafraq Governorate, northern Jordan, about 17 km east of Mafraq",
    "coords": "32 19 37 N 36 22 12 E",
    "unesco": "World Heritage Site no. 1721, inscribed July 2024, Jordan 7th site",
}

TIMELINE = [
    ("1st c. CE", "Nabataean roots", "Farming homesteads and a trading outpost serving Bostra."),
    ("106 CE", "Roman rule", "Rome annexes the region. After 275 CE a fortified garrison is built."),
    ("5th-6th c.", "Byzantine prosperity", "Town grows into farming and trading centre with about 6000 people and 16 churches."),
    ("640 CE", "Early Islamic period", "Umayyad era: buildings are reused, houses become mosques, population shrinks."),
    ("c. 749 CE", "Earthquake and decline", "Major earthquake damages the town. Settlement ends by late 8th century."),
    ("2024", "World Heritage Site", "Inscribed by UNESCO for authentic basalt architecture."),
]

FACTS = [
    ("Material", "Local black volcanic basalt"),
    ("Structures", "More than 170, only a few archaeologically investigated"),
    ("Core area", "42.584 ha"),
    ("Water", "Catchment system with cisterns and channels"),
    ("Protected", "National property since 1939"),
    ("Visit", "House 119 rebuilt as visitor centre and site museum"),
]

UNESCO_AUTH = "UNESCO finds the site authentic in form, design and materials. Restoration has been minimal so what you see is the original basalt."
UNESCO_INTEG = "The walled town holds all the attributes of the settlement including parts of its water system."
SOURCES = '<a href="https://whc.unesco.org/en/list/1721/">UNESCO World Heritage Centre</a>'

class C:
    on = True
    @staticmethod
    def c(code, s):
        return f"\033[{code}m{s}\033[0m" if C.on else s
    blue = staticmethod(lambda s: C.c("1;34", s))
    green = staticmethod(lambda s: C.c("1;32", s))
    amber = staticmethod(lambda s: C.c("38;5;179", s))
    red = staticmethod(lambda s: C.c("1;31", s))
    dim = staticmethod(lambda s: C.c("2", s))
    bold = staticmethod(lambda s: C.c("1", s))

def setup_terminal(no_color):
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass
    if no_color or not sys.stdout.isatty() or os.environ.get("NO_COLOR"):
        C.on = False
    elif os.name == "nt":
        os.system("")

def prompt(cmd, path="~/heritage"):
    return (C.blue("+--(") + C.green("jimal@ummjimal") + C.blue(")-[") + path + C.blue("]\n")
            + C.blue("`--") + C.amber("$") + " " + cmd)

ARCH = r"""
  ██╗   ██╗███╗   ███╗███╗   ███╗     █████╗ ██╗         ██╗██╗███╗   ███╗ █████╗ ██╗     
  ██║   ██║████╗ ████║████╗ ████║    ██╔══██╗██║         ██║██║████╗ ████║██╔══██╗██║     
  ██║   ██║██╔████╔██║██╔████╔██║    ███████║██║         ██║██║██╔████╔██║███████║██║     
  ██║   ██║██║╚██╔╝██║██║╚██╔╝██║    ██╔══██║██║    ██   ██║██║██║╚██╔╝██║██╔══██║██║     
  ╚██████╔╝██║ ╚═╝ ██║██║ ╚═╝ ██║    ██║  ██║███████╗╚█████╔╝██║██║ ╚═╝ ██║██║  ██║███████╗
   ╚═════╝ ╚═╝     ╚═╝╚═╝     ╚═╝    ╚═╝  ╚═╝╚══════╝ ╚════╝ ╚═╝╚═╝     ╚═╝╚═╝  ╚═╝╚══════╝
"""

def banner():
    w = min(shutil.get_terminal_size((80, 24)).columns, 78)
    rule = C.dim("-" * w)
    print()
    for line in ARCH.strip("\n").splitlines():
        print(C.amber(line))
    print()
    print("  " + C.bold("U M M J I M A L S E A L"))
    print("  " + C.dim("Integrity and authenticity for your folders - SHA-256 + Ed25519"))
    print(rule)
    print(prompt("locate umm-al-jimal"))
    for k, v in (("site", SITE["name"]), ("location", SITE["where"]),
                 ("coordinates", SITE["coords"]), ("unesco", SITE["unesco"])):
        print(f"  {C.dim(k.ljust(12))} {v}")
    print(rule)
    print(prompt("cat history.log"))
    for when, title, text in TIMELINE:
        print(f"  {C.amber(when.ljust(10))} {C.bold(title)}")
        print(f"  {' ' * 10} {C.dim(text)}")
    print(rule)
    print(prompt("cat why-this-tool.txt"))
    print("  UNESCO listed Umm al-Jimal for two things: " + C.bold("authenticity") + " and " + C.bold("integrity") + ".")
    print("  " + C.dim("Same two ideas as file security: a hash proves nothing changed,"))
    print("  " + C.dim("a signature proves it is the genuine original."))
    print(rule)
    print()

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def scan(folder, skip):
    out = {}
    for root, _dirs, files in os.walk(folder):
        for name in files:
            p = Path(root) / name
            rel = p.relative_to(folder).as_posix()
            if rel in skip:
                continue
            out[rel] = sha256_file(p)
    return dict(sorted(out.items()))

def canonical(payload):
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")

def load_private(path):
    return serialization.load_pem_private_key(Path(path).read_bytes(), password=None)

def load_public(path):
    return serialization.load_pem_public_key(Path(path).read_bytes())

def compare(folder, recorded, skip):
    current = scan(folder, skip)
    modified = sorted(p for p in recorded if p in current and recorded[p] != current[p])
    removed = sorted(p for p in recorded if p not in current)
    added = sorted(p for p in current if p not in recorded)
    intact = sorted(p for p in recorded if p in current and recorded[p] == current[p])
    return modified, added, removed, intact, current

def cmd_about(_args):
    pass

def cmd_keygen(args):
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    priv = Ed25519PrivateKey.generate()
    (out / "private.pem").write_bytes(priv.private_bytes(
        serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
    (out / "public.pem").write_bytes(priv.public_key().public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo))
    try:
        os.chmod(out / "private.pem", 0o600)
    except OSError:
        pass
    print(C.green("[+]") + f" Keys written to {out}/")
    print(f"    private.pem  {C.red('keep SECRET')}")
    print(f"    public.pem   share it for verification")

def cmd_seal(args):
    folder = Path(args.folder).resolve()
    if not folder.is_dir():
        sys.exit(f"Not a folder: {folder}")
    manifest_path = Path(args.manifest) if args.manifest else folder / MANIFEST_NAME
    skip = {MANIFEST_NAME}
    if manifest_path.resolve().parent == folder:
        skip.add(manifest_path.name)
    files = scan(folder, skip)
    payload = {
        "tool": "ummjimalseal", "version": VERSION,
        "sealed_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "algorithm": "sha256", "files": files,
    }
    sig = load_private(args.key).sign(canonical(payload))
    doc = {"payload": payload, "signature": base64.b64encode(sig).decode()}
    manifest_path.write_text(json.dumps(doc, indent=2, ensure_ascii=False), encoding="utf-8")
    print(C.green("[+]") + f" Sealed {len(files)} files -> {manifest_path}")

def cmd_verify(args):
    folder = Path(args.folder).resolve()
    manifest_path = Path(args.manifest) if args.manifest else folder / MANIFEST_NAME
    if not manifest_path.is_file():
        sys.exit(f"Manifest not found: {manifest_path}")
    doc = json.loads(manifest_path.read_text(encoding="utf-8"))
    payload, sig = doc["payload"], base64.b64decode(doc["signature"])

    try:
        load_public(args.pub).verify(sig, canonical(payload))
        authentic = True
    except InvalidSignature:
        authentic = False

    skip = {MANIFEST_NAME}
    if manifest_path.resolve().parent == folder:
        skip.add(manifest_path.name)

    modified, added, removed, intact, current = compare(folder, payload["files"], skip)
    clean = authentic and not (modified or added or removed)

    sig_txt = C.green("VALID") if authentic else C.red("INVALID")
    print(C.bold("Signature (authenticity):"), sig_txt)
    print(C.bold("Sealed at:"), payload.get("sealed_at"))
    print(C.bold("Files:"), f"intact {len(intact)}, modified {len(modified)}, added {len(added)}, removed {len(removed)}")
    for tag, items, col in (("MODIFIED", modified, C.red), ("ADDED", added, C.amber), ("REMOVED", removed, C.red)):
        for p in items:
            print("  " + col(f"[{tag}]") + f" {p}")
    print(C.dim("-" * 40))
    print(C.bold("RESULT:"), C.green("ORIGINAL, the seal holds") if clean
          else C.red("TAMPERED, do not trust this folder"))

    if args.html:
        out = write_html(Path(args.html), folder.name, payload, authentic,
                         modified, added, removed, intact, current)
        print(C.green("[+]") + f" HTML report -> {out}")
    sys.exit(0 if clean else 1)

def img_data_uri(path):
    if not path.is_file():
        return None
    return "data:image/jpeg;base64," + base64.b64encode(path.read_bytes()).decode()

def write_html(path, name, payload, authentic, modified, added, removed, intact, current):
    template_path = ASSETS / "report_template.html"
    if not template_path.is_file():
        sys.exit(f"Report template missing: {template_path}")
    clean = authentic and not (modified or added or removed)
    esc = html.escape

    def rows(items, cls, label, hashes):
        return "".join(
            f'<div class="row {cls}"><span class="c">{label}</span><span class="p">{esc(p)}</span>'
            f'<span class="h">{esc(hashes.get(p, "")[:16])}</span></div>' for p in items)

    rec = payload["files"]
    problems = (rows(modified, "bad", "MODIFIED", current) + rows(added, "warn", "ADDED", current)
                + rows(removed, "bad", "REMOVED", rec))
    shown = intact[:12]
    ok_rows = rows(shown, "ok", "INTACT", rec)
    if len(intact) > len(shown):
        ok_rows += f'<div class="more">... and {len(intact) - len(shown)} more intact files</div>'
    files_html = (problems + ok_rows) or '<div class="more">(no files)</div>'

    timeline = "".join(
        f'<li><div class="when">{esc(w)}</div><h4>{esc(t)}</h4><p>{esc(d)}</p></li>' for w, t, d in TIMELINE)
    facts = "".join(f"<dt>{esc(k)}</dt><dd>{esc(v)}</dd>" for k, v in FACTS)

    hero = img_data_uri(ASSETS / "umm-al-jimal-1.jpg")
    photo2 = img_data_uri(ASSETS / "umm-al-jimal-2.jpg")

    if clean:
        verdict, vsub = "ORIGINAL", "The seal holds. Every file matches what was signed."
    elif not authentic:
        verdict, vsub = "FORGED SEAL", "The manifest signature does not match this public key."
    else:
        verdict, vsub = "TAMPERED", "The signature is genuine, but files changed after sealing."

    rep = {
        "%%FOLDER%%": esc(name),
        "%%HERO_IMG%%": f'<img src="{hero}" alt="Umm al-Jimal">' if hero else "",
        "%%PHOTO2%%": f'<div class="photo"><img src="{photo2}" alt="Umm al-Jimal"></div>' if photo2 else "",
        "%%CLASS%%": "ok" if clean else "bad",
        "%%STAMP_LABEL%%": "SEALED" if clean else "BROKEN",
        "%%COORDS%%": esc(SITE["coords"]),
        "%%SITE_NAME%%": esc(SITE["name"]),
        "%%WHERE%%": esc(SITE["where"]),
        "%%UNESCO%%": esc(SITE["unesco"]),
        "%%CMD%%": "umm_jimal_seal verify " + esc(name) + " --pub public.pem",
        "%%VERDICT%%": verdict,
        "%%VERDICT_SUB%%": vsub,
        "%%SIGCLASS%%": "sigok" if authentic else "sigbad",
        "%%SIG%%": "VALID" if authentic else "INVALID",
        "%%SEALED_AT%%": esc(str(payload.get("sealed_at"))),
        "%%N_INTACT%%": str(len(intact)), "%%N_MOD%%": str(len(modified)),
        "%%N_ADD%%": str(len(added)), "%%N_REM%%": str(len(removed)),
        "%%FILES%%": files_html,
        "%%FACT_TABLE%%": facts,
        "%%TIMELINE%%": timeline,
        "%%AUTH_UNESCO%%": esc(UNESCO_AUTH),
        "%%AUTH_TOOL%%": "In this tool the Ed25519 signature proves the manifest is the genuine original.",
        "%%INTEG_UNESCO%%": esc(UNESCO_INTEG),
        "%%INTEG_TOOL%%": "In this tool the SHA-256 hashes prove every file is exactly as it was when sealed.",
        "%%SOURCES%%": SOURCES,
    }
    page = template_path.read_text(encoding="utf-8")
    for k, v in rep.items():
        page = page.replace(k, v)
    path.write_text(page, encoding="utf-8")
    return path

def main():
    ap = argparse.ArgumentParser(prog="umm_jimal_seal")
    ap.add_argument("--no-banner", action="store_true")
    ap.add_argument("--no-color", action="store_true")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("about").set_defaults(fn=cmd_about)

    k = sub.add_parser("keygen")
    k.add_argument("--out", default="keys")
    k.set_defaults(fn=cmd_keygen)

    s = sub.add_parser("seal")
    s.add_argument("folder")
    s.add_argument("--key", required=True)
    s.add_argument("--manifest")
    s.set_defaults(fn=cmd_seal)

    v = sub.add_parser("verify")
    v.add_argument("folder")
    v.add_argument("--pub", required=True)
    v.add_argument("--manifest")
    v.add_argument("--html")
    v.set_defaults(fn=cmd_verify)

    args = ap.parse_args()
    setup_terminal(args.no_color)
    if args.cmd == "about" or not args.no_banner:
        banner()
    args.fn(args)

if __name__ == "__main__":
    main()