#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
下载 _harvest_imgmap.json 里补齐物种的图片到 images/{id}.jpg，并更新 _images.json。
用 Commons Special:FilePath 的 ?width=800 直接取缩放图，不走 API（避免限流）。
可重复运行：已下载的跳过。--force 重下。
"""
import json, os, sys, time, urllib.parse, urllib.request, urllib.error

ROOT = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(ROOT, "images")
UA = "1001fish/1.0 (educational bilingual fish gallery; popstudy@gmail.com)"
WIDTH = 800

def thumb_url(u):
    # P18 值形如 .../Special:FilePath/Name.jpg —— 加 width 参数取缩放版
    sep = "&" if "?" in u else "?"
    return u + sep + "width=%d" % WIDTH

def download(url, dest, tries=3):
    for a in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=60) as r:
                blob = r.read()
            if len(blob) < 1500:
                raise ValueError("too small %d" % len(blob))
            open(dest, "wb").write(blob)
            return len(blob)
        except urllib.error.HTTPError as e:
            if e.code in (429, 503) and a < tries - 1:
                time.sleep(3); continue
            raise
    raise RuntimeError("unreachable")

def main():
    force = "--force" in sys.argv
    imgmap = json.load(open(os.path.join(ROOT, "_harvest_imgmap.json"), encoding="utf-8"))
    manifest = {}
    mpath = os.path.join(ROOT, "_images.json")
    if os.path.exists(mpath):
        manifest = json.load(open(mpath, encoding="utf-8"))
    os.makedirs(IMG_DIR, exist_ok=True)

    ok = fail = skip = 0
    fails = []
    items = sorted(imgmap.items(), key=lambda kv: int(kv[0]))
    for i, (fid, url) in enumerate(items):
        dest = os.path.join(IMG_DIR, "%s.jpg" % fid)
        if not force and os.path.exists(dest) and os.path.getsize(dest) > 1500:
            skip += 1; continue
        try:
            n = download(thumb_url(url), dest)
            manifest[fid] = {"ok": True, "src": thumb_url(url), "orig": url, "bytes": n}
            ok += 1
            if ok % 25 == 0:
                print("  ...%d ok (at id %s)" % (ok, fid)); sys.stdout.flush()
                json.dump(manifest, open(mpath, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
        except Exception as e:
            fail += 1; fails.append(fid)
            manifest[fid] = {"ok": False, "err": str(e)}
            print("  MISS %s: %s" % (fid, e))
        time.sleep(0.15)

    json.dump(manifest, open(mpath, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    print("=== harvest imgs: %d ok, %d fail, %d skip ===" % (ok, fail, skip))
    if fails:
        print("misses:", ",".join(fails))

if __name__ == "__main__":
    main()
