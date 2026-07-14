#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
1001fish 配图管线：按拉丁学名从 Wikipedia pageimages API 取真实鱼图，下载到 images/{id}.jpg。
学名取不到时回退用英文俗名。生成 _images.json 清单（哪些成功/失败/来源）。
用法: python fetch_images.py            # 全量（跳过已下载）
      python fetch_images.py --force    # 重下全部
      python fetch_images.py --ids 5,7  # 只处理指定 id
"""
import json, os, re, sys, time, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(ROOT, "images")
MANIFEST = os.path.join(ROOT, "_images.json")
UA = "1001fish/1.0 (educational bilingual fish gallery; contact popstudy@gmail.com)"
API = "https://en.wikipedia.org/w/api.php"
REST = "https://en.wikipedia.org/api/rest_v1/page/summary/"
THUMB = 800  # 卡片/弹窗用的图宽

def load_fish():
    txt = open(os.path.join(ROOT, "fish.js"), encoding="utf-8").read()
    start = txt.index("[")
    end = txt.rindex("]")
    arr = txt[start:end+1]
    arr = re.sub(r"/\*.*?\*/", "", arr, flags=re.S)   # 去掉分区注释块
    return json.loads(arr)

# 文件名里出现这些词，多半不是活体照片（示意图/分布图/古画/化石等），弃用
BAD_WORDS = ("svg", "size", "diagram", "distribution", "range_map", "locator",
             "map_", "_map", "chart", "cladogram", "phylogen", "scale",
             "sketchbook", "painting", "illustration", "drawing", "plate",
             "engraving", "lithograph", "fossil", "skeleton", "stamp", "logo")

def is_bad_image(url):
    name = urllib.parse.unquote(url).rsplit("/", 1)[-1].lower()
    return any(w in name for w in BAD_WORDS)

def api_image(title):
    """返回 (thumb_url, original_url, resolved_title) 或 None"""
    q = urllib.parse.urlencode({
        "action": "query", "titles": title, "prop": "pageimages",
        "piprop": "thumbnail|original", "pithumbsize": THUMB,
        "format": "json", "redirects": 1,
    })
    req = urllib.request.Request(API + "?" + q, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=25) as r:
        data = json.loads(r.read().decode("utf-8"))
    pages = data.get("query", {}).get("pages", {})
    for _, p in pages.items():
        if "thumbnail" in p:
            th = p["thumbnail"]["source"]
            orig = p.get("original", {}).get("source", th)
            if is_bad_image(orig):    # 示意图/古画等，跳过让其走兜底
                return None
            return th, orig, p.get("title", title)
    return None

def rest_summary_image(title):
    """兜底：REST summary 接口，取 thumbnail 并把宽度改写为 THUMB。返回 (url, orig, title) 或 None"""
    enc = urllib.parse.quote(title.replace(" ", "_"))
    req = urllib.request.Request(REST + enc, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=25) as r:
        data = json.loads(r.read().decode("utf-8"))
    thumb = data.get("thumbnail", {}).get("source")
    if not thumb:
        return None
    orig = data.get("originalimage", {}).get("source", thumb)
    if is_bad_image(orig):
        return None
    big = re.sub(r"/\d+px-", "/%dpx-" % THUMB, thumb)   # 拉高分辨率
    return big, orig, data.get("title", title)

def commons_image(sci):
    """最终兜底：Wikimedia Commons 文件搜索（拉丁学名唯一），取 800px 缩略。返回 (url, title) 或 None"""
    q = urllib.parse.urlencode({
        "action": "query", "generator": "search",
        "gsrsearch": 'filetype:bitmap "%s"' % sci, "gsrnamespace": 6, "gsrlimit": 8,
        "prop": "imageinfo", "iiprop": "url|mime", "iiurlwidth": THUMB, "format": "json",
    })
    req = urllib.request.Request("https://commons.wikimedia.org/w/api.php?" + q,
                                 headers={"User-Agent": UA})
    d = json.loads(urllib.request.urlopen(req, timeout=25).read().decode("utf-8"))
    pages = sorted(d.get("query", {}).get("pages", {}).values(), key=lambda p: p.get("index", 99))
    for p in pages:
        ii = (p.get("imageinfo") or [{}])[0]
        mime = ii.get("mime", "")
        url = ii.get("thumburl") or ii.get("url") or ""
        title = p.get("title", "")
        if mime.startswith("image/") and "svg" not in mime and not is_bad_image(url) and not is_bad_image(title):
            return (url, None, title)
    return None

def download(url, dest):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=45) as r:
        blob = r.read()
    if len(blob) < 1500:  # 太小多半是占位/错误
        raise ValueError("image too small (%d bytes)" % len(blob))
    with open(dest, "wb") as f:
        f.write(blob)
    return len(blob)

def main():
    force = "--force" in sys.argv
    only = None
    if "--ids" in sys.argv:
        only = set(int(x) for x in sys.argv[sys.argv.index("--ids")+1].split(","))
    os.makedirs(IMG_DIR, exist_ok=True)
    fish = load_fish()
    manifest = {}
    if os.path.exists(MANIFEST):
        manifest = json.load(open(MANIFEST, encoding="utf-8"))

    ok = fail = skip = 0
    fails = []
    for f in fish:
        fid = f["id"]
        if only and fid not in only:
            continue
        dest = os.path.join(IMG_DIR, "%d.jpg" % fid)
        if not force and os.path.exists(dest) and os.path.getsize(dest) > 1500:
            skip += 1
            continue
        got = None
        titles = [t for t in (f["sci"], f.get("name_en", "")) if t]
        attempts = ([("pageimages", t) for t in titles] +
                    [("rest", t) for t in titles] +
                    [("commons", f["sci"])])   # 学名走 Commons 文件搜索兜底
        for method, title in attempts:
            try:
                if method == "pageimages": got = api_image(title)
                elif method == "rest":     got = rest_summary_image(title)
                else:                      got = commons_image(title)
                if got:
                    break
            except Exception as e:
                print("  %s err [%s] %s: %s" % (method, fid, title, e))
            time.sleep(0.2)
        if not got:
            fail += 1
            fails.append((fid, f["sci"]))
            manifest[str(fid)] = {"ok": False, "sci": f["sci"]}
            print("  MISS %-4d %s / %s" % (fid, f["sci"], f.get("name_en", "")))
            continue
        thumb_url, orig_url, resolved = got
        try:
            size = download(thumb_url, dest)
            ok += 1
            manifest[str(fid)] = {"ok": True, "sci": f["sci"], "src": thumb_url,
                                  "orig": orig_url, "title": resolved, "bytes": size}
            print("  OK   %-4d %-28s <- %s" % (fid, f["sci"], resolved))
        except Exception as e:
            fail += 1
            fails.append((fid, f["sci"]))
            manifest[str(fid)] = {"ok": False, "sci": f["sci"], "err": str(e)}
            print("  DLERR %-4d %s: %s" % (fid, f["sci"], e))
        time.sleep(0.2)

    json.dump(manifest, open(MANIFEST, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    print("\n=== done: %d ok, %d fail, %d skip (total %d) ===" % (ok, fail, skip, len(fish)))
    if fails:
        print("misses:", ", ".join("%d(%s)" % (i, s) for i, s in fails))

if __name__ == "__main__":
    main()
