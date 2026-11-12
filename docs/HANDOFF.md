# HANDOFF · 日本語 Daily（japanese learning app）

> 接手先读这份，再读 `docs/WORKLOG.md` 最新一节。

## 是什么

辐射蓝每天在微信给朋友发一道 JLPT 真题。这个小软件把这些题做成练习：
选答案 → 看对错和解析 → 错题按周复习。纯静态网页，双击 `index.html` 就能用，不需要服务器。

- 本地目录：`C:\Users\wangx\Desktop\japanese learning app`
- GitHub：`mxxs109-ops/japanese-learning-app`（公开仓库，main 分支）
  - 必须公开：一键安装命令用 curl 匿名下载，私有仓库下不到
- 和 MyTheo 无关，不要把这里的日志写进 MyTheo 的 `Claude\`

## 文件

| 文件 | 作用 |
|---|---|
| `index.html` | 整个界面（样式 + 页面逻辑都在里面） |
| `questions.js` | 题库 `window.QUESTIONS` + 微信里已做过的结果 `window.PAST_RESULTS` |
| `srs.js` | 复习规则（改规则只改这里）；也能被 node `require` 做测试 |
| `install.bat` | 一键安装/更新脚本（纯 ASCII + CRLF，`.gitattributes` 里 `*.bat -text` 保证 GitHub 原样存 CRLF） |
| `README.md` | 仓库首页，写着一键命令 |
| `images/` | 题目插图（install.bat 会拷） |
| `screenshots/<级别>/` | 原题 + 解析截图（只进仓库，不进软件） |
| `notes/` | **手写笔记书**（和小软件无关的另一条线，见下面「手写笔记书」一章） |
| `tools/check_teach.js` | 教学模式注音校验 |
| `tools/make_notes_pdf.py` | 笔记页 → 4 个 PDF + 4 张翻页用整页图 |
| `tools/make_notes_audio.py` | 笔记页 → VOICEVOX 朗读音频（有缓存） |
| `tools/test_notes_book.py` | 笔记书自动验收（CDP 模拟鼠标，6 项） |
| `docs/HANDOFF.md` / `docs/WORKLOG.md` | 本文件 / 每天做了什么（倒序） |

## 复习规则（辐射蓝 2026-11-06 定）

- 新题第一次做对 → 已掌握，不再出现（题库页可手动复习）
- 做错 → 进错题集，连对清零，1 星期后出现
- 错题**到期那天**做对 → 连对 +1，下次间隔 = (连对+1) 星期（2 周、3 周……10 周）
- 连对满 10 → 移出错题集
- 中途做错 → 连对清零，下星期再来
- 不是到期那天手动练：做对不计连对；做错照样清零进错题集

⚠️ 「每次做对增加 1 个星期」是按「间隔逐次 +1 周」理解的（依据：他说做错「**还是**下个星期出现」）。
若他说其实是「每次固定隔 1 周」，只改 `srs.js` 里 `WEEK * (r.streak + 1)` → `WEEK`。

## 每天加新题（最常做的事）

1. 他发截图 → 在 `questions.js` 的 `QUESTIONS` 末尾照格式加一项
   - `date` = 哪天解锁；`sentence` 里 `[方括号]` = 下划线部分；`answer` 从 0 开始
   - 解析逐字抄他截图里的文字，别自己编
2. 如果截图里朋友已经在微信作答了，在 `PAST_RESULTS` 加一条 `{id, date, choice}`（choice 从 0 开始）
   - 每条只写入一次（`state.pastApplied` 记着），会覆盖写入前的浏览器记录，之后的进度不动
3. 🔴 **截图两处都要放**（他 11-09 定：软件里可以没有，文件夹和 GitHub 必须有）：
   题目 + 解析截图放进 `screenshots/<级别>/` **和** 桌面 `日本語Daily_真题截图\<级别>\`，两边一致；
   命名 `DayN_MM-DD_单词_1题目.png` / `_2解析.png`；🔴 **同一天同级别有多道时加原题题号**（截图顶部数字条）保证按题目顺序排：
   `Day5_11-12_5_の_1题目.png`、`Day5_11-12_6_で_…`（他 11-12 要求）。
   🔴 **阅读题 / 文章题（`layout: 'passage'`）解析末尾必须加「**全文翻译**」**（他 11-12 要求），只在答完后显示。
   ⚠️ 本地改题后验证前先推送：页面会自动检查更新，同 id 以 GitHub 为准，没推的本地改动会被盖掉、看起来像没生效。install.bat 不拷 screenshots/，不进软件
4. `git commit` + `git push` —— **只改题目不用让朋友重装**：App 打开时自动检查、或点右上角「检查更新」，就从 GitHub 拿最新 `questions.js`

## 检查更新（2026-11-06 加）

- 走 GitHub API `api.github.com/repos/mxxs109-ops/japanese-learning-app/contents/<文件>?ref=main`
  （带 `Accept: application/vnd.github.raw+json` 直接拿原文；**不用 raw.githubusercontent**，那个有 5 分钟缓存）
- 拿到的 `questions.js` 用 `new Function('window', 源码)` 跑在假 window 上取 `QUESTIONS / PAST_RESULTS`，
  逐条 `validQ` 校验，**同 id 以 GitHub 为准**，存进 localStorage `jp-daily-remote-v1`（离线也能用上次拿到的）
- 打开时自动静默检查：没网 / 出错就什么都不显示；只有拿到新题才提示「拿到 N 道新题」
- **程序更新**：`version.txt` 里的数 > 页面里的 `APP_VERSION` ⇒ 顶部出「程序有新版本」+「复制安装命令」
  ⇒ 🔴 **改了 index.html / srs.js / install.bat，必须把 `APP_VERSION` 和 `version.txt` 一起 +1**，否则朋友收不到提示
- 未登录 API 限额 60 次/小时/IP，个人用够

## 一键安装命令（Windows cmd）

```
curl -sL -o "%TEMP%\jla.bat" https://raw.githubusercontent.com/mxxs109-ops/japanese-learning-app/main/install.bat && "%TEMP%\jla.bat"
```

脚本：取真实桌面路径（兼容 OneDrive 重定向）→ curl 下 main.zip → `tar -xf` 解压 → 只拷 3 个文件到桌面 `japanese learning app` → 打开页面 → 3、2、1 → `exit` 关窗。
倒计时用 `ping -n 2 127.0.0.1`，不用 `timeout`（stdin 重定向时 timeout 直接报错退出）。
curl / tar 写死 `%SystemRoot%\System32\` 的版本：装了 Git 的机器上，PATH 里的 GNU tar 会把 `C:` 当远程主机（`tar: Cannot connect to C: resolve failed`）。
改完 install.bat 后 raw 地址有约 5 分钟缓存，测试要按提交号下载：`raw.githubusercontent.com/.../<commit>/install.bat`。

## 测试

- 规则单测：`node <scratch>/test_srs.js` 的写法见 WORKLOG 11-06；核心断言：新题对→mastered、错→+7 天、间隔 2..10 周、第 10 次毕业、中途错清零
- 模拟日期：网址加 `?today=2026-11-13`（顶上黄条提示；测试模式下作答也会写进进度）
- 进度存在 localStorage key `jp-daily-v1`；file:// 下 Chromium 所有本地文件共用一个存储

## 手写笔记书（notes/，2026-11-09 起）

辐射蓝把真题手抄在 KOKUYO 横线本上，拍照发来。这里把每一页做成「打印字体电子版」：PDF 能打印，还装订成一本可翻页、可朗读的书。
**和小软件（index.html）是两条线**：install.bat 不拷 `notes/`，朋友的软件里没有。

### 打开方式
- 书：`notes/book.html`（桌面 `日本語Daily_手写笔记\book.html` 同一份）——**平时给他看就开这个**
- 单页：`notes/PageNNN/PageNNN.html`（右上角也有切换和朗读）
- PDF：`notes/PageNNN/PageNNN_<照片配色|白底>[_隐藏笔记].pdf`

### 结构
```
notes/
├─ book.html                 书（翻页 + 工具栏）
├─ pages.js                  书里有哪些页：window.NOTE_PAGES = ['Page001', ...]
├─ _shared/
│  ├─ say.js                 所有页共用：朗读、逐词高亮、嵌进书（?embed=1）、截图模式（?shot=1）、导出朗读计划（?sayplan=1）
│  ├─ page-flip.browser.js   StPageFlip 2.0.7（MIT）本地副本 —— 🔴 改过一处（clear 用 clearRect），别从 CDN 覆盖
│  └─ page-flip.LICENSE
└─ PageNNN/
   ├─ PageNNN.html           排版源（一行 = 本子一条横线）
   ├─ PageNNN_原稿照片.jpg     他拍的原稿
   ├─ PageNNN_A3插图.png      题目插图（原图原色）
   ├─ PageNNN_*.pdf × 4       照片配色/白底 × 显示/隐藏笔记
   ├─ flip/<white|photo>_<0|1>.png   翻书用整页图（1588×2246）
   └─ audio/                  朗读：<缓存号>.ogg/.json、manifest.js、kana.txt、voices.txt
