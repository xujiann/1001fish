#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从 Wikidata 采集"有中文名 + 有图片"的真实鱼类物种，作为 239 精选之外的补齐来源。
输出 _harvest_raw.json（qid, sci, zh, en, img）。不改 fish.js，仅生成原料。
覆盖：Actinopterygii(辐鳍鱼 Q127595)、Chondrichthyes(软骨鱼 Q83367)、
      Agnatha 无颌类(七鳃鳗 Q47698 等) 及 肉鳍鱼(Q129604)。
"""
import json, sys, time, urllib.parse, urllib.request, urllib.error

UA = "1001fish/1.0 (educational bilingual fish gallery; popstudy@gmail.com)"
ENDPOINT = "https://query.wikidata.org/sparql"
CLASSES = {
    "Actinopterygii": "Q127595",
    "Chondrichthyes": "Q83367",
    "Sarcopterygii":  "Q129604",
    "Agnatha":        "Q599909",
}

def sparql(query, tries=8):
    url = ENDPOINT + "?" + urllib.parse.urlencode({"query": query, "format": "json"})
    for attempt in range(tries):
        req = urllib.request.Request(url, headers={
            "User-Agent": UA, "Accept": "application/sparql-results+json"})
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                return json.loads(r.read().decode("utf-8"))["results"]["bindings"]
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < tries - 1:
                print("    429, waiting 65s (attempt %d)..." % (attempt + 1)); sys.stdout.flush()
                time.sleep(65); continue
            raise

def harvest_class(qid):
    q = """
    SELECT ?item ?sci ?zh (SAMPLE(?en) AS ?enName) (SAMPLE(?img) AS ?image) WHERE {
      ?item wdt:P171* wd:%s ;
            wdt:P105 wd:Q7432 ;
            wdt:P225 ?sci ;
            wdt:P18 ?img ;
            rdfs:label ?zh . FILTER(LANG(?zh)="zh")
      OPTIONAL { ?item rdfs:label ?en . FILTER(LANG(?en)="en") }
    } GROUP BY ?item ?sci ?zh
    """ % qid
    return sparql(q)

def main():
    out = {}
    for name, qid in CLASSES.items():
        try:
            rows = harvest_class(qid)
            print("%-16s %5d rows" % (name, len(rows)))
        except Exception as e:
            print("%-16s ERROR %s" % (name, e))
            continue
        for r in rows:
            qidv = r["item"]["value"].rsplit("/", 1)[-1]
            if qidv in out:
                continue
            out[qidv] = {
                "qid": qidv,
                "sci": r["sci"]["value"],
                "zh": r["zh"]["value"],
                "en": r.get("enName", {}).get("value", ""),
                "img": r.get("image", {}).get("value", ""),
                "cls": name,
            }
        json.dump(list(out.values()), open("_harvest_raw.json", "w", encoding="utf-8"),
                  ensure_ascii=False, indent=0)   # 每类完成即落盘
        time.sleep(65)   # 尊重 1 req/min 限流
    json.dump(list(out.values()), open("_harvest_raw.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=0)
    print("=== total unique: %d -> _harvest_raw.json ===" % len(out))

if __name__ == "__main__":
    main()
