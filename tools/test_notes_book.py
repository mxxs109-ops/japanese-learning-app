# 手写笔记书（notes/book.html）的自动验收：用 CDP 控制固定视口的 headless Edge，模拟真实鼠标，截图 + 断言
#
# 用法（需要 websocket-client，D:\A030_VOICEVOX\venv 里装好了）：
#   D:\A030_VOICEVOX\venv\Scripts\python.exe tools\test_notes_book.py [截图输出目录]
# 截图默认存到 %TEMP%\notes_book_test\，看图确认效果。控制台只打 ASCII（本机 GBK）。
#
# 🔴 为什么不用 msedge --screenshot：它在截图时会改视口大小，排版用的尺寸和截出来的不一样，
#    截出来的画面是错的（2026-11-10 被它骗过一次）。CDP 固定视口 + 页面里直接执行操作才可信。
#
# 检查项：
#   1 停稳时真页面（iframe）显示，且和库算出的页面位置逐像素对齐
#   2 鼠标移到右下角 → 卷角（state=fold_corner），真页面藏起来
#   3 按住右下角拖过书脊 → 翻页（user_fold → flip）
#   4 切「照片配色 / 显示笔记」→ 翻页用的图跟着换
#   5 停稳时点「全部朗读」→ 当前页回报 playing=true
#   6 窄屏（600 宽）→ 单页（portrait），真页面对齐
import base64, json, os, subprocess, sys, time, urllib.request
import websocket

EDGE = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOOK = 'file:///' + os.environ.get('NOTES_BOOK', os.path.join(ROOT, 'notes', 'book.html')).replace('\\', '/')   # NOTES_BOOK=测别的副本
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.environ.get('TEMP', '.'), 'notes_book_test')
os.makedirs(OUT, exist_ok=True)


