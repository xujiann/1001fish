#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""按「目」逐个采集辐鳍鱼（整个超纲一次查会 504 超时），累积合并进 _harvest_raw.json。
   进度记录在 _orders_done.json，可随时中断续跑。"""
import json, os, sys, time, urllib.parse, urllib.request, urllib.error

ROOT = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(ROOT, "_harvest_raw.json")
DONE = os.path.join(ROOT, "_orders_done.json")
UA = "1001fish/1.0 (educational; popstudy@gmail.com)"
EP = "https://query.wikidata.org/sparql"

def sparql(q, tries=5, timeout=240):
    url = EP + "?" + urllib.parse.urlencode({"query": q, "format": "json"})
    for a in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA,
                     "Accept": "application/sparql-results+json"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read().decode("utf-8"))["results"]["bindings"]
        except urllib.error.HTTPError as e:
            if e.code in (429,500,502,503,504) and a < tries-1:
                time.sleep(45); continue
            raise
        except Exception:
            if a < tries-1: time.sleep(25); continue
            raise

def main():
    orders = json.load(open(os.path.join(ROOT,"_orders.json"), encoding="utf-8"))
    out = {d["qid"]: d for d in json.load(open(RAW, encoding="utf-8"))} if os.path.exists(RAW) else {}
    done = set(json.load(open(DONE, encoding="utf-8"))) if os.path.exists(DONE) else set()
    print("已有 %d 条物种，已完成 %d/%d 个目" % (len(out), len(done), len(orders)))
    sys.stdout.flush()

    for i, o in enumerate(orders, 1):
        if o["qid"] in done: continue
        q = """SELECT ?item ?sci ?zh (SAMPLE(?en) AS ?enName) (SAMPLE(?img) AS ?image) WHERE {
          ?item wdt:P171* wd:%s ; wdt:P105 wd:Q7432 ; wdt:P225 ?sci ; wdt:P18 ?img ;
                rdfs:label ?zh . FILTER(LANG(?zh)="zh")
          OPTIONAL { ?item rdfs:label ?en . FILTER(LANG(?en)="en") }
        } GROUP BY ?item ?sci ?zh""" % o["qid"]
        before = len(out)
        try:
            rows = sparql(q)
        except Exception as e:
            print("  [%d/%d] %-26s 失败 %s" % (i,len(orders),o["sci"],str(e)[:40])); sys.stdout.flush()
            continue
        for r in rows:
            qv = r["item"]["value"].rsplit("/",1)[-1]
            if qv in out: continue
            out[qv] = {"qid": qv, "sci": r["sci"]["value"], "zh": r["zh"]["value"],
                       "en": r.get("enName",{}).get("value",""),
                       "img": r.get("image",{}).get("value",""), "cls": o["sci"]}
        done.add(o["qid"])
        json.dump(list(out.values()), open(RAW,"w",encoding="utf-8"), ensure_ascii=False, indent=0)
        json.dump(sorted(done), open(DONE,"w",encoding="utf-8"))
        if len(out) > before or len(rows):
            print("  [%d/%d] %-26s %4d 行 +%d (累计 %d)" % (i,len(orders),o["sci"],len(rows),len(out)-before,len(out)))
            sys.stdout.flush()
        time.sleep(3)
    print("=== 完成：共 %d 条 ===" % len(out))

if __name__ == "__main__":
    main()
