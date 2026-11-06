// 复习规则（改规则只改这个文件）
//
// 新题：第一次就做对 -> 已掌握，以后不再出现（除非手动复习）
//       第一次做错   -> 进错题集，连对清零，1 星期后出现
// 错题集里的题（到期那天做）：
//       做对 -> 连对 +1；下次间隔 = (连对+1) 星期；连对满 10 -> 毕业，移出错题集
//       做错 -> 连对清零，1 星期后再出现
// 手动复习（不是到期那天）：做对不计入连对；做错照样进错题集、清零
(function (root) {
  'use strict';
  var MAX_STREAK = 10;
  var WEEK = 7;

  function pad(n) { return (n < 10 ? '0' : '') + n; }
  function todayStr(d) {
    d = d || new Date();
    return d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate());
  }
  function addDays(s, n) {
    var p = s.split('-').map(Number);
    return todayStr(new Date(p[0], p[1] - 1, p[2] + n));
  }
  function blank() { return { status: 'new', streak: 0, due: null, wrongCount: 0, history: [] }; }
  function clone(r) {
    var c = Object.assign(blank(), r || {});
    c.history = (c.history || []).slice();
    return c;
  }
  function markWrong(r, today) {
    r.status = 'learning';
    r.streak = 0;
    r.wrongCount++;
    r.due = addDays(today, WEEK);
  }

  // mode: 'daily' = 今日练习（到期的题）；'free' = 手动复习
  function applyAnswer(rec, correct, today, mode) {
    var r = clone(rec);
    r.history.push({ date: today, correct: !!correct, mode: mode });
    if (!correct) { markWrong(r, today); return r; }
    if (r.status === 'new') { r.status = 'mastered'; r.due = null; return r; }
    if (r.status === 'learning' && mode === 'daily') {
      r.streak++;
      if (r.streak >= MAX_STREAK) { r.status = 'graduated'; r.due = null; }
      else { r.due = addDays(today, WEEK * (r.streak + 1)); }
    }
    return r;
  }

  function isDue(r, today) { return !!(r && r.status === 'learning' && r.due && r.due <= today); }

  // 今日队列：先到期的错题，再今天解锁的新题
  function dailyQueue(questions, records, today) {
    var reviews = [], news = [];
    questions.forEach(function (q) {
      if (q.date > today) return;
      var r = records[q.id];
      if (!r || r.status === 'new') news.push(q.id);
      else if (isDue(r, today)) reviews.push(q.id);
    });
    reviews.sort(function (a, b) { return records[a].due < records[b].due ? -1 : 1; });
    return reviews.concat(news);
  }

  var api = {
    MAX_STREAK: MAX_STREAK, WEEK: WEEK,
    todayStr: todayStr, addDays: addDays, blank: blank,
    applyAnswer: applyAnswer, isDue: isDue, dailyQueue: dailyQueue
  };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.SRS = api;
})(this);