class Browser:
    def __init__(self, url, w, h, port):
        prof = os.path.join(os.environ.get('TEMP', '.'), 'notes_book_test_profile_%d' % port)
        self.p = subprocess.Popen([EDGE, '--headless=new', '--disable-gpu', '--remote-debugging-port=%d' % port,
                                   '--user-data-dir=' + prof, '--autoplay-policy=no-user-gesture-required',
                                   '--window-size=%d,%d' % (w, h), 'about:blank'],
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        tab = None
        for _ in range(100):
            try:
                tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:%d/json' % port).read())
                tab = [t for t in tabs if t.get('type') == 'page'][0]
                break
            except Exception:
                time.sleep(0.2)
        self.ws = websocket.create_connection(tab['webSocketDebuggerUrl'], timeout=30)
        self.n = 0
        self.call('Emulation.setDeviceMetricsOverride', width=w, height=h, deviceScaleFactor=1, mobile=False)
        self.call('Page.enable')
        self.call('Page.navigate', url=url)
        time.sleep(2.5)
        self.js('localStorage.clear()')

    def call(self, method, **params):
        self.n += 1
        self.ws.send(json.dumps({'id': self.n, 'method': method, 'params': params}))
        while True:
            m = json.loads(self.ws.recv())
            if m.get('id') == self.n:
                return m.get('result', {})

    def js(self, expr):
        r = self.call('Runtime.evaluate', expression=expr, returnByValue=True, awaitPromise=True)
        return r.get('result', {}).get('value')

    def shot(self, name):
        r = self.call('Page.captureScreenshot', format='png')
        open(os.path.join(OUT, name), 'wb').write(base64.b64decode(r['data']))

    def mouse(self, typ, x, y, buttons=0):
        self.call('Input.dispatchMouseEvent', type=typ, x=x, y=y, button='none' if typ == 'mouseMoved' else 'left',
                  buttons=buttons, clickCount=0 if typ == 'mouseMoved' else 1)

    def geo(self):
        return json.loads(self.js("JSON.stringify({r:BOOK.flip.getBoundsRect(),b:document.getElementById('book').getBoundingClientRect(),"
                                  "o:BOOK.flip.getOrientation()})"))

    def close(self):
        try:
            self.ws.close()
        except Exception:
            pass
        self.p.kill()


results = []
def check(name, ok, detail=''):
    results.append(ok)
    print('[%s] %s %s' % ('OK' if ok else 'FAIL', name, detail), flush=True)


def aligned(b, k):
    """第 k 页的 iframe 是否和库算出的页面位置对齐（误差 1px）"""
    g = b.geo()
    f = json.loads(b.js("JSON.stringify(BOOK.frames[%d].getBoundingClientRect())" % k))
    r, bk = g['r'], g['b']
    if g['o'] == 'portrait':
        x = bk['left'] + r['left'] + r['pageWidth']
    else:
        x = bk['left'] + (r['left'] + r['pageWidth'] if k % 2 == 0 else r['left'])
    want = [x, bk['top'] + r['top'], r['pageWidth'], r['height']]
    got = [f['left'], f['top'], f['width'], f['height']]
    return all(abs(a - c) <= 1 for a, c in zip(want, got)), 'want=%s got=%s' % ([round(v) for v in want], [round(v) for v in got])


b = Browser(BOOK, 1400, 950, 9341)
try:
    b.js('BOOK.flip.turnToPage(1)'); time.sleep(1.5)
    ok, d = aligned(b, 1)
    check('1 rest: live page shown + aligned', b.js('BOOK.frames[1].className') == 'live on' and ok, d)
    b.shot('1_rest.png')

    b.js("window.__log=[];BOOK.flip.on('changeState',function(e){__log.push('state:'+e.data)});BOOK.flip.on('flip',function(e){__log.push('flip:'+e.data)})")
    g = b.geo(); r, bk = g['r'], g['b']
    cx, cy = bk['left'] + r['left'] + 2 * r['pageWidth'] - 12, bk['top'] + r['top'] + r['height'] - 12
    b.mouse('mouseMoved', cx - 80, cy - 80); time.sleep(0.2)
    b.mouse('mouseMoved', cx, cy); time.sleep(0.8)
    log = json.loads(b.js('JSON.stringify(__log)'))
    check('2 corner hover: fold_corner + live page hidden', 'state:fold_corner' in log and b.js('BOOK.frames[1].className') == 'live', str(log))
    b.shot('2_corner.png')

    b.mouse('mousePressed', cx, cy, 1); time.sleep(0.1)
    for k in range(1, 21):
        x, y = cx - k * 1.6 * r['pageWidth'] / 20, cy - k * 8
        b.mouse('mouseMoved', x, y, 1); time.sleep(0.03)
        if k == 10:
            b.shot('3_drag_half.png')
    b.mouse('mouseReleased', x, y); time.sleep(1.8)
    log = json.loads(b.js('JSON.stringify(__log)'))
    check('3 drag corner past spine: page flips', 'state:user_fold' in log and any(s.startswith('flip:') for s in log), str(log))

    b.js('BOOK.flip.turnToPage(1)'); time.sleep(1.2)
    b.js("document.querySelector('[data-t=photo]').click()"); time.sleep(0.4)
    b.js("document.querySelector('[data-c=\"0\"]').click()"); time.sleep(1.2)
    # 图片地址在库内部：看库里第 1 页的图片对象
    cur =b.js("(function(){try{return BOOK.flip.getPageCollection().getPage(1).image.src}catch(e){return 'ERR '+e}})()")
    check('4 theme photo + notes: flip image switched', isinstance(cur, str) and cur.endswith('flip/photo_0.png'), str(cur)[-40:])
    b.mouse('mouseMoved', 700, 400); time.sleep(0.2)
    g = b.geo(); r, bk = g['r'], g['b']
    b.mouse('mouseMoved', bk['left'] + r['left'] + 14, bk['top'] + r['top'] + r['height'] - 14); time.sleep(0.8)
    b.shot('4_photo_left_corner.png')
    b.mouse('mouseMoved', 700, 400); time.sleep(1.0)

    b.js("document.getElementById('play').click()"); time.sleep(1.5)
    st = json.loads(b.js("JSON.stringify(BOOK.states[1]||{})"))
    check('5 read-aloud at rest: page reports playing', st.get('playing') is True, 'playing=%s' % st.get('playing'))
    b.js("document.getElementById('stop').click()")
finally:
    b.close()

b = Browser(BOOK, 600, 1000, 9342)
try:
    b.js('BOOK.flip.turnToPage(1)'); time.sleep(1.5)
    ok, d = aligned(b, 1)
    check('6 narrow: portrait + aligned', b.geo()['o'] == 'portrait' and ok, d)
    b.shot('6_portrait.png')
finally:
    b.close()

print('[%s] %d/%d passed, screenshots in %s' % ('OK' if all(results) else 'FAIL', sum(results), len(results), OUT.encode('ascii', 'replace').decode()))
sys.exit(0 if all(results) else 1)
