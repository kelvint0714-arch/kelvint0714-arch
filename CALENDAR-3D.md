# Bloom Calendar · 黑白漫画立体花园

本包只更新贡献日历，适用于此前的漫画主页（manga.py + manga_lettering.json）。
视频、头像、章节标题、仓库卡片、语言花束、活动记录、README 引用均不修改。

## 安装

目标仓库：kelvint0714-arch/kelvint0714-arch，不是 kelvint0714-arch.github.io。
解压后，在仓库根目录用 Add file → Upload files 上传 assets/ 与 scripts/ 两个文件夹，
保持包内目录结构并提交 main。不需要覆盖 README.md，不需要上传本说明或预览图。
不要只传 SVG：scripts/garden/calendar3d.py 和 scripts/build_metrics.py 一起上传，
后续每日刷新才能保持立体样式。

包中同时提供 assets/ink-v2/metrics/calendar-*.svg 和 assets/metrics/calendar-*.svg。
这两套是内容一致的日历兼容路径，避免旧 README 引用导致样式未更新。
每日脚本仍在原来的 ink-v2 目录生成其他图，只给日历额外写一份旧路径别名。

## 视觉变化

* 原平面小花点阵改成有侧面厚度的斜向花床。
* 每天保留一个独立小花台；贡献等级控制小花台、花茎高度和花朵饱满程度。
* 花朵采用立起的花茎、弯曲叶片、倾斜花冠和叠压花瓣；侧面使用排线与网点。
* 纯黑白：白纸、黑墨、无色彩渐变、无模糊滤镜，也没有新增持续动画。
* 字体延续现有哥特标题。此包不含任何字体文件。
* 桌面为整年一座花床，手机顺序分为两座半年度花床，不丢弃日期。

这是固定视角的立体矢量插画，不是需要 WebGL 的可旋转三维控件。

## 数据与验证

预览与随包 SVG 沿用上一版的日历快照：2025-10-12—2026-10-17、371 个日期、130 次贡献。
它不是实时抓取的新统计。所有日期的原始 count 与 level 均逐项保留，没有补造活跃日。
真实数据继续由原 data.collect() 流程采集，本包不包含也不覆盖 data/snapshot.json。
提交脚本会按仓库原有的工作流触发生成；网络失败时仍使用原快照回退策略。

本地已执行：44 项单元测试（含 18 项新增日历测试）、14 组 Chromium
屏幕宽度/主题组合、全部四个新日历与原 SVG 中 371 个日期的逐项对照。
浏览器测试使用生成的离线 HTML 和 SVG 图片，未验证远端 GitHub 部署或手机实机。

## 文件职责

scripts/garden/calendar3d.py：新日历绘制器。
scripts/build_metrics.py：把日历调用切到新绘制器，保留花束、记录、采集与回退函数。
scripts/test_calendar3d.py：日历和生成入口的回归测试；测试数据不会写入用户快照。
assets/**/calendar-*.svg：四种响应式资源，两套兼容路径。

## 回滚

在 GitHub 撤销此次提交即可；无需删除视频、头像或其他装饰。
旧平面日历绘制函数依然保留在 scripts/garden/manga.py 中。
