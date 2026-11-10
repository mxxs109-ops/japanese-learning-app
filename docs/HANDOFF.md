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
   命名 `DayN_MM-DD_单词_1题目.png` / `_2解析.png`。install.bat 不拷 screenshots/，不进软件
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

## 当前状态（2026-11-10）

- **当前 APP_VERSION = 8**（version.txt 同步）。仓库只有 `main` 一个分支（他说「master 分支」指的就是它）
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
- **手写笔记电子版**（11-09 起）：`notes/PageNNN/` = 原稿照片 `PageNNN_原稿照片.jpg` + 排版源 `PageNNN.html` +
  两个 PDF（`_照片配色.pdf` 纸色+金棕/红墨水；`_白底.pdf` 白纸淡线，金棕→黑、红→正蓝）。桌面 `日本語Daily_手写笔记\PageNNN\` 同一份。
  导出：`python tools/make_notes_pdf.py notes/PageNNN/PageNNN.html`。HTML 里一行 = 本子一条横线，换行照手写稿；
  颜色约定：题干说明/中文注释/圈正确答案/×/对调括号 = 金棕；Page 标题/日文句子/选项/波浪线 = 红。
  「隐藏笔记」（11-09 加）：`&clean=1` / 屏幕右上角按钮，隐藏所有 `class="note"`（中文注释）+ 圈答案 + × + 对调括号，题目和下划线照旧；
  导出共 4 个 PDF（照片配色 / 白底 × 有笔记 / 隐藏笔记）。题目插图放 `PageNNN_A3插图.png`（原图原色）
  **默认 = 白底 + 隐藏笔记**（他定）；`?theme=photo` / `&clean=0` 切过去。插图只占该题的「说明第 2 行 + 句子 + 选项」三行，
  上下贴横线不多占行，紧跟文字右边；显示笔记时右移让开中文注释。题目句子里被考的词用红色波浪线（新しい、ほてる）
  **Page001 已抄完**（11-10，A1〜A4：新しい / ほてる / うるさい / デパート）。A4 选项里的波浪线（かいもの 等）隐藏笔记时也保留——
  他还没表态，若要算笔记就加 `note`。⚠️ `note` 只能挂在行内 span 上，挂在整行 `.row` 上会连横线一起藏掉。
  下一页 = 新建 `notes/Page002/`，照 Page001 的结构；他发照片后：放原稿照片 → 写 HTML → 导 4 个 PDF → 两处同步（md5 比对）
- 题库级别筛选（11-09，APP_VERSION 6）：可多选，存 `state.levels`；**只管题库列表和「复习」，「今日」不筛**（他拍板：
  否则没选的级别到期错题永远不出现）。「错题集」标签不显示红点数字（他要求）
- 微信结果已补录：Day1 新しい 对、通って 错（错题集，11-13 再出现）；Day2 五道全对 → 已掌握
- 从 Day2 起每天 N5〜N1 各一道（Day4 起另有小1）
- 汉字上方注音：`{漢字|かな}`（如 `{選|えら}`），渲染成 ruby；2026-11-08 加，APP_VERSION 3
- 级别标签用 JLPT 官方配色（取自官网按钮）：N1 `#5dae98` 绿、N2 `#e68329` 橙、N3 `#856ea5` 紫、N4 `#d57567` 红、N5 `#497ebe` 蓝；APP_VERSION 4
- 本地克隆在 `Desktop\japanese-learning-app`（带横杠）；git 默认凭据是另一个账号会 403，push 用 gh 的 token：
  `git -c credential.helper= -c "credential.helper=!f(){ echo username=x-access-token; echo password=$(gh auth token); }; f" push origin main`
