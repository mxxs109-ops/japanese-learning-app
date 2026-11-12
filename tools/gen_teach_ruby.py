# -*- coding: utf-8 -*-
"""
教学模式「注音」补全：给解析里的日语、题库列表的 brief、题目分类名（section）、试卷分区名自动加注音，
生成 questions.js 末尾「自动注音」那一块（两行标记之间整块覆盖），并输出逐行对照表供人工核对。

用法（janome 装在别处时用 JANOME_PATH 指过去）：
  python tools/gen_teach_ruby.py            # 生成 + 写回 questions.js + 写对照表 docs/teach_ruby_review.txt
  python tools/gen_teach_ruby.py --check    # 只检查：块是不是最新的（不写文件）

规则：
- 只注汉字，读音用平假名；{漢字|かな}，和 TEACH 其它字段同一种写法
- 解析行：「」里的内容一定当日语；「→」左边、不含中文虚词的段落当整段日语；其余只注「连着假名的那一串」
- 读错 / 中文字被误认成日语 → 写进下面的 WORD / LINE / SKIP 修正表，再重新生成。手写的 TEACH 字段优先，不会被覆盖
"""
import io, json, os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QJS = os.path.join(ROOT, 'questions.js')
REVIEW = os.path.join(ROOT, 'docs', 'teach_ruby_review.txt')
if os.environ.get('JANOME_PATH'):
    sys.path.insert(0, os.environ['JANOME_PATH'])
from janome.tokenizer import Tokenizer  # noqa: E402

BEGIN = '// ==== 自动注音 BEGIN（tools/gen_teach_ruby.py 生成，别手改；改读音去改脚本里的修正表）===='
END = '// ==== 自动注音 END ===='

# ---------- 人工修正表（逐行核对后填） ----------
# 词 → 读音：分词结果里出现这个词就用这个读音（整词注一个 ruby）
WORD = {
    '聴解': 'ちょうかい',
    '類義': 'るいぎ',
    '語形成': 'ごけいせい',
    '中文': 'ちゅうぶん',
    '通って': 'かよって',   # janome 读成 とおって；这道题考的就是 かよって
}
# 整行修正：原行（逐字） → 注音版（去掉注音后必须和原行一样）
LINE = {
    # 纯汉字的日语粗体
    '「しゅうしゅう」写成汉字是 **収集**，意思是"收集、回收"。「ごみの収集日」就是"垃圾回收日"，整句意思是"今天是收垃圾的日子吗？"':
    '「しゅうしゅう」写成汉字是 **{収集|しゅうしゅう}**，意思是"收集、回收"。「ごみの{収集|しゅうしゅう}{日|び}」就是"垃圾回收日"，整句意思是"今天是收垃圾的日子吗？"',
    # 括号里单独一个「名」
    '完整句子是：あの映画の最後は（名）場面として知られている。意思是"那部电影的结尾作为经典名场面而广为人知"。':
    '完整句子是：あの{映画|えいが}の{最後|さいご}は（{名|めい}）{場面|ばめん}として{知|し}られている。意思是"那部电影的结尾作为经典名场面而广为人知"。',
}
# 中文里的汉字被误认成日语：(原行里的一小段, 要跳过的那个字) —— 这一段里的这个字不注音
SKIP = [
    ('日元', '日'), ('日元', '元'),
]

KANJI = re.compile(r'[一-鿿々〆ヶ]')
KANA = re.compile(r'[ぁ-ゟ゠-ヿ]')
# 只在中文里出现、日语正文里基本不会出现的字：段落里有这些 = 中文段落
#   （会 / 都 / 与 / 被 / 后 日语里常用，不能放进来：放进来会把「会社に通う」整句漏掉）
CN = set('是了这们说读吗呢么还没个为对从就也把种词句译选项过时给让很什啊吧哪儿该样边别里听戴和')

