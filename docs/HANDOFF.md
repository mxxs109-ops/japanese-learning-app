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
3. `git commit` + `git push` —— **只改题目不用让朋友重装**：App 打开时自动检查、或点右上角「检查更新」，就从 GitHub 拿最新 `questions.js`

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

## 当前状态（2026-11-08）

- 题目 7 道：Day1（11-06）新しい N5、通って N4；Day2（11-07）N5〜N1 各一道：ホテル、送ります、代表、種、挑んで
- 微信结果已补录：Day1 新しい 对、通って 错（错题集，11-13 再出现）；Day2 五道全对 → 已掌握
- 从 Day2 起每天 N5〜N1 各一道
- 原题汉字上方的注音（如 選に「えら」）软件不支持，写成括号「選（えら）ばれた」
- 本地克隆在 `Desktop\japanese-learning-app`（带横杠）；git 默认凭据是另一个账号会 403，push 用 gh 的 token：
  `git -c credential.helper= -c "credential.helper=!f(){ echo username=x-access-token; echo password=$(gh auth token); }; f" push origin main`
