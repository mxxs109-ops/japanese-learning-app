// 手写笔记页的日语朗读（所有 PageNNN.html 共用）
//
//   要读的元素加 data-say="段落id"；同一个 id 的多个元素按页面顺序合成一段（比如两行题干说明）。
//   元素里这些不读：.note（中文笔记）、.nosay（A1： 这种标签）、<rt>（注音）。.under（＿＿ 下划线）念成「かせん」。
//   断词：.s（词间空格）、.gap（括号里的空白）、。、 之后；选项编号 .num / .circ 单独一词，读成 いち/に/さん/よん。
//
//   语音是事先用 VOICEVOX 生成好的（tools/make_notes_audio.py），存在同页的 audio/：
//     audio/manifest.js  = window.SAY_DATA（每段每个音色对应哪个音频 + 每个词从第几秒开始）
//     audio/<缓存号>.ogg = 音频；缓存号由「文字 + 音色 + 引擎版本」算出，文字没改就不会重新生成
//   页面上：网址加 ?sayplan=1 会把「要读的内容」写进 <pre id="say-plan">，生成脚本靠它拿到和页面完全一致的分词。
(function () {
  'use strict';
  var NUM = { '1': 'いち', '2': 'に', '3': 'さん', '4': 'よん', '5': 'ご', '6': 'ろく' };
  var SKIP_CLASS = ['note', 'nosay'];
  var LETTER = /[0-9A-Za-z぀-ヿ㐀-鿿０-９Ａ-ｚ]/;

  function hasClass(el, list) {
    if (!el.classList) return false;
    for (var i = 0; i < list.length; i++) if (el.classList.contains(list[i])) return true;
    return false;
  }

  // ---------- 分段 + 分词 ----------
  function buildPlan() {
    var segs = [], byId = {};
    var els = document.querySelectorAll('[data-say]');
    for (var i = 0; i < els.length; i++) {
      var el = els[i], id = el.getAttribute('data-say'), seg = byId[id];
      if (!seg) { seg = byId[id] = { id: id, chunks: [], cur: null, els: [] }; segs.push(seg); }
      close(seg);                       // 换一个元素（换行）= 换一个词
      if (seg.els.length) seg.joinNext = true;   // 但念的时候和上一行连着念（「いち｜ばん」跨行）
      seg.els.push(el);
      walk(el, seg);
      close(seg);
    }
    segs.forEach(function (s) {
      s.chunks.forEach(function (c) {
        // 念的文字 = c.alt（带注音的汉字换成注音，比如 <ruby>今<rt>いま</rt></ruby> 念 いま）；高亮仍按页面上的汉字
        c.say = c.sayAs ? c.sayAs : c.num ? (NUM[c.text.replace(/[^0-9]/g, '')] || c.text) + '、' : c.alt.replace(/[＿_]/g, '');
        // 「1・2・3・4」引擎会念成「いってん、に、さんてん…」（・当小数点），改成 いち、に、さん、よん
        c.say = c.say.replace(/[0-9](?:・[0-9])+/g, function (m) {
          return m.split('・').map(function (d) { return NUM[d] || d; }).join('、');
        });
      });
    });
    return segs;
  }
  function newChunk(seg, num) {
    seg.cur = { text: '', alt: '', pieces: [], num: !!num, join: !!seg.joinNext };
    seg.joinNext = false;
    return seg.cur;
  }
  function close(seg) {
    var c = seg.cur; seg.cur = null;
    if (!c || !c.text) return;
    var prev = seg.chunks[seg.chunks.length - 1];
    // 只有标点（（ ）。・）的不单独成词，并到前一个词里
    if (!c.sayAs && !LETTER.test(c.text) && prev && !prev.num) {
      prev.text += c.text; prev.alt += c.alt; prev.pieces = prev.pieces.concat(c.pieces); return;
    }
    seg.chunks.push(c);
  }
  function addChar(seg, node, k, ch, noAlt) {
    var c = seg.cur || newChunk(seg);
    var last = c.pieces[c.pieces.length - 1];
    if (last && last[0] === node && last[2] === k) last[2] = k + 1;
    else c.pieces.push([node, k, k + 1]);
    c.text += ch;
    if (!noAlt) c.alt += ch;
  }
  // <ruby>漢字<rt>かな</rt></ruby>：高亮标在汉字上，念的时候用注音
  function walkRuby(rb, seg) {
    // data-yomi = 只给朗读用的读法（引擎把注音念错时用，比如「はいる」被当成助词「は」+「いる」→ 写 data-yomi="ハイ"）
    var rt = rb.querySelector('rt');
    var reading = rb.getAttribute('data-yomi') || (rt ? rt.textContent.replace(/\s/g, '') : '');
    var any = false;
    for (var ch = rb.firstChild; ch; ch = ch.nextSibling) {
      if (ch.nodeType !== 3) continue;
      var s = ch.nodeValue;
      for (var k = 0; k < s.length; k++) {
        if (/\s/.test(s[k])) continue;
        addChar(seg, ch, k, s[k], !!reading); any = true;
      }
    }
    if (any && reading) seg.cur.alt += reading;
  }
  function walk(node, seg) {
    for (var ch = node.firstChild; ch; ch = ch.nextSibling) {
      if (ch.nodeType === 3) {
        var s = ch.nodeValue;
        for (var k = 0; k < s.length; k++) {
          var x = s[k];
          if (/\s/.test(x) && x !== '　') continue;      // HTML 排版用的空白不算
          if (x === '　') { close(seg); continue; }
          addChar(seg, ch, k, x);
          if (x === '。' || x === '、') close(seg);
        }
      } else if (ch.nodeType === 1) {
        // ＿＿ 下划线：念成「かせん」（下線），高亮时照样标出这段下划线
        if (hasClass(ch, ['under'])) { close(seg); newChunk(seg).sayAs = 'かせん'; walk(ch, seg); close(seg); continue; }
        if (ch.tagName === 'RT' || ch.tagName === 'RP' || hasClass(ch, SKIP_CLASS)) continue;
        if (ch.tagName === 'RUBY') { walkRuby(ch, seg); continue; }
        if (hasClass(ch, ['s', 'gap'])) { close(seg); continue; }
        if (hasClass(ch, ['num', 'circ'])) { close(seg); newChunk(seg, true); walk(ch, seg); close(seg); continue; }
        if (hasClass(ch, ['opt'])) { close(seg); walk(ch, seg); close(seg); continue; }
        walk(ch, seg);
      }
    }
  }

  var PLAN = buildPlan();

  // 给生成脚本用：?sayplan=1 时把要读的内容写出来
  // （页面的主题切换会用 replaceState 改写网址，所以看导航时的原始网址）
  var navUrl = '';
  try { navUrl = performance.getEntriesByType('navigation')[0].name; } catch (e) {}
  if (/[?&]sayplan=1/.test(location.search + ' ' + navUrl)) {
    var pre = document.createElement('pre');
    pre.id = 'say-plan';
    pre.textContent = JSON.stringify(PLAN.map(function (s) {
      return { id: s.id, chunks: s.chunks.map(function (c) { return { t: c.text, s: c.say, j: c.join ? 1 : 0 }; }) };
    }));
    document.body.appendChild(pre);
    return;
  }

  // ---------- 播放 ----------
  var DATA = window.SAY_DATA || null;
  var hl = window.CSS && CSS.highlights && window.Highlight;
  var audio = new Audio();
  try { audio.preservesPitch = true; } catch (e) {}
  var st = { seg: -1, chunk: -1, playing: false, raf: 0 };
  var ui = {};

  function load(key, fallback) { try { var v = localStorage.getItem('say-' + key); return v == null ? fallback : v; } catch (e) { return fallback; } }
  function keep(key, v) { try { localStorage.setItem('say-' + key, v); } catch (e) {} }

  function voiceId() { return ui.voice ? ui.voice.value : ''; }
  function voiceName() {
    if (!DATA) return '';
    for (var i = 0; i < DATA.voices.length; i++) if (String(DATA.voices[i].id) === voiceId()) return DATA.voices[i].name;
    return '';
  }
  function entry(i) {
    var s = DATA && DATA.segs[PLAN[i].id];
    if (!s || s.text !== PLAN[i].chunks.map(function (c) { return c.say; }).join('')) return null;   // 文字改了还没重新生成
    var key = s.v[voiceId()];
    return key ? { key: key, starts: DATA.keys[key].c } : null;
  }

  function rangeOf(c) {
    var r = document.createRange(), a = c.pieces[0], b = c.pieces[c.pieces.length - 1];
    r.setStart(a[0], a[1]); r.setEnd(b[0], b[2]);
    return r;
  }
  function paint() {
    if (!hl) return;
    CSS.highlights.delete('say-word'); CSS.highlights.delete('say-seg');
    if (st.seg < 0) return;
    var seg = PLAN[st.seg];
    var all = new Highlight();
    seg.chunks.forEach(function (c) { all.add(rangeOf(c)); });
    CSS.highlights.set('say-seg', all);
    if (st.chunk >= 0 && seg.chunks[st.chunk]) CSS.highlights.set('say-word', new Highlight(rangeOf(seg.chunks[st.chunk])));
  }

  function tick() {
    st.raf = 0;
    if (st.seg < 0) return;
    var e = entry(st.seg);
    if (e) {
      var t = audio.currentTime, k = -1;
      for (var i = 0; i < e.starts.length; i++) if (t + 0.02 >= e.starts[i]) k = i;
      if (k !== st.chunk) { st.chunk = k; paint(); }
    }
    if (st.playing) st.raf = requestAnimationFrame(tick);
  }

  function playSeg(i) {
    // 跳过没有语音的段
    while (i < PLAN.length && !entry(i)) i++;
    if (i >= PLAN.length) {
      var chain = st.playing && !st.single;
      stop();
      if (chain) tell({ say: 'done' });       // 整页读完 → 书翻到下一页接着读
      return;
    }
    st.seg = i; st.chunk = -1; st.playing = true;
    var first = PLAN[i].els[0];
    var r = first.getBoundingClientRect();
    if (r.top < 60 || r.bottom > window.innerHeight - 60) first.scrollIntoView({ block: 'center', behavior: 'smooth' });
    audio.src = 'audio/' + entry(i).key + '.ogg';
    audio.playbackRate = Number(ui.speed.value) || 1;
    audio.play().catch(function () {});
    paint(); refresh();
    if (!st.raf) st.raf = requestAnimationFrame(tick);
  }
  audio.addEventListener('ended', function () {
    if (!st.playing) return;
    if (st.single) { stop(); return; }
    setTimeout(function () { if (st.playing) playSeg(st.seg + 1); }, 350);
  });

  function stop() {
    st.playing = false; st.seg = -1; st.chunk = -1; st.single = false;
    audio.pause(); paint(); refresh();
  }
  function togglePause() {
    if (st.seg < 0) { st.single = false; playSeg(0); return; }
    if (st.playing) { st.playing = false; audio.pause(); }
    else { st.playing = true; audio.play().catch(function () {}); if (!st.raf) st.raf = requestAnimationFrame(tick); }
    refresh();
  }
  function refresh() {
    tell({ say: 'state', playing: st.playing, active: st.seg >= 0, hasAudio: !!DATA,
           voices: DATA ? DATA.voices : [], voice: voiceId(), credit: DATA ? 'VOICEVOX:' + voiceName() : '' });
    if (!ui.play) return;
    ui.play.textContent = st.playing ? '⏸ 暂停' : (st.seg >= 0 ? '▶ 继续' : '▶ 全部朗读');
    ui.stop.disabled = st.seg < 0;
    ui.credit.textContent = DATA ? '音声：VOICEVOX:' + voiceName() : '还没有生成语音（tools/make_notes_audio.py）';
  }

  // ---------- 面板 ----------
  var CSS_TEXT =
    '::highlight(say-seg){background-color:rgba(255,214,102,.28)}' +
    '::highlight(say-word){background-color:#ffd24d}' +
    '.say-able{cursor:pointer}' +
    '.say-panel{align-items:center;gap:2px}' +
    '.say-panel button[disabled]{opacity:.35;cursor:default}' +
    '.say-panel select{border:0;background:#f1f1f1;font:inherit;font-size:14px;padding:7px 8px;border-radius:999px;margin-left:4px;cursor:pointer}' +
    '.say-credit{font-size:12px;color:#555;background:#fff;border-radius:8px;padding:4px 10px;box-shadow:0 2px 10px rgba(0,0,0,.12)}' +
    '@media print{.say-panel,.say-credit{display:none!important}}';

  function panel() {
    var box = document.querySelector('.switch');
    if (!box) return;
    var style = document.createElement('style');
    style.textContent = CSS_TEXT;
    document.head.appendChild(style);
    var seg = document.createElement('div');
    seg.className = 'seg say-panel';
    seg.innerHTML =
      '<button class="say-play">▶ 全部朗读</button><button class="say-stop">⏹ 停止</button>' +
      '<select class="say-voice" title="音色"></select>' +
      '<select class="say-speed" title="语速">' +
      ['0.6', '0.75', '0.9', '1', '1.15', '1.3'].map(function (v) { return '<option value="' + v + '">' + v + '×</option>'; }).join('') +
      '</select>';
    box.appendChild(seg);
    var credit = document.createElement('div');
    credit.className = 'say-credit';
    box.appendChild(credit);
    ui = { play: seg.querySelector('.say-play'), stop: seg.querySelector('.say-stop'),
           voice: seg.querySelector('.say-voice'), speed: seg.querySelector('.say-speed'), credit: credit };
    if (DATA) DATA.voices.forEach(function (v) {
      var o = document.createElement('option'); o.value = v.id; o.textContent = v.name; ui.voice.appendChild(o);
    });
    else { ui.play.disabled = true; ui.voice.disabled = true; ui.speed.disabled = true; }
    var savedVoice = load('voice', DATA && DATA.voices.length ? String(DATA.voices[0].id) : '');
    if (ui.voice.querySelector('option[value="' + savedVoice + '"]')) ui.voice.value = savedVoice;
    ui.speed.value = load('speed', '1');
    ui.play.onclick = togglePause;
    ui.stop.onclick = stop;
    ui.voice.onchange = function () {
      keep('voice', ui.voice.value);
      if (st.seg >= 0) { var i = st.seg, single = st.single; playSeg(i); st.single = single; }
      refresh();
    };
    ui.speed.onchange = function () { keep('speed', ui.speed.value); audio.playbackRate = Number(ui.speed.value) || 1; };
    // 点页面上任何一段要读的文字：只读这一段
    PLAN.forEach(function (s, i) {
      s.els.forEach(function (el) {
        el.classList.add('say-able');
        el.addEventListener('click', function () { if (!DATA) return; playSeg(i); st.single = true; });
      });
    });
    refresh();
  }
  // ---------- 装在书里（book.html 用 iframe 打开 PageNNN.html?embed=1）----------
  var EMBED = /[?&]embed=1/.test(location.search + ' ' + navUrl) && window.parent !== window;
  // ?shot=1：给 tools/make_notes_pdf.py 截翻页用的图（只要纸面，不要按钮和灰底）
  var SHOT = /[?&]shot=1/.test(location.search + ' ' + navUrl);
  function tell(msg) { if (EMBED) try { window.parent.postMessage(msg, '*'); } catch (e) {} }
  function embedSetup() {
    if (!EMBED && !SHOT) return;
    var s = document.createElement('style');
    s.textContent = 'html,body{background:transparent!important;margin:0!important;padding:0!important;overflow:hidden}' +
      '.page{margin:0!important;box-shadow:none!important}.switch{display:none!important}';
    document.head.appendChild(s);
    // 纸宽固定 210mm = 793.7px（不用 offsetWidth：缩放后再量会量到缩放过的值，越缩越错）
    var PAGE_PX = 210 * 96 / 25.4;
    var lastW = 0;
    function fit() { if (window.innerWidth !== lastW) { lastW = window.innerWidth; document.body.style.zoom = lastW / PAGE_PX; } }
    // 书页大小由翻页库改，resize 事件不一定到得了 iframe 里 → 定时对一下
    fit(); window.addEventListener('resize', fit); setInterval(fit, 300);
    if (!EMBED) return;
    function click(sel) { var b = document.querySelector(sel); if (b) b.click(); }
    window.addEventListener('message', function (e) {
      var m = e.data || {};
      if (m.say === 'theme') click('.switch button[data-t="' + m.v + '"]');
      else if (m.say === 'clean') click('.switch button[data-c="' + m.v + '"]');
      else if (m.say === 'play') { st.single = false; playSeg(0); }
      else if (m.say === 'toggle') togglePause();
      else if (m.say === 'stop') stop();
      else if (m.say === 'voice' && ui.voice && ui.voice.querySelector('option[value="' + m.v + '"]')) { ui.voice.value = m.v; ui.voice.onchange(); }
      else if (m.say === 'speed' && ui.speed) { ui.speed.value = m.v; ui.speed.onchange(); }
      else if (m.say === 'hello') refresh();
    });
  }
  function start() { panel(); embedSetup(); refresh(); }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start); else start();

  // 给外层（翻书页面）和自动测试用
  window.SAY = {
    plan: PLAN, audio: audio, state: st,
    play: function (i) { playSeg(i || 0); st.single = false; },
    toggle: togglePause, stop: stop,
    show: function (i, t) {             // 不出声，直接把第 i 段第 t 秒的高亮画出来（测试用）
      st.seg = i; var e = entry(i), k = -1;
      if (e) for (var j = 0; j < e.starts.length; j++) if (t + 0.02 >= e.starts[j]) k = j;
      st.chunk = k; paint();
      return k >= 0 ? PLAN[i].chunks[k].text : null;
    }
  };
})();