# 「」里只有一个汉字（在讲这个字本身）→ 读音按这一行在讲的那个读法：(题目 id, 行号, 字) → 读音；没写的用 QK 默认
QK = {
    '新': 'しん', '通': 'つう', '近': 'ちか', '逆': 'ぎゃく', '辺': 'へん', '送': 'そう', '代': 'だい', '表': 'ひょう',
    '挑': 'ちょう', '推': 'すい', '索': 'さく', '守': 'しゅ', '支': 'し', '協': 'きょう', '助': 'じょ',
    '拾': 'しゅう', '修': 'しゅう', '取': 'しゅ', '種': 'しゅ',
    # 假词（凑出来的写法）：按题目里的读音「しゅうしゅう」注
    '拾集': '{拾|しゅう}{集|しゅう}', '修集': '{修|しゅう}{集|しゅう}', '取集': '{取|しゅ}{集|しゅう}',
    # 前缀「名〜」等：按这一行讲的读法
    '名〜': '{名|めい}〜', '高〜': '{高|こう}〜', '良〜': '{良|りょう}〜', '真〜': '{真|ま}〜',
}
QK_AT = {
    ('n2-moji1-tane', 0, '種'): 'たね',
    ('n1-moji1-idonde', 1, '挑'): 'いど',
    ('n3-moji2-tasukete', 1, '守'): 'まも',
    ('n3-moji2-tasukete', 1, '支'): 'ささ',
}


def hira(s):
    return ''.join(chr(ord(c) - 0x60) if 'ァ' <= c <= 'ヶ' else c for c in s)


_tok = Tokenizer()


def align(surface, reading):
    """surface=送ります reading=おくります → {送|おく}ります；对不上返回 None"""
    if not KANJI.search(surface):
        return surface
    parts = re.findall(r'[一-鿿々〆ヶ]+|[^一-鿿々〆ヶ]+', surface)
    pat = ''.join('(.+?)' if KANJI.match(p) else '(' + re.escape(hira(p)) + ')' for p in parts)
    m = re.fullmatch(pat, reading)
    if not m:
        return None
    return ''.join('{%s|%s}' % (p, g) if KANJI.match(p) else p for p, g in zip(parts, m.groups()))


def ruby_plain(text, problems, where):
    """一段纯日语（无 ** 标记）→ 注音版"""
    out = ''
    i = 0
    # 先按 WORD 表切开（最长优先）
    keys = sorted(WORD, key=len, reverse=True)
    while i < len(text):
        hit = next((k for k in keys if text.startswith(k, i)), None)
        if hit:
            out += align(hit, WORD[hit]) or '{%s|%s}' % (hit, WORD[hit])
            i += len(hit)
            continue
        j = i
        while j < len(text) and not any(text.startswith(k, j) for k in keys):
            j += 1
        # 空格（半角/全角）原样保留：janome 会把空白吃掉
        for chunk in re.split(r'(\s+)', text[i:j]):
            if not chunk or chunk.isspace():
                out += chunk
                continue
            for t in _tok.tokenize(chunk):
                s = t.surface
                if not KANJI.search(s):
                    out += s
                    continue
                r = hira(t.reading) if t.reading and t.reading != '*' else ''
                a = align(s, r) if r else None
                if a is None:
                    problems.append('%s: 读不出「%s」(janome=%s)' % (where, s, t.reading))
                    a = s
                out += a
        i = j
    return out


def ruby_segment(seg, problems, where):
    """seg 可能带 ** 粗体标记：去掉标记注音，再按位置放回（标记不会插进 {..} 里）"""
    marks = []
    plain = ''
    k = 0
    while k < len(seg):
        if seg.startswith('**', k):
            marks.append(len(plain)); k += 2
        else:
            plain += seg[k]; k += 1
    r = ruby_plain(plain, problems, where)
    if not marks:
        return r
    # 按 plain 下标把 ** 放回去
    out, pi, k = '', 0, 0
    pending = list(marks)
    while k < len(r):
        while pending and pending[0] == pi:
            out += '**'; pending.pop(0)
        m = re.match(r'\{([^|{}]+)\|([^|{}]+)\}', r[k:])
        if m:
            base = m.group(1)
            inner = [p for p in pending if pi < p < pi + len(base)]
            if inner:
                problems.append('%s: 粗体标记落在词中间「%s」' % (where, base))
            out += m.group(0); pi += len(base); k += m.end()
            pending = [p for p in pending if p >= pi]
        else:
            out += r[k]; pi += 1; k += 1
    out += '**' * len(pending)
    return out


