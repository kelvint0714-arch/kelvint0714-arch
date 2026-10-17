# 维护说明

这个仓库是 [kelvint0714-arch 的 GitHub 主页](https://github.com/kelvint0714-arch)。装饰结合《薫る花は凛と咲く》、和栗薫子的暖色横幅，以及用户提供的粉色花田与樱花参考：奶油白、深梅灰文字、灰玫瑰主花与淡紫陪衬。视觉采用柔和立体效果，以卷曲花瓣、暖光、自然弧线和前后遮叠表现体积。深色版使用梅灰底色。页首保留用户提供的视频横幅；其余花朵由 `scripts/garden/` 的代码绘制，参考图没有嵌入装饰素材。

## 视觉约定

- 分节标题采用浅浮雕衬线文字、柔圆编号章与舒展的弯枝。粉花大小错落、前后相叠，淡紫花作为陪衬。
- 指标卡共用大圆角、柔和面光、薄侧缘与扩散投影；文字保持足够对比。
- 花瓣用连续曲线、柔和渐变、内折暗部与透光边缘表现卷曲，叶片有弯曲中脉。小于 10px 半径的花朵使用简化花心和最多两层花瓣，确保小尺寸清楚。
- 花暦采用浅斜向投影的柔圆花床，保留七行星期映射和每个已有日期的独立标记。无贡献日为种子；四档花朵采用 GitHub 提供的等级，用株高、花冠大小和饱满程度区分。日历有独立的小花配色，浅色版增强粉色主体，深色版提升活跃花的亮度。
- 语言花束的百分比和细线条长度按公开非 fork 仓库的代码字节数计算。花束只承担视觉点缀，准确比例以数字与细线条为准。
- 花便り采用轻弯花茎时间轴和柔和浮起的记录底色。日历、语言及活动的数据获取、快照回退和每日自动更新流程保持一致。
- SVG 在静止时就是完整画面；入场动画使用短暂淡入与轻微舒展，少量大花缓慢摆动。开启「减少动态效果」时直接显示完成状态。

## 结构

| 部分 | 脚本 | 输出 |
| :--- | :--- | :--- |
| 页首视频横幅 | `scripts/build_banner.py` | `assets/banner.webp`、`assets/banner-static.webp` |
| 分节标题 | `scripts/build_sections.py` | `assets/sections/*.svg` |
| 花暦 / 言語の花束 / 花便り | `scripts/build_metrics.py` | `assets/metrics/*.svg`、`data/snapshot.json` |
| 公开仓库表 | `scripts/update_repositories.py` | `README.md` 中 `GARDEN-REPOS` 标记之间 |

`scripts/garden/` 是共用的绘图工具：`flora.py`（柔和立体花形与轻量动画）、`palette.py`（浅色/深色配色）、`depth.py`（圆润卡片、软投影与浅浮雕文字）、`text.py`（把字形转成路径，保证各浏览器显示一致）、`data.py`（读取公开的 GitHub 数据）。

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