```

### 新抄一页的完整流程（Page002 照这个做）
1. 他发照片 → 建 `notes/Page002/`，放 `Page002_原稿照片.jpg`；有插图就从原题截图裁出 `Page002_<题号>插图.png`
2. 复制 Page001.html 改成 Page002.html，**逐行照照片**写（先放大照片看清每处颜色）：
   - 一行 = 一条横线；换行位置照手写稿（跨行的词在朗读里会自动连读）
   - 颜色：题干说明 / 中文注释 / 圈正确答案 / × / 对调括号 = 金棕（`gold`）；Page 标题 / 日文句子 / 选项 / 波浪线 = 红（`red`）
   - **笔记**（隐藏笔记时消失、也不朗读）一律包在行内 `<span class="note">` 里 —— ⚠️ 别挂在整行 `.row` 上，会连横线一起藏掉
   - 要朗读的加 `data-say`：题干两行同一个 id（`A1-i`）、句子行 `A1-s`、选项 `A1-o1`〜`o4`（选项在同一行就挂在 `.opt` 上）；
     题号标签包 `<span class="nosay">A1：</span>`；下划线 `<span class="under">＿＿</span>` 会念「かせん」
   - 页尾两行 script（`audio/manifest.js` + `../_shared/say.js`）别漏
3. 导 PDF + 翻页图：`python tools\make_notes_pdf.py notes\Page002\Page002.html` → 4 个 PDF + `flip/` 4 张图，打开 PDF 看一遍
4. 生成朗读：`D:\A030_VOICEVOX\venv\Scripts\python.exe tools\make_notes_audio.py notes\Page002\Page002.html`
   → **打开 `audio/kana.txt` 逐段核对读音**（片假名 = 实际念法）；不对就在 say.js 里加读法替换，生成方法变了把脚本里 `GEN` +1
5. `notes/pages.js` 加 `'Page002'`
6. 验收：`D:\A030_VOICEVOX\venv\Scripts\python.exe tools\test_notes_book.py` → 6/6；看 `%TEMP%\notes_book_test\` 截图。
   有两页了，顺手测「全部朗读 → 第 1 页读完自动翻到第 2 页」（至今没测过）
7. 整个 `notes/` 复制到桌面 `日本語Daily_手写笔记\`，逐文件 md5 比对；commit + push；更新 WORKLOG

### 朗读（VOICEVOX）
- 为什么是它（11-10 实测 + 搜索）：CosyVoice 用中文音色念日语不准（14 段只对 1 段）；微软 Edge 语音准但只有 2 个音色且不开源；
  AivisSpeech 音质好但官方 mora 时长永远 0.0，做不了精确高亮。VOICEVOX：开源、离线、几十个角色、`audio_query` 给每个音的时长
- 引擎：`D:\A030_VOICEVOX\windows-cpu\run.exe`（0.26.1 CPU 版），脚本自己起、用完关；python 用 `D:\A030_VOICEVOX\venv`（soundfile/numpy/pypdf/websocket-client）
- 只读 `data-say`；`.note` / `.nosay` / `<rt>` 不读
- 生成方式（`make_notes_audio.py`）：词间加全角空格送进引擎（否则断错词，如「デパートでかいもの」→ でかい），
  再删掉这些空格造成的停顿（只留原文 。、）；「1・2・3・4」改念 いち、に、さん、よん（否则念成「いってん」）
- 缓存号 = sha1(GEN | 引擎版本 | 音色 | 要念的文字)，有就跳过；`--prune` 删没人用的旧音频（默认只报数）
- 高亮：每个词的开始时间 = 按「每个词几个音」在整句的音时间轴上切出来；`scaled=0` 表示每段都对得上（Page001 全部 0）
- 音色：脚本 `DEFAULT_VOICES` 6 个（四国めたん / ずんだもん / 春日部つむぎ / 冥鳴ひまり / 青山龍星 / 玄野武宏），`--voices 2,3` 指定；
  全部音色 id 在 `audio/voices.txt`。🔴 VOICEVOX 角色条款：用到哪个角色就要显示「音声：VOICEVOX:角色名」（书和单页都显示了）
- 语速在页面上用 `playbackRate` 调（0.6×〜1.3×，变速不变调），不重新生成

### 翻书（StPageFlip 画布模式）
- 翻页时画的是整页图（`flip/`），卷角 / 阴影 / 拖拽都在 canvas 上；**书停稳**（state=read）时，在看得到的页上叠真页面 iframe（朗读 / 高亮用），
  一开始卷角或拖页就藏起来。图和真页面由同一个 HTML 生成，所以看不出切换
- 🔴 **改了 PageNNN.html 必须重跑 make_notes_pdf.py**，否则翻页时露出旧图
- 坑（都踩过）：
  1. 画布模式库只在 `<canvas>` 上听「按下」→ 书角 / 书边的透明把手把 mousedown/touchstart **转发给 canvas**，否则拖不动
  2. 库的 `clear()` 原本把画布涂白 → 书两侧白边 → 本地副本改成 `clearRect`
  3. 库只听 window resize；工具栏字体加载后变矮、书区变大它不知道 → 画布被拉伸、真页面错位 → ResizeObserver + `flip.getUI().update()`
  4. iframe 里页面按 210mm = 793.7px 固定值缩放（用 offsetWidth 会量到自己 zoom 过的值）；书页尺寸变化不一定触发 iframe 的 resize → 每 0.3s 对一次
- 第一版用的是 HTML 模式（直接翻 iframe），他评价「丑陋、没对齐」→ 已整个换掉，别回退
- 书 ↔ 页的消息：书发 `{say: theme|clean|play|toggle|stop|voice|speed|hello}`；页回 `{say:'state', playing, active, voices…}` 和整页读完的 `{say:'done'}`

### 测试
- `tools/test_notes_book.py`：CDP 控制固定视口 headless Edge，模拟真实鼠标。6 项：停稳对齐 / 悬停卷角 / 拖过书脊翻页 / 换主题换图 / 朗读 / 窄屏单页。
  判据能红能绿：把「转发按下」那行弄坏的副本 → 第 3 项 FAIL、exit 1（`NOTES_BOOK=<副本路径>` 可测别的副本）
- 🔴 **别用 `msedge --screenshot` 验证书**：它截图时改视口，排版和截图不是同一尺寸，画面是错的（11-10 被骗过一次）
- 朗读读音：看 `audio/kana.txt`；要更硬的证据就用 Whisper 转写（CosyVoice 的 venv 里有：`D:\A029_CosyVoice\venv`，模型 small）

### Page002〜003（2026-11-12）要点 —— 下次加页 / 改页先看这里
- 现有 3 页：Page001（文字・語彙 A1〜A4）、Page002（文法 B1、B2、B3 前半）、Page003（B3 后半、読解 B4）。
  **PageNNN.html 就是源文件，直接改它**（11-12 第一次是用临时脚本拼的，脚本没进仓库，不要找）。
- 每页第一行 = 分类标题（「言語知識（文字・語彙）：」「言語知識（文法）・読解：」），**也朗读**（data-say="H"，他要求的）。
- 新记号（CSS 在 Page002/003 的 style 末尾）：.blank 填空线、.qbox 方框（□ / ？）、.ul 下划线、.wavyg 金棕波浪线、.ok（✓ 画在下一行，同 .x）、.heart。
- 「笔记」= 他的标注（中文、× ✓ 圈、♡↑、1 4 2 3、＊）。**原题里的日语（含 B2 下面「答えかた」例题那段）算正文，要朗读**（他 11-12 要求）。
- 选项一律每个单独一段 data-say（放一段会连读成「じしょをに、…」）。
- 选项 + 下一行的 ×/注释要对齐：用等宽格子（display:inline-block;width:24mm），注释列用固定宽度（B3 是 86mm）；他嫌「两个一行挤在一起」不好看。
- 朗读按注音念（say.js 读 ruby 的 rt）；引擎念错时 `<ruby data-yomi="カタカナ">`：入（はい）る → ハイ；句号「。」当符号念 → `<ruby data-yomi="まる">。<rt></rt></ruby>`。
  改完必看 audio/kana.txt。
- 🔴 他开着 PDF 查看器时 make_notes_pdf.py 会在「删旧 PDF」那步失败（WinError 32）→ 请他关 PDF，或在临时目录生成后覆盖拷回（覆盖写不会被拦）。
- 朗读交互（11-12）：点一句 = 从这句往下读；书记住读到哪（book-resume），按钮「▶ 接着上次读（P00N）」；任何时候只有一页在响（hushOthers）。
  改 say.js / book.html 后要同步到黄金眼合并本（它的 book.html 是改过的副本，函数要逐段照搬，**别漏 readFrom 上面的 resumeGet / resumeSet / hushOthers**）
- 黄金眼：11-12 他（另一个会话）把 p001〜p003 合成一本 `jp-n5-kaisetsu-all`；以后更新黄金眼 = 把 Daily 的 PageNNN 同步进 all 那本，见黄金眼 WORKLOG。

### 待他定 / 没做完
- 6 个音色留哪几个；两个男声（青山龍星、玄野武宏）Whisper 听出词间多了「お/あ」，可能是删停顿后的衔接杂音
- A4 选项下的波浪线（かいもの 等）隐藏笔记时要不要也藏
- ~~「整页读完自动翻页接着读」~~ 11-12 已实测通过（模拟 done 消息：第 1 页 → 第 2 页 → 翻页 → 第 3 页 → 停）
- 🔴 朗读按注音念：`<ruby>漢字<rt>かな</rt></ruby>` 念 rt；引擎把注音念错时加 `data-yomi="カタカナ"`（例：入（はい）る → data-yomi="ハイ"）

## 当前状态（2026-11-10）

- **当前 APP_VERSION = 18**（18 = 试卷每题答完马上显示对错、不能改，计时不限时；17 = 试卷 `window.EXAMS`（N5 官网样题 1〜14）；16 = 听力题 `layout: 'listening'` + `audio/`（只能听一次，音频用 JLPT 官网样题原始 mp3）；15 = 「正确答案是…」和错题集「答案…」显示注音，选项可以带 {…|…}；**每题解析末尾都要有「全文翻译」**（他 11-12 要求）；14 = 文章题插图原尺寸 + 【しつもん】拆到图下面、黑底标签，见 WORKLOG 11-12 第 15 条；13 = 文章题 `layout: 'passage'`：`sentence` 放整篇文章（`\n` 换行）全部展开、**不做滚动框**（他 11-12 要求），
  `□` = 红框空格、答完变绿填答案，`brief` = 列表里显示的那一句，见 WORKLOG 11-12 第 8 条；12 = 同 id 合并保留本地新字段 + 2099-12-31 = 锁定待定；11 = 电脑上两栏照原题截图一比一、页面加宽；9 = 小1 答完小动画；10 = 小1 答完照原题截图两栏竖排 + 题目字段 `kaisetsu`，见 WORKLOG 11-10 第 15 条）（version.txt 同步）。仓库只有 `main` 一个分支（他说「master 分支」指的就是它）
- 题目 18 道：Day1（11-06）新しい N5、通って N4；Day2（11-07）N5〜N1 各一道：ホテル、送ります、代表、種、挑んで；
  Day3（11-09）N5〜N1：うるさい（带插图）、レシート、助けて、収集、推測（朋友还没作答）；
  Day4（11-10）N5〜N1：デパート（言い換え）、しらせて（言い換え）、ぐっすり、名（語形成）、ややこしい；+ 小1 つる
- **各级别「文字・語彙」小题覆盖**（他会问「齐了没」）：N5 共 4 小题 → 1〜4 齐 ✅；N4 共 5 小题 → 缺 **5［用法］**；
  N3 有 1、2、3；N2 有 1、2、3；N1 有 1、2、3。截图顶部的数字条可看每级共几小题
- **「小1 こくご」级别**（11-10，APP_VERSION 8）：小学一年级国语，和 JLPT 同一题库，`level: '小1'`，排在 N5 前，颜色 `#69bdbc`。
  来源：「小1 こくご(ドリル)」→ ひらがな（1）ひらがな1，共 9 题，**已加 1 道（つる），剩 8 道等他发**；放出节奏（一天几道）他**还没定**。
  原题竖排，这里横排；插图按非白像素从截图裁（`images/sho1-*.png`）；解析 = 他发的中文 + 原题「こたえとかいせつ」一句。
  截图放 `screenshots/小1/` + 桌面 `日本語Daily_真题截图\小1\`（题目 / 解析 / 原题正解 / 课程页）
- **长选项排版**（11-10，APP_VERSION 8）：任一选项 >10 字 ⇒ `.opts.long` 一行一个、只在空格处断（言い換え题选项是整句）
- 解析写法：截图里开头「答案是…」那行不抄，其余逐字抄
- **题目插图**（11-09 加，APP_VERSION 5）：题目加 `image: 'images/<id>.png'`，图从截图裁出来放 `images/`。
  页面先读本地图，本地没有（旧安装）就改读 `raw.githubusercontent.com/.../main/images/...`；install.bat 会 xcopy `images/`。
  ⚠️ 版本 ≤4 的旧 index.html 不认 `image` 字段 → 只是看不到图，题照样能做；顶部会提示新版本
- Day3 五道的解析都已换成辐射蓝发来的版本（逐字抄）
- **教学模式「注音」**（11-09，APP_VERSION 7）：右上角小开关，存 `state.teach`。打开后题目句子、说明、选项里**所有汉字带注音**
  （考点也标，他拍板：教学模式就是用来学的），**外来语上面标英文原词**（蓝色斜体，`{クラス|class}`，注音是纯 ASCII 自动换样式）。
  数据在 `questions.js` 底部 `window.TEACH[id] = {instruction?, sentence?, options?}`，没写的字段显示原文；检查更新会一起拉。
  🔴 **每天加新题时要同时写 TEACH**，然后跑 `node tools/check_teach.js`：去掉注音后必须和原题逐字一样、不许有没注音的汉字
  （片假名无来源词只给 INFO，假词选项正常）。假词选项（守けて/拾集）按单字读音标
- **手写笔记书**：Page001（A1〜A4）、Page002〜003（B1〜B4，11-12）已做完，有朗读和翻书。详见下面「手写笔记书」一章
- 题库级别筛选（11-09，APP_VERSION 6）：可多选，存 `state.levels`；**只管题库列表和「复习」，「今日」不筛**（他拍板：
  否则没选的级别到期错题永远不出现）。「错题集」标签不显示红点数字（他要求）
- 微信结果已补录：Day1 新しい 对、通って 错（错题集，11-13 再出现）；Day2 五道全对 → 已掌握
- 从 Day2 起每天 N5〜N1 各一道（Day4 起另有小1）
- 汉字上方注音：`{漢字|かな}`（如 `{選|えら}`），渲染成 ruby；2026-11-08 加，APP_VERSION 3
- 级别标签用 JLPT 官方配色（取自官网按钮）：N1 `#5dae98` 绿、N2 `#e68329` 橙、N3 `#856ea5` 紫、N4 `#d57567` 红、N5 `#497ebe` 蓝；APP_VERSION 4
- 本地克隆在 `Desktop\japanese-learning-app`（带横杠）；git 默认凭据是另一个账号会 403，push 用 gh 的 token：
  `git -c credential.helper= -c "credential.helper=!f(){ echo username=x-access-token; echo password=$(gh auth token); }; f" push origin main`