def is_cn(c):
    """这个汉字只会出现在中文里：中文虚词，或者日文字库（cp932）里没有的简体字"""
    if c in CN:
        return True
    if KANJI.match(c):
        try:
            c.encode('cp932')
        except UnicodeEncodeError:
            return True
    return False


def jp_ok(s):
    return not any(is_cn(c) for c in s)


def jp_line(line, problems, where):
    """解析里的一行 → 注音版（中文部分原样）。
    日语 =「」里的内容 / 中文句子里的 **粗体** / 用标点切开后「有假名、且没有中文专用字」的小句"""
    if line in LINE:
        return LINE[line]
    if not KANJI.search(line):
        return line
    out = ''
    for pc in re.split(r'(「[^「」]*」|\*\*[^*]+\*\*)', line):
        if not pc:
            continue
        if pc.startswith('「') and pc.endswith('」'):
            inner = pc[1:-1]
            m = re.match(r'(\S+) ex(\d+)$', where)
            at = QK_AT.get((m.group(1), int(m.group(2)), inner)) if m else None
            if at or inner in QK:
                v = at or QK[inner]
                out += '「' + (v if '{' in v else '{%s|%s}' % (inner, v)) + '」'
            else:
                out += '「' + (ruby_segment(inner, problems, where) if jp_ok(inner.replace('*', '')) else inner) + '」'
        elif pc.startswith('**') and pc.endswith('**') and len(pc) > 4:
            # 中文句子里的粗体：有假名才当日语（「不寂寞」「下周一」这种纯汉字粗体是中文）；纯汉字的日语粗体走 LINE
            inner = pc[2:-2]
            out += '**' + (ruby_segment(inner, problems, where) if jp_ok(inner) and KANJI.search(inner) and KANA.search(inner) else inner) + '**'
        else:
            for cl in re.split(r'([，。：；、（）()"“”/→～？！]+)', pc):
                if KANJI.search(cl) and KANA.search(cl) and jp_ok(cl):
                    out += ruby_segment(cl, problems, where)
                else:
                    out += cl
    for frag, ch in SKIP:
        if frag in line:
            out = re.sub(r'\{' + re.escape(ch) + r'\|[^|{}]+\}', ch, out)
    return out


def strip_ruby(s):
    return re.sub(r'\{([^|{}]+)\|([^|{}]+)\}', r'\1', s)


def load():
    js = ("global.window={};require(%s);process.stdout.write(JSON.stringify({Q:window.QUESTIONS,T:window.TEACH,E:window.EXAMS}))"
          % json.dumps(QJS.replace('\\', '/')))
    out = subprocess.run(['node', '-e', js], capture_output=True, check=True).stdout
    return json.loads(out.decode('utf-8'))


