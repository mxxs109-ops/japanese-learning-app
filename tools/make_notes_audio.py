# 给手写笔记页生成日语朗读（VOICEVOX），生成过的不再生成
#
# 用法（用 VOICEVOX 旁边那个 venv，里面装了 soundfile/numpy）：
#   D:\A030_VOICEVOX\venv\Scripts\python.exe tools\make_notes_audio.py notes\Page001\Page001.html
#   可选：--voices 2,3,8   只生成这几个音色（style id，见 audio/voices.txt）
#         --prune          删掉 audio/ 里已经没人用的旧音频（默认只报数，不删）
#
# 流程：
#   1. 用 headless Edge 打开 PageNNN.html?sayplan=1，拿到页面要读的内容（和页面上的分词完全一致，见 notes/_shared/say.js）
#   2. 每段 × 每个音色：缓存号 = sha1(引擎版本|音色|要读的文字)。audio/<缓存号>.ogg + .json 已存在 → 直接用，不重新生成
#   3. 没有的才调 VOICEVOX：audio_query（拿到每个音的时长）→ synthesis → 存 OGG；按「每个词有几个音」算出每个词从第几秒开始
#   4. 写 audio/manifest.js（页面读它）+ audio/kana.txt（每段实际念成的片假名，核对读音用）
# VOICEVOX 引擎没开就自动启动，用完关掉（是脚本自己开的才关）。控制台只打 ASCII（本机 GBK）。
import glob, hashlib, html, io, json, os, re, subprocess, sys, time, urllib.parse, urllib.request
import numpy as np, soundfile as sf

EDGE = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
ENGINE_ROOT = r'D:\A030_VOICEVOX'
BASE = 'http://127.0.0.1:50021'
# 默认生成的音色：(角色名, 风格名)。辐射蓝挑过后改这里
DEFAULT_VOICES = [
    ('四国めたん', 'ノーマル'),
    ('ずんだもん', 'ノーマル'),
    ('春日部つむぎ', 'ノーマル'),
    ('冥鳴ひまり', 'ノーマル'),
    ('青山龍星', 'ノーマル'),
    ('玄野武宏', 'ノーマル'),
]


def api(path, params=None, body=None, raw=False, timeout=120):
    url = BASE + path + ('?' + urllib.parse.urlencode(params) if params else '')
    data = None if body is None else json.dumps(body).encode('utf-8')
    req = urllib.request.Request(url, data=data, method='POST' if (body is not None or path in ('/audio_query', '/accent_phrases', '/synthesis')) else 'GET')
    if data is not None:
        req.add_header('Content-Type', 'application/json')
    with urllib.request.urlopen(req, timeout=timeout) as r:
        b = r.read()
    return b if raw else json.loads(b.decode('utf-8'))


def engine_up():
    try:
        return api('/version', timeout=3)
    except Exception:
        return None


