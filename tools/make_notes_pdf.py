# 把手写笔记的 HTML 电子版导出成两个 PDF（照片配色 / 白底）
# 用法：python tools/make_notes_pdf.py notes/Page001/Page001.html
# 输出：同目录下 <名字>_照片配色.pdf、_白底.pdf、_照片配色_隐藏笔记.pdf、_白底_隐藏笔记.pdf
import os, subprocess, sys, pathlib, time

EDGE = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
src = pathlib.Path(sys.argv[1]).resolve()
base = src.with_suffix('')
url = src.as_uri()
prof = pathlib.Path(os.environ.get('TEMP', '.')) / 'notes_pdf_profile'

ok = True
VERSIONS = (
    ('theme=photo&clean=0', '照片配色'),
    ('theme=white&clean=0', '白底'),
    ('theme=photo&clean=1', '照片配色_隐藏笔记'),
    ('theme=white&clean=1', '白底_隐藏笔记'),
)
for query, label in VERSIONS:
    theme = query
    out = pathlib.Path(str(base) + '_' + label + '.pdf')
    for attempt in range(3):          # headless Edge 偶尔第一次不出文件，重试
        if out.exists():
            out.unlink()
        subprocess.run([EDGE, '--headless=new', '--disable-gpu', '--user-data-dir=' + str(prof),
                        '--no-pdf-header-footer', '--virtual-time-budget=4000',
                        '--print-to-pdf=' + str(out), url + '?' + query],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if out.exists() and out.stat().st_size > 1000:
            break
        time.sleep(1)
    # 控制台是 GBK，只打 ASCII
    if out.exists():
        print('[OK]', theme, out.stat().st_size, 'bytes')
    else:
        print('[FAIL]', theme); ok = False
sys.exit(0 if ok else 1)