def main():
    check_only = '--check' in sys.argv
    src = io.open(QJS, encoding='utf-8', newline='').read()
    nl = '\r\n' if '\r\n' in src else '\n'
    # 生成时不能读到旧的自动块（否则会以为手写字段已经有了）
    if BEGIN in src:
        a = src.index(BEGIN); b = src.index(END) + len(END)
        base_src = src[:a].rstrip() + nl + src[b:].lstrip('\r\n')
    else:
        base_src = src
    tmp = QJS + '.gen_tmp.js'
    io.open(tmp, 'w', encoding='utf-8', newline='').write(base_src)
    global QJS_LOAD
    try:
        js = ("global.window={};require(%s);process.stdout.write(JSON.stringify({Q:window.QUESTIONS,T:window.TEACH,E:window.EXAMS}))"
              % json.dumps(tmp.replace('\\', '/')))
        data = json.loads(subprocess.run(['node', '-e', js], capture_output=True, check=True).stdout.decode('utf-8'))
    finally:
        os.remove(tmp)
    Q, T, E = data['Q'], data['T'] or {}, data['E'] or []

    gen, review, problems, untouched = {}, [], [], []
    for q in Q:
        t = T.get(q['id'], {})
        g = {}
        where = q['id']
        if KANJI.search(q.get('section', '')) and 'section' not in t:
            g['section'] = ruby_segment(q['section'], problems, where + ' section')
            review.append((where, 'section', q['section'], g['section']))
        if isinstance(q.get('brief'), str) and 'brief' not in t:
            plain = strip_ruby(q['brief'])
            if KANJI.search(re.sub(r'\{[^|{}]+\|[^|{}]+\}', '', q['brief'])):
                g['brief'] = ruby_segment(plain, problems, where + ' brief')
                review.append((where, 'brief', q['brief'], g['brief']))
        hand = {strip_ruby(x) for x in t.get('expl', [])}
        ex = []
        for n, l in enumerate(q['explanation']):
            if l in hand:
                continue
            r = jp_line(l, problems, '%s ex%d' % (where, n))
            if r == l and KANJI.search(l) and KANA.search(l):
                untouched.append('[%s ex%d] %s' % (where, n, l))
            if r != l:
                if strip_ruby(r) != l:
                    problems.append('%s ex%d: 去掉注音后和原行不一样' % (where, n))
                ex.append(r)
                review.append((where, 'ex%d' % n, l, r))
        if ex:
            g['expl'] = ex
        if g:
            gen[q['id']] = g
    parts = {}
    for x in E:
        for p in x['parts']:
            if KANJI.search(p['name']) and 'teach' not in p:
                parts[p['name']] = ruby_segment(p['name'], problems, 'exam part')
                review.append(('EXAM', 'part', p['name'], parts[p['name']]))

    body = json.dumps(gen, ensure_ascii=False, indent=2)
    pbody = json.dumps(parts, ensure_ascii=False, indent=2)
    block = (BEGIN + nl +
             '// 手写的 TEACH 字段优先；这里只补没写的 section / brief / expl（expl 和手写的合并）；试卷分区名加 teach' + nl +
             '(function (T, E, G, P) {' + nl +
             '  Object.keys(G).forEach(function (id) {' + nl +
             '    var t = T[id] = T[id] || {};' + nl +
             "    Object.keys(G[id]).forEach(function (k) { if (k === 'expl') t.expl = (t.expl || []).concat(G[id].expl); else if (t[k] == null) t[k] = G[id][k]; });" + nl +
             '  });' + nl +
             '  (E || []).forEach(function (x) { x.parts.forEach(function (p) { if (p.teach == null && P[p.name]) p.teach = P[p.name]; }); });' + nl +
             '})(window.TEACH = window.TEACH || {}, window.EXAMS, ' + body.replace('\n', nl) + ', ' + pbody.replace('\n', nl) + ');' + nl +
             END)
    new_src = base_src.rstrip() + nl + nl + block + nl

    lines = []
    for where, f, a, b in review:
        lines.append('[%s %s]' % (where, f))
        lines.append('  原: ' + a)
        lines.append('  注: ' + b)
    lines.append('')
    lines.append('== 没加注音、但有假名又有汉字的解析行 %d 条（逐行确认：里面的汉字应该全是中文）==' % len(untouched))
    lines += untouched
    lines.append('')
    lines.append('== 问题 %d 条 ==' % len(problems))
    lines += problems
    if check_only:
        same = new_src == src
        print('[OK] block up to date' if same else '[FAIL] block out of date: run tools/gen_teach_ruby.py')
        sys.exit(0 if same else 1)
    io.open(REVIEW, 'w', encoding='utf-8', newline='\n').write('\n'.join(lines) + '\n')
    io.open(QJS, 'w', encoding='utf-8', newline='').write(new_src)
    print('[OK] questions: %d with ruby, review lines: %d, problems: %d' % (len(gen), len(review), len(problems)))


if __name__ == '__main__':
    main()