def start_engine():
    exes = glob.glob(os.path.join(ENGINE_ROOT, '**', 'run.exe'), recursive=True)
    if not exes:
        sys.exit('[FAIL] run.exe not found under ' + ENGINE_ROOT)
    p = subprocess.Popen([exes[0], '--host', '127.0.0.1', '--port', '50021'], cwd=os.path.dirname(exes[0]),
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                         creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    for _ in range(180):
        if engine_up():
            return p
        if p.poll() is not None:
            sys.exit('[FAIL] engine exited, code %s' % p.returncode)
        time.sleep(1)
    p.kill()
    sys.exit('[FAIL] engine did not start in 180s')


def get_plan(page):
    url = pathlib_uri(page) + '?sayplan=1'
    prof = os.path.join(os.environ.get('TEMP', '.'), 'notes_say_profile')
    out = subprocess.run([EDGE, '--headless=new', '--disable-gpu', '--user-data-dir=' + prof,
                          '--virtual-time-budget=3000', '--dump-dom', url],
                         stdout=subprocess.PIPE, stderr=subprocess.DEVNULL).stdout.decode('utf-8', 'replace')
    m = re.search(r'<pre id="say-plan">(.*?)</pre>', out, re.S)
    if not m:
        sys.exit('[FAIL] no say-plan in page (is notes/_shared/say.js included?)')
    return json.loads(html.unescape(m.group(1)))


def pathlib_uri(p):
    import pathlib
    return pathlib.Path(p).resolve().as_uri()


def moras_of(q):
    """每个音（mora）的开始时间（秒），以及总时长。speedScale 固定 1，语速在页面上用 playbackRate 调"""
    t = q['prePhonemeLength']
    starts = []
    for ap in q['accent_phrases']:
        for m in ap['moras']:
            starts.append(t)
            t += (m.get('consonant_length') or 0) + m['vowel_length']
        if ap.get('pause_mora'):
            t += (ap['pause_mora'].get('consonant_length') or 0) + ap['pause_mora']['vowel_length']
    return starts, t + q['postPhonemeLength']


def count_moras(text, style):
    if not re.search(r'[0-9A-Za-z\u3040-\u30ff\u3400-\u9fff\uff10-\uff19]', text):
        return 0
    aps = api('/accent_phrases', {'text': text, 'speaker': style})
    return sum(len(ap['moras']) for ap in aps)


GEN = 'g3'   # 生成方法的版本；🔴 改了送进引擎的方式（空格/停顿/读法）就 +1，否则会一直复用旧音频


def make(seg, style, cache_dir, version, stats):
    text = ''.join(c['s'] for c in seg['chunks'])
    key = hashlib.sha1(('%s|%s|%s|%s' % (GEN, version, style, text)).encode('utf-8')).hexdigest()[:16]
    ogg, meta = os.path.join(cache_dir, key + '.ogg'), os.path.join(cache_dir, key + '.json')
    if os.path.exists(ogg) and os.path.exists(meta):
        stats['reused'] += 1
        return key, json.load(io.open(meta, encoding='utf-8'))
    counts = [count_moras(c['s'], style) for c in seg['chunks']]
    # 词与词之间加全角空格送进引擎：不加的话会断错词（「デパートでかいもの」→ でかい）。
    # 但空格会让引擎在每个词后停顿 → 把「我们加的空格」造成的停顿去掉，只留原文 。、 的停顿
    joined, inserted, cum = '', set(), 0
    for i, c in enumerate(seg['chunks']):
        joined += c['s']
        cum += counts[i]
        # 不加空格的情况：最后一个词；原文已有 。、；＿＿（念「かせん」）要和后面的「の」连着；
        # 下一个词是跨行接着的（j=1，「いち｜ばん」）
        nxt = seg['chunks'][i + 1] if i < len(seg['chunks']) - 1 else None
        if nxt and not re.search(r'[。、]$', c['s']) and not re.fullmatch(r'[＿_]+', c['t']) and not nxt.get('j'):
            joined += '　'
            inserted.add(cum)
    q = api('/audio_query', {'text': joined, 'speaker': style})
    pos = 0
    for ap in q['accent_phrases']:
        pos += len(ap['moras'])
        if ap.get('pause_mora') and pos in inserted:
            ap['pause_mora'] = None
            stats['unpaused'] += 1
    q['speedScale'] = 1.0
    wav = api('/synthesis', {'speaker': style}, body=q, raw=True, timeout=300)
    x, sr = sf.read(io.BytesIO(wav), dtype='float32')
    if x.ndim > 1:
        x = x.mean(1)
    starts, total = moras_of(q)
    n, s = len(starts), sum(counts)
    if s != n:
        stats['scaled'] += 1             # 分开数和整句数对不上 → 按比例分
    cum, cstart = 0, []
    for k in counts:
        idx = min(n - 1, int(round(cum * n / s))) if s else 0
        cstart.append(round(starts[idx] if n else 0, 3))
        cum += k
    # 0 个音的词（只有括号）= 和下一个词同时开始
    for i in range(len(counts) - 2, -1, -1):
        if counts[i] == 0:
            cstart[i] = cstart[i + 1]
    info = {'d': round(len(x) / sr, 3), 'c': cstart, 'kana': q.get('kana', ''), 'calc': round(total, 3), 'm': [n, s]}
    tmp = ogg + '.part'
    sf.write(tmp, x, sr, format='OGG', subtype='VORBIS')
    os.replace(tmp, ogg)
    io.open(meta, 'w', encoding='utf-8').write(json.dumps(info, ensure_ascii=False))
    stats['made'] += 1
    return key, info


def main():
    args = [a for a in sys.argv[1:]]
    page = [a for a in args if a.lower().endswith('.html')]
    if not page:
        sys.exit(__doc__ or 'usage: make_notes_audio.py notes/PageNNN/PageNNN.html')
    page = os.path.abspath(page[0])
    cache_dir = os.path.join(os.path.dirname(page), 'audio')
    os.makedirs(cache_dir, exist_ok=True)

    started = None
    version = engine_up()
    if not version:
        print('[INFO] starting VOICEVOX engine ...', flush=True)
        started = start_engine()
        version = engine_up()
    print('[OK] engine', version, flush=True)
    try:
        speakers = api('/speakers')
        lines, by_name = [], {}
        for sp in speakers:
            for stl in sp['styles']:
                by_name[(sp['name'], stl['name'])] = stl['id']
                lines.append('%d\t%s\t%s' % (stl['id'], sp['name'], stl['name']))
        io.open(os.path.join(cache_dir, 'voices.txt'), 'w', encoding='utf-8').write('\n'.join(lines) + '\n')

        if '--voices' in args:
            ids = [int(v) for v in args[args.index('--voices') + 1].split(',')]
            names = {v: k for k, v in by_name.items()}
            voices = [(i, '%s（%s）' % names[i]) for i in ids]
        else:
            voices = []
            for nm, stl in DEFAULT_VOICES:
                if (nm, stl) in by_name:
                    voices.append((by_name[(nm, stl)], nm))
                else:
                    print('[WARN] voice not found, skipped (see audio/voices.txt)', flush=True)

        plan = get_plan(page)
        print('[OK] plan segments', len(plan), 'voices', len(voices), flush=True)
        stats = {'made': 0, 'reused': 0, 'scaled': 0, 'unpaused': 0}
        segs, keys, kana = {}, {}, []
        for seg in plan:
            text = ''.join(c['s'] for c in seg['chunks'])
            segs[seg['id']] = {'text': text, 'v': {}}
            for vi, (style, name) in enumerate(voices):
                key, info = make(seg, style, cache_dir, version, stats)
                segs[seg['id']]['v'][str(style)] = key
                keys[key] = {'d': info['d'], 'c': info['c']}
                if vi == 0:
                    kana.append('%s\t%s\t%s' % (seg['id'], text, info.get('kana', '')))
        data = {'engine': version, 'voices': [{'id': str(s), 'name': n} for s, n in voices], 'segs': segs, 'keys': keys}
        io.open(os.path.join(cache_dir, 'manifest.js'), 'w', encoding='utf-8').write(
            '// 由 tools/make_notes_audio.py 生成，别手改\nwindow.SAY_DATA = ' + json.dumps(data, ensure_ascii=False) + ';\n')
        io.open(os.path.join(cache_dir, 'kana.txt'), 'w', encoding='utf-8').write('\n'.join(kana) + '\n')

        used = set(keys)
        old = [f for f in glob.glob(os.path.join(cache_dir, '*.ogg')) if os.path.basename(f)[:-4] not in used]
        if '--prune' in args:
            for f in old:
                os.remove(f)
                j = f[:-4] + '.json'
                if os.path.exists(j):
                    os.remove(j)
        print('[OK] made=%d reused=%d scaled=%d unpaused=%d unused_old=%d%s' % (
            stats['made'], stats['reused'], stats['scaled'], stats['unpaused'], len(old),
            ' (pruned)' if '--prune' in args and old else ''), flush=True)
    finally:
        if started:
            started.kill()
            print('[INFO] engine stopped', flush=True)


if __name__ == '__main__':
    main()
