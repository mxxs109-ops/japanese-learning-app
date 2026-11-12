// 检查 questions.js 里的 TEACH（教学模式注音）：
//   1) 去掉注音后必须和原题逐字一样
//   2) 列出没有注音的汉字（应该为 0）
//   3) 列出没有标来源词的片假名词（假词选项可以没有）
// 用法：node tools/check_teach.js [questions.js 路径]
const path = require('path');
const file = path.resolve(process.argv[2] || path.join(__dirname, '..', 'questions.js'));
global.window = {};
require(file);
const Q = window.QUESTIONS, T = window.TEACH || {};
const strip = s => s.replace(/\{([^|{}]+)\|([^|{}]+)\}/g, '$1');
const bare = s => strip(s).replace(/\{([^|{}]+)\|([^|{}]+)\}/g, '');
let fail = 0, warn = 0;

for (const id of Object.keys(T)) {
  const q = Q.find(x => x.id === id);
  if (!q) { console.log('[FAIL] TEACH has unknown id', id); fail++; continue; }
  const t = T[id];
  const pairs = [];
  if (t.instruction != null) pairs.push(['instruction', t.instruction, q.instruction]);
  if (t.sentence != null) pairs.push(['sentence', t.sentence, q.sentence]);
  if (t.options != null) {
    if (t.options.length !== q.options.length) { console.log('[FAIL]', id, 'options length'); fail++; }
    t.options.forEach((o, i) => pairs.push(['option' + (i + 1), o, q.options[i]]));
  }
  // expl：解析里某几行的注音版（听力原文）。每行去掉注音后必须正好是解析里的一行，且不许有没注音的汉字
  if (t.expl != null) {
    if (!Array.isArray(t.expl)) { console.log('[FAIL]', id, 'expl must be an array'); fail++; }
    else t.expl.forEach((s, i) => {
      if (!q.explanation.includes(strip(s))) { console.log('[FAIL]', id, 'expl' + (i + 1), 'matches no explanation line:', strip(s)); fail++; }
      const k = s.replace(/\{([^|{}]+)\|([^|{}]+)\}/g, '').match(/[一-鿿々]/g);
      if (k) { console.log('[FAIL]', id, 'expl' + (i + 1), 'kanji without reading:', k.join('')); fail++; }
    });
  }
  for (const [name, tv, qv] of pairs) {
    if (strip(tv) !== strip(qv)) { console.log('[FAIL]', id, name, 'text differs:\n   teach:', strip(tv), '\n   orig :', strip(qv)); fail++; }
  }
}

// coverage: every field shown in teaching mode
for (const q of Q) {
  const t = T[q.id] || {};
  const fields = [['instruction', t.instruction || q.instruction], ['sentence', t.sentence || q.sentence]];
  q.options.forEach((o, i) => fields.push(['option' + (i + 1), (t.options && t.options[i]) || o]));
  for (const [name, s] of fields) {
    const outside = s.replace(/\{([^|{}]+)\|([^|{}]+)\}/g, '');
    const kanji = outside.match(/[一-鿿々]/g);
    if (kanji) { console.log('[FAIL]', q.id, name, 'kanji without reading:', kanji.join('')); fail++; }
    const kata = outside.match(/[ァ-ヺー]{2,}/g);
    if (kata) { console.log('[INFO]', q.id, name, 'katakana without source word:', kata.join(' ')); warn++; }
  }
}
console.log(fail ? '[FAIL] ' + fail + ' problem(s)' : '[OK] teach check passed', '| katakana notes:', warn);
process.exit(fail ? 1 : 0);
