# 日本語 Daily

JLPT 真题练习小软件：选答案 → 看解析 → 错题自动按周复习，连对 10 次移出错题集。

## 一键安装 / 更新（Windows）

按 `Win + R`，输入 `cmd` 回车，把下面这一行粘进去回车：

```
curl -sL -o "%TEMP%\jla.bat" https://raw.githubusercontent.com/mxxs109-ops/japanese-learning-app/main/install.bat && "%TEMP%\jla.bat"
```

会装到桌面的 `japanese learning app` 文件夹并自动打开。以后有新题，再跑一次同一行就更新，做题进度不会丢。

## 复习规则

- 新题第一次就做对 → 已掌握，不再出现（可在「题库」手动复习）
- 做错 → 进错题集，1 星期后出现
- 错题到期做对 → 连对 +1，下次间隔 2 周、3 周……
- 连对 10 次 → 移出错题集；中途做错 → 连对清零，下星期再来
