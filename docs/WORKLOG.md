# WORKLOG · 日本語 Daily

## 2026-11-09（周一）· Day3

1. 开工先 `git fetch`：GitHub 比这份本地克隆多 8 个提交（另一个会话在 `Desktop\japanese-learning-app` 做的 Day2 五题、注音、官方配色）→ `merge --ff-only` 后再改
2. 加 Day3 N5「ここは（　）です。べんきょうできません。」答案 3 うるさい；解析是我写的（截图没给解析）
3. 题目插图支持：`image` 字段 + `images/n5-moji3-urusai.png`（从截图按非白像素自动裁边，575×324）；
   本地图加载失败 → 自动改读 GitHub raw；install.bat 加 xcopy images。APP_VERSION 4→5，version.txt 同步
4. 句子换行：`word-break: keep-all` + `overflow-wrap: anywhere`，只在空格处断（原来断成「できませ／ん。」）
5. 实测（headless Edge，自动点「开始练习」）：带图本地 ✅；删掉 images 文件夹 → 图从 GitHub 加载 ✅（raw 200，91969B）；
   install.bat 回读 crlf 59 / lf_only 0 / ctrl 0 / nonascii 0。手机宽度截图被切边，判断是无头窗口最小宽度的假象，**未验证**
6. 补 Day3 N4〜N1：レシート / 助けて（{困|こま} 注音）/ 収集 / 推測；うるさい、推測 的解析换成他发来的官方版（替掉我写的）。
   node 校验 12 题 id 不重复、5 道答案序号对；页面今日队列「1 / 5」。只改题库，APP_VERSION 不变（5）
7. 他要求：①「错题集」标签去掉红点数字 ② 题库按级别筛选（他拍板：**可多选**；**「今日」不跟着筛选**）。
   实现：题库顶部「全部 / N5〜N1」按钮，选中用级别官方色；`state.levels` 存选择（空 = 全部，五个全选也归为全部），
   只影响题库列表和「复习」。APP_VERSION 5→6。
   实测（headless 自动点 题库→N4→N5）：题库 · 6、只剩 N5/N4 ✅；再点「复习」→「1 / 6」✅；红点消失 ✅
8. 整理真题原图到桌面 `日本語Daily_真题截图\N5〜N1`（不在仓库里，公开仓库不放截图）：12 题 × 题目+解析 = 24 张齐。
   N4 通って 的题目没有原图，从微信截图裁的；Day2 四题的 8 张是他补发的（另一个会话的记录不在本机）
9. 教学模式「注音」开关（APP_VERSION 7）：手工给 12 题写 TEACH 注音版（汉字注音 + 外来语英文原词 bus/hotel/class/supermarket/register/receipt）。
   新增 `tools/check_teach.js`：真文件 [OK]；故意改一个字 + 删一个注音的副本 → 两条都报 [FAIL] exit=1 ✅（判据能红能绿）。
   截图验 N4 レシート（外来语蓝字）、N1 推測（说明/句子/选项全注音）✅；选项和说明的注音字号调大
10. 他要求截图也上 GitHub（推翻第 8 条的「仓库不放截图」）：24 张复制进 `screenshots/N5〜N1`（2.9M），
    与桌面文件夹 md5 逐个一致 ✅；已确认没有微信聊天内容（通って 只裁了题目卡片）；install.bat 只拷 images/，截图不进软件

## 2026-11-06（周五）· 建项目

**起因**：辐射蓝在微信每天给朋友发一道 JLPT 真题，要做成能选答案、看解析、带错题集和按周复习的小软件。

**做了什么**
1. 新建 `Desktop\japanese learning app`：`index.html` + `questions.js` + `srs.js`，纯静态，双击打开
2. 录入 3 道题（解析逐字取自他的截图）：新しい N5、通って N4（今天）、ホテル N5（11-07 解锁）
3. 复习规则写进 `srs.js`（见 HANDOFF「复习规则」）；node 单测全过（`[OK] all srs tests passed`）
4. 按他「先理解一下，做成美观简约的小程序」重做界面：米白底 + 黑色主按钮，三个标签页 今日 / 错题集 / 题库，答题页照真题版式
5. 补录微信结果：新しい 选 1 对；通って 选 1 むかって 错（正确 2 かよって）
   - 🐞 第一版补录写成「只补没有记录的题」，而他在补录前已经在浏览器里两题都点对了 ⇒ 补录被跳过，显示「已掌握 2、错题集 0」
   - 修法：改成每条强制写入一次（`state.pastApplied`）。用 headless Edge 先注入「两题都已掌握」的旧进度再打开 → 显示错题集 1、已掌握 1 ✅
6. 按他要求删掉首页的规则说明卡片和「导出/导入进度」按钮
7. 按钮调整：「复习已掌握的」「全部练一遍」从小号改正常大小，文字改成「复习」「练习」；「去题库复习」从白底改黑底
8. 一键安装：`install.bat`（ASCII + CRLF，已校验 crlf 45 / lf_only 0 / nonascii 0）+ README 写命令
9. git 本地初始化提交；建公开仓库被权限拦截两次 → 辐射蓝自己跑 `gh repo create ... --public --source=. --push`，已上线
10. 🐞 实测 install.bat：`tar: Cannot connect to C: resolve failed` —— 调到了 Git 的 GNU tar。改成写死 `%SystemRoot%\System32\curl.exe / tar.exe`
    - 改的时候 bash heredoc 又把 `\t` 吃成了 TAB，回读控制字符计数抓到，改用 Write 写的脚本修
12. 题库「复习」改成：**所有已解锁的题随机顺序**出（原来只出已掌握的）；删掉错题集底部那行手动练说明
13. 桌面图标：用他给的 9 白点截图（105×96）重做 `icon.ico/icon.png`（背景放大+模糊、9 个点按原位置重画成清晰的、圆角）。
    install.bat 新增：拷 icon、写 `desktop.ini` 给文件夹换图标、在桌面建「日本語 Daily」快捷方式（直接打开 index.html）。
    本地 zip 实测：首装 + 再装（更新）都 exit=0，快捷方式目标/图标正确，不重复。`desktop.ini` 进 .gitignore
14. 一键检查更新（APP_VERSION = 2，version.txt = 2）：新题点一下/打开自动就到；程序改了提示复制安装命令。
    实测（headless Edge，真连 GitHub）：A 本地删掉 ホテル → 自动拿回，显示「拿到 1 道新题」✅；
    B 把 APP_VERSION 调成 -1 → 出现「程序有新版本 + 复制安装命令」✅
11. ✅ 实测（从 GitHub 按提交号下载 install.bat，只把安装目录改到临时目录）：exit=0、4 秒、3 个文件与 HEAD 逐字节一致、倒计时 3/2/1 后关窗

**🔙 回滚**：git 历史在仓库里，`git log` 逐条可回。
