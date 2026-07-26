"use strict";
(function () {
  const DATA = window.FISH_DATA || [];

  // 图片基址：腾讯云 COS 南京区（国内直连，比 jsDelivr 快约 10 倍）。本地开发可改回 "images"
  const IMG_BASE = "https://pic-1302017848.cos.ap-nanjing.myqcloud.com/fish";

  // category metadata: label(zh/en), color var, representative emoji
  const CATS = {
    reef:      { zh:"珊瑚礁",   en:"Coral Reef",   color:"var(--c-reef)",      emoji:"🐠" },
    fresh:     { zh:"淡水观赏", en:"Ornamental",   color:"var(--c-fresh)",     emoji:"🐟" },
    pelagic:   { zh:"大洋洄游", en:"Open Ocean",   color:"var(--c-pelagic)",   emoji:"🦈" },
    deep:      { zh:"深海奇异", en:"Deep Sea",     color:"var(--c-deep)",      emoji:"🎣" },
    temperate: { zh:"温带常见", en:"Temperate",    color:"var(--c-temperate)", emoji:"🐡" },
    special:   { zh:"特殊体型", en:"Odd Bodies",   color:"var(--c-special)",   emoji:"🐙" },
    rare:      { zh:"珍稀活化石", en:"Rare & Relict", color:"var(--c-rare)",    emoji:"🦴" },
    more:      { zh:"世界鱼类图鉴", en:"Field Guide", color:"var(--c-more)",    emoji:"🐟" },
  };
  const CAT_ORDER = ["reef","fresh","pelagic","deep","temperate","special","rare","more"];

  // per-category emoji pools for a little variety on cards
  const EMOJI = {
    reef:["🐠","🐟","🐡"], fresh:["🐟","🐠"], pelagic:["🦈","🐋","🐬"],
    deep:["🎣","🐙","🦑"], temperate:["🐟","🎏"], special:["🐙","🦑","🐡","🐴"],
    rare:["🦴","🐊","🐉"], more:["🐟","🐠","🐡","🎣"],
  };
  function emojiFor(f){ const p = EMOJI[f.cat]||["🐟"]; return p[f.id % p.length]; }

  // ---- i18n ----
  const I18N = {
    zh:{ sub:"种鱼", subtitle:"从珊瑚礁的斑斓到深海的幽光", species:"种", families:"科",
         search:"搜索名称、学名、科…", allFam:"全部科", all:"全部",
         sortDefault:"默认", sortName:"按名称", sortFamily:"按科", random:"随机一鱼",
         noresults:"未找到符合条件的鱼", reset:"重置筛选",
         lFamily:"科", lHabitat:"栖息水域", lSize:"最大体长",
         prev:"← 上一条", next:"下一条 →",
         footer:"1001+ 种真实鱼类 · 从珊瑚礁的斑斓到深海的幽光", langbtn:"EN",
         share:"复制链接", copied:"已复制 ✓", photo:"图片：",
         byFamily:"按科浏览", allFamiliesTitle:"按科浏览", famCount:"种", backToFamilies:"← 所有科" },
    en:{ sub:" Fishes", subtitle:"From reef brilliance to the glow of the deep", species:"species", families:"families",
         search:"Search name, sci. name, family…", allFam:"All families", all:"All",
         sortDefault:"Default", sortName:"By name", sortFamily:"By family", random:"Random fish",
         noresults:"No fish match your filters", reset:"Reset filters",
         lFamily:"Family", lHabitat:"Habitat", lSize:"Max length",
         prev:"← Prev", next:"Next →",
         footer:"1001+ real fish species · from reef brilliance to the deep-sea glow", langbtn:"中",
         share:"Copy link", copied:"Copied ✓", photo:"Photo: ",
         byFamily:"By family", allFamiliesTitle:"Browse by family", famCount:"species", backToFamilies:"← All families" },
  };
  let lang = localStorage.getItem("fish-lang") || "zh";

  // ---- state ----
  let activeCat = "";     // "" = all
  let famFilter = "";
  let sort = "default";
  let query = "";
  let filtered = [];
  // 1001 条全部有图，直接渲染 <img>，加载失败时由 error 监听移除、露出 emoji 占位。
  // 图片署名（Commons 文件名）按需懒加载，不进首屏关键路径。
  let CREDITS = null, creditsPromise = null;
  function loadCredits(){
    if(CREDITS) return Promise.resolve(CREDITS);
    if(!creditsPromise){
      creditsPromise = fetch("credits.json").then(r=>r.ok?r.json():{})
        .then(c=>{ CREDITS = c||{}; return CREDITS; })
        .catch(()=>{ CREDITS = {}; return CREDITS; });
    }
    return creditsPromise;
  }

  // ---- elements ----
  const $ = id => document.getElementById(id);
  const gallery = $("gallery"), catTabs = $("cat-tabs"), famSel = $("family-filter"),
        sortSel = $("sort-filter"), searchIn = $("search"), clearBtn = $("clear-search"),
        noResults = $("no-results");

  function nameOf(f){ return lang==="zh" ? f.name : f.name_en; }
  function subOf(f){ return lang==="zh" ? f.name_en : f.name; }

  // ---- build family dropdown ----
  function buildFamilies(){
    const fams = [...new Set(DATA.map(f=>lang==="zh"?f.family:f.family_en).filter(Boolean))].sort((a,b)=>a.localeCompare(b));
    const cur = famFilter;
    famSel.innerHTML = `<option value="">${I18N[lang].allFam}</option>` +
      fams.map(fm=>`<option value="${fm}">${fm}</option>`).join("");
    famSel.value = cur;
  }

  // ---- category tabs ----
  function buildTabs(){
    const counts = {}; DATA.forEach(f=>counts[f.cat]=(counts[f.cat]||0)+1);
    let html = `<button class="cat-tab ${activeCat===""?"active":""}" data-cat="" style="--tabc:var(--accent)">`+
               `<span class="dot"></span>${I18N[lang].all} <span class="cnt">${DATA.length}</span></button>`;
    html += CAT_ORDER.filter(c=>counts[c]).map(c=>{
      const m=CATS[c];
      return `<button class="cat-tab ${activeCat===c?"active":""}" data-cat="${c}" style="--tabc:${m.color}">`+
             `<span class="dot"></span>${lang==="zh"?m.zh:m.en} <span class="cnt">${counts[c]}</span></button>`;
    }).join("");
    catTabs.innerHTML = html;
    catTabs.querySelectorAll(".cat-tab").forEach(t=>t.onclick=()=>{
      activeCat=t.dataset.cat; buildTabs(); apply();
    });
  }

  // ---- 按科浏览：227 个科用下拉框太难逛，做成可视索引 ----
  let famView = false;
  let FAMS = null;   // [{zh,la,count,repId}]，按数量降序

  function buildFamData(){
    if(FAMS) return FAMS;
    const map = new Map();
    DATA.forEach(f=>{
      if(!f.family) return;
      let e = map.get(f.family);
      if(!e){ e = {zh:f.family, la:f.family_en||"", count:0, repId:f.id}; map.set(f.family, e); }
      e.count++;
    });
    FAMS = [...map.values()].sort((a,b)=> b.count-a.count || a.zh.localeCompare(b.zh,"zh"));
    return FAMS;
  }

  function renderFamilyIndex(){
    const el = $("family-index");
    el.innerHTML = buildFamData().map(fm=>
      `<button class="fam-card" data-fam="${fm.zh.replace(/"/g,"&quot;")}">`+
        `<img class="fam-thumb" src="${IMG_BASE}/${fm.repId}.jpg" alt="" loading="lazy">`+
        `<span class="fam-body">`+
          `<span class="fam-zh">${lang==="zh"?fm.zh:(fm.la||fm.zh)}</span>`+
          `<span class="fam-la">${lang==="zh"?fm.la:fm.zh}</span>`+
          `<span class="fam-cnt">${fm.count} ${I18N[lang].famCount}</span>`+
        `</span></button>`
    ).join("");
  }

  function showFamilyIndex(){
    famView = true; famFilter = ""; famSel.value = "";
    renderFamilyIndex();
    $("family-index").style.display = "grid";
    $("family-header").style.display = "none";
    gallery.style.display = "none";
    noResults.style.display = "none";
    if(sentinel) sentinel.style.display = "none";
    $("family-view-btn").classList.add("active");
  }

  function hideFamilyIndex(){
    famView = false;
    $("family-index").style.display = "none";
    gallery.style.display = "";
    if(sentinel) sentinel.style.display = "";
    $("family-view-btn").classList.remove("active");
  }

  function openFamily(fam){
    const fm = buildFamData().find(x=>x.zh===fam);
    hideFamilyIndex();
    famFilter = lang==="zh" ? fam : (fm && fm.la ? fm.la : fam);
    famSel.value = famFilter;
    const h = $("family-header");
    h.innerHTML = `<button class="fh-back" id="fh-back">${I18N[lang].backToFamilies}</button>`+
      `<h2>${lang==="zh"?fm.zh:(fm.la||fm.zh)}</h2>`+
      `<span class="fh-la">${lang==="zh"?fm.la:fm.zh}</span>`+
      `<span class="fh-cnt">${fm.count} ${I18N[lang].famCount}</span>`;
    h.style.display = "flex";
    $("fh-back").onclick = showFamilyIndex;
    apply();
    window.scrollTo({top:0, behavior: reduceMotion ? "auto" : "smooth"});
  }

  // ---- filtering ----
  function apply(){
    const q = query.trim().toLowerCase();
    filtered = DATA.filter(f=>{
      if(activeCat && f.cat!==activeCat) return false;
      if(famFilter && (lang==="zh"?f.family:f.family_en)!==famFilter) return false;
      if(q){
        const hay = `${f.name} ${f.name_en} ${f.sci} ${f.family} ${f.family_en} ${f.habitat} ${f.habitat_en} ${f.py||""}`.toLowerCase();
        if(!hay.includes(q)) return false;
      }
      return true;
    });
    if(sort==="name") filtered.sort((a,b)=>nameOf(a).localeCompare(nameOf(b),lang==="zh"?"zh":"en"));
    else if(sort==="family") filtered.sort((a,b)=>(lang==="zh"?a.family:a.family_en).localeCompare(lang==="zh"?b.family:b.family_en,lang==="zh"?"zh":"en"));
    else filtered.sort((a,b)=>a.id-b.id);
    render();
  }

  // 增量渲染：1001 条太多，先渲一页，滚动到底再续（配合懒加载图片，保持流畅）
  const PAGE = 120;
  let shownCount = 0, sentinel = null, io = null;

  function cardHTML(f){
    const m=CATS[f.cat];
    const photo = `<img class="card-photo" src="${IMG_BASE}/${f.id}.jpg" alt="" loading="lazy">`;
    return `<article class="card" data-id="${f.id}" style="--cardc:${m.color}" tabindex="0" role="button" aria-label="${nameOf(f)}">`+
      `<div class="card-img"><span class="card-cat">${lang==="zh"?m.zh:m.en}</span>`+
      `<span class="card-emoji">${emojiFor(f)}</span>${photo}</div>`+
      `<div class="card-body">`+
        `<div class="card-name">${nameOf(f)}</div>`+
        `<div class="card-en">${subOf(f)}</div>`+
        `<div class="card-sci">${f.sci}</div>`+
        `<div class="card-meta"><span>${(lang==="zh"?f.family:f.family_en)||""}</span><span>${f.size||""}</span></div>`+
      `</div></article>`;
  }

  function renderMore(){
    const next = filtered.slice(shownCount, shownCount + PAGE);
    if(!next.length) return;
    gallery.insertAdjacentHTML("beforeend", next.map(cardHTML).join(""));
    shownCount += next.length;
  }

  function render(){
    gallery.innerHTML = "";
    shownCount = 0;
    if(!filtered.length){ noResults.style.display="block"; }
    else{ noResults.style.display="none"; renderMore(); }
    if(!sentinel){
      sentinel = document.createElement("div");
      sentinel.style.height = "1px";
      gallery.after(sentinel);
      io = new IntersectionObserver(es=>{ if(es[0].isIntersecting) renderMore(); }, {rootMargin:"800px"});
      io.observe(sentinel);
    }
    $("shown-count").textContent = filtered.length;
  }

  // 图片署名：链回 Wikimedia Commons 原始文件页（CC 图片应署名）
  function renderCredit(id){
    const el = $("modal-credit"); if(!el) return;
    const name = CREDITS && CREDITS[id];
    if(!name){ el.innerHTML = ""; return; }
    const disp = decodeURIComponent(name).replace(/_/g," ");
    el.innerHTML = I18N[lang].photo +
      `<a href="https://commons.wikimedia.org/wiki/File:${encodeURIComponent(name)}" target="_blank" rel="noopener">${disp}</a>` +
      " · Wikimedia Commons";
  }

  // ---- modal ----
  let modalId = null, modalOpener = null;
  function openModal(id){
    const f = DATA.find(x=>x.id===id); if(!f) return;
    if(!$("modal").classList.contains("open")) modalOpener = document.activeElement;
    modalId = id; const m=CATS[f.cat];
    const box = document.querySelector(".modal-box");
    box.style.setProperty("--cardc", m.color);
    $("modal-img").innerHTML = `<img src="${IMG_BASE}/${f.id}.jpg" alt="${nameOf(f)}">`;
    $("modal-img").firstChild.onerror = function(){
      $("modal-img").innerHTML=""; $("modal-img").textContent = emojiFor(f);
    };
    $("modal-credit").innerHTML = "";
    loadCredits().then(()=>{ if(modalId===id) renderCredit(id); });
    $("modal-cat").textContent = lang==="zh"?m.zh:m.en;
    $("modal-name").textContent = nameOf(f);
    $("modal-en").textContent = subOf(f);
    $("modal-sci").textContent = f.sci;
    $("modal-family").textContent = (lang==="zh"?f.family:f.family_en) || "—";
    $("modal-habitat").textContent = (lang==="zh"?f.habitat:f.habitat_en) || "—";
    $("modal-size").textContent = f.size || "—";
    const idx = filtered.findIndex(x=>x.id===id);
    $("modal-num").textContent = idx>=0 ? `${idx+1} / ${filtered.length}` : "";
    $("modal-share").textContent = "⎘ " + I18N[lang].share;
    const wasOpen = $("modal").classList.contains("open");
    $("modal").classList.add("open");
    if(!wasOpen) $("modal-close").focus();   // 打开时焦点移到关闭按钮（可访问性）
    try{ history.replaceState(null,"", "#f"+id); }catch(e){}
    // 预加载上/下一条图片，翻页更顺
    if(idx>=0){
      [filtered[idx-1], filtered[(idx+1)%filtered.length]].forEach(nf=>{
        if(nf && hasImg(nf.id)){ const im=new Image(); im.src=`${IMG_BASE}/${nf.id}.jpg`; }
      });
    }
  }
  function closeModal(){
    $("modal").classList.remove("open"); modalId=null;
    try{ history.replaceState(null,"", location.pathname+location.search); }catch(e){}
    if(modalOpener && modalOpener.focus){ modalOpener.focus(); modalOpener=null; }   // 焦点还给来源卡片
  }
  function step(d){
    const idx = filtered.findIndex(x=>x.id===modalId);
    if(idx<0) return;
    const n = (idx+d+filtered.length)%filtered.length;
    openModal(filtered[n].id);
  }

  // ---- language ----
  function applyLang(){
    const t = I18N[lang];
    // 已选中的科要跟着语言换名，否则筛选值对不上（中文科名 vs 拉丁科名）→ 结果为 0
    if(famFilter){
      const fm = buildFamData().find(x=>x.zh===famFilter || x.la===famFilter);
      if(fm){
        famFilter = lang==="zh" ? fm.zh : (fm.la || fm.zh);
        const h = $("family-header");
        if(h.style.display !== "none"){
          h.innerHTML = `<button class="fh-back" id="fh-back">${t.backToFamilies}</button>`+
            `<h2>${lang==="zh"?fm.zh:(fm.la||fm.zh)}</h2>`+
            `<span class="fh-la">${lang==="zh"?fm.la:fm.zh}</span>`+
            `<span class="fh-cnt">${fm.count} ${t.famCount}</span>`;
          $("fh-back").onclick = showFamilyIndex;
        }
      }
    }
    document.documentElement.lang = lang==="zh"?"zh-CN":"en";
    $("t-sub").textContent = t.sub;
    $("t-subtitle").textContent = t.subtitle;
    $("t-species").textContent = t.species;
    $("t-families").textContent = t.families;
    searchIn.placeholder = t.search;
    sortSel.options[0].text=t.sortDefault; sortSel.options[1].text=t.sortName; sortSel.options[2].text=t.sortFamily;
    $("random-btn").textContent = t.random;
    document.getElementById("t-noresults").textContent = t.noresults;
    $("reset-btn").textContent = t.reset;
    $("l-family").textContent=t.lFamily; $("l-habitat").textContent=t.lHabitat; $("l-size").textContent=t.lSize;
    $("prev-fish").textContent=t.prev; $("next-fish").textContent=t.next;
    $("modal-share").textContent="⎘ "+t.share;
    $("family-view-btn").textContent=t.byFamily;
    if(famView) renderFamilyIndex();
    document.getElementById("t-footer").textContent=t.footer;
    $("lang-toggle").textContent=t.langbtn;
    buildFamilies(); buildTabs(); apply();
  }

  // ---- events ----
  gallery.addEventListener("click",e=>{ const c=e.target.closest(".card"); if(c) openModal(+c.dataset.id); });
  gallery.addEventListener("keydown",e=>{
    if(e.key!=="Enter"&&e.key!==" ") return;
    const c=e.target.closest(".card"); if(c){ e.preventDefault(); openModal(+c.dataset.id); }
  });
  searchIn.addEventListener("input",()=>{ query=searchIn.value; clearBtn.style.display=query?"block":"none";
    if(famView && query){ hideFamilyIndex(); $("family-header").style.display="none"; famFilter=""; famSel.value=""; }
    apply(); });
  clearBtn.onclick=()=>{ searchIn.value=""; query=""; clearBtn.style.display="none"; apply(); };
  famSel.onchange=()=>{ famFilter=famSel.value; if(famView) hideFamilyIndex(); $("family-header").style.display="none"; apply(); };
  $("family-view-btn").onclick=()=>{ famView ? (hideFamilyIndex(), $("family-header").style.display="none", apply()) : showFamilyIndex(); };
  $("family-index").addEventListener("click", e=>{
    const c = e.target.closest(".fam-card"); if(c) openFamily(c.dataset.fam);
  });
  sortSel.onchange=()=>{ sort=sortSel.value; apply(); };
  $("random-btn").onclick=()=>{ if(filtered.length) openModal(filtered[Math.floor(Math.random()*filtered.length)].id); };
  $("modal-close").onclick=closeModal;
  $("modal").onclick=e=>{ if(e.target===$("modal")) closeModal(); };
  $("prev-fish").onclick=()=>step(-1);
  $("next-fish").onclick=()=>step(1);
  $("modal-share").onclick=()=>{
    if(!modalId) return;
    const link = location.origin + location.pathname + "#f" + modalId;
    const done=()=>{ const b=$("modal-share"); b.textContent="⎘ "+I18N[lang].copied;
      setTimeout(()=>{ b.textContent="⎘ "+I18N[lang].share; }, 1500); };
    if(navigator.clipboard&&navigator.clipboard.writeText){ navigator.clipboard.writeText(link).then(done,done); }
    else{ const t=document.createElement("textarea"); t.value=link; document.body.appendChild(t); t.select();
      try{document.execCommand("copy");}catch(e){} t.remove(); done(); }
  };
  $("reset-btn").onclick=()=>{ activeCat="";famFilter="";query="";searchIn.value="";clearBtn.style.display="none";
    if(famView) hideFamilyIndex(); $("family-header").style.display="none";
    buildTabs();buildFamilies();apply(); };
  $("lang-toggle").onclick=()=>{ lang=lang==="zh"?"en":"zh"; localStorage.setItem("fish-lang",lang); applyLang(); };
  document.addEventListener("keydown",e=>{
    const modalOpen = $("modal").classList.contains("open");
    if(e.key==="Escape"){ closeModal(); return; }
    if(modalOpen){
      if(e.key==="ArrowLeft") step(-1);
      else if(e.key==="ArrowRight") step(1);
      else if(e.key==="Tab"){   // 焦点困在弹窗内（可访问性）
        const foc=[...document.querySelectorAll(".modal-box button")].filter(b=>b.offsetParent!==null);
        if(foc.length){
          const first=foc[0], last=foc[foc.length-1];
          if(e.shiftKey && document.activeElement===first){ e.preventDefault(); last.focus(); }
          else if(!e.shiftKey && document.activeElement===last){ e.preventDefault(); first.focus(); }
        }
      }
      return;
    }
    if(e.key==="/"&&document.activeElement!==searchIn){ e.preventDefault(); searchIn.focus(); }
    else if(e.key.toLowerCase()==="r"&&document.activeElement!==searchIn){ $("random-btn").click(); }
  });

  // 从 URL 恢复状态：?q= 预填搜索；#f<id> 直接打开某条鱼（可分享的深链）
  function applyUrlState(){
    const params = new URLSearchParams(location.search);
    const q = params.get("q");
    if(q){ searchIn.value=q; query=q; clearBtn.style.display="block"; apply(); }
    const m = location.hash.match(/^#f(\d+)$/);
    if(m){ const id=+m[1]; if(DATA.some(f=>f.id===id)) openModal(id); }
  }

  // 回到顶部
  const toTop = $("to-top");
  window.addEventListener("scroll", ()=>{ toTop.classList.toggle("show", window.scrollY > 600); }, {passive:true});
  const reduceMotion = window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches;
  toTop.onclick = ()=> window.scrollTo({top:0, behavior: reduceMotion ? "auto" : "smooth"});

  // 卡片图加载失败时移除，露出 emoji 占位（error 不冒泡，用捕获）
  gallery.addEventListener("error", e=>{
    if(e.target && e.target.classList && e.target.classList.contains("card-photo")) e.target.remove();
  }, true);

  // ---- init ----
  $("family-count").textContent = new Set(DATA.map(f=>f.family).filter(Boolean)).size;
  applyLang();
  applyUrlState();
})();
