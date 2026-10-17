# 维护说明

这个仓库是 [kelvint0714-arch 的 GitHub 主页](https://github.com/kelvint0714-arch)。风格取自《薫る花は凛と咲く》：桔梗、樱花、薰衣草，清晨的粉蓝天空与夜晚的靛蓝。所有花朵都由 `scripts/garden/` 里的代码绘制，不使用任何图片素材。

## 结构

| 部分 | 脚本 | 输出 |
| :--- | :--- | :--- |
| 页首视频横幅 | `scripts/build_banner.py` | `assets/banner.webp`、`assets/banner-static.webp` |
| 分节标题 | `scripts/build_sections.py` | `assets/sections/*.svg` |
| 花暦 / 言語の花束 / 花便り | `scripts/build_metrics.py` | `assets/metrics/*.svg`、`data/snapshot.json` |
| 公开仓库表 | `scripts/update_repositories.py` | `README.md` 中 `GARDEN-REPOS` 标记之间 |

`scripts/garden/` 是共用的绘图工具：`flora.py`（花的形状与动画）、`palette.py`（浅色/深色配色）、`text.py`（把字形转成路径，保证各浏览器显示一致）、`data.py`（读取公开的 GitHub 数据）。

每张 SVG 都有浅色、深色两版，README 用 `<picture>` 按访客的主题切换。动画的基础样式就是最终画面，访客开启「减少动态效果」时直接显示完成状态。

## 修改文字

分节标题的文字在 `garden.json`。改了日文后先运行一次：

```bash
python3 scripts/fetch_fonts.py
```

它会从 Google Fonts 重新下载只含所需汉字/假名的 Noto Serif JP 子集（字体均为 OFL 许可，许可文本在 `fonts/`）。然后重新生成：

```bash
python3 scripts/build_sections.py
```

## 页首视频横幅

主页最上方是你提供的视频片段，转换成循环播放的动图。

1. 把视频片段（mp4 / mov / webm）放进 `banners/`。视频本身不会提交到仓库（见 `.gitignore`），只提交转换后的图片。
2. 按需修改 `banners/config.json`：`start`（起始秒）、`duration`（时长）、`fps`、`width`、`aspect`（宽高比，现在是 16:9 保留完整画面；2.4 是更窄的电影比例）、`focus_y`（裁切的上下位置，0 顶部 – 1 底部）、`poster_at`（静止帧取第几秒）、`alt`（图片说明）、`credit`（显示在横幅下方的出处，比如原视频作者）。
3. 运行（需要 ffmpeg：`brew install ffmpeg`）：

```bash
python3 scripts/build_banner.py
```

脚本会裁切、缩放、加圆角和柔和的边缘渐隐，把结尾和开头交叉淡化成无缝循环，输出动态 WebP 和一张静止帧，并自动把横幅插入 README。文件超过约 9 MB 时会提示，减小 `duration`、`fps` 或 `width` 即可。`--remove` 可以撤下横幅。

## 自动更新

[Tend the garden](.github/workflows/garden.yml) 每天北京时间 06:23 运行，也会在修改 `garden.json`、`scripts/`、`fonts/` 后运行，或在 Actions 页面手动运行。它会先跑测试，再重新绘制所有 SVG、读取最新的公开数据、刷新仓库表，有变化就提交。

数据都是公开可见的内容：贡献日历从公开主页匿名读取，仓库、语言和动态来自公开 API（`GITHUB_TOKEN` 只用来提高频率上限）。读取失败时沿用 `data/snapshot.json` 里上一次的数据，卡片不会变空。

## 本地预览与测试

```bash
python3 -m pip install fonttools Pillow
python3 -m unittest discover -s scripts -p "test_*.py"
python3 scripts/build_metrics.py --offline   # 不联网，用快照重画卡片
```
