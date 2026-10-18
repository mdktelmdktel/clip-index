# ClipIndex · 素材管家

把一文件夹的录像，变成一份"能点名"的高光清单。

录了一堆联机素材，想剪的时候翻半天找不到有意思的那几分钟？跑一下这个脚本，生成一个本地网页：所有素材按时间倒序排好、点开即看、标上高光、记下时间点，一键导出剪辑清单。

## 功能

- 扫描文件夹里的视频：mp4 / mkv / mov / avi / webm / flv / ts / m4v / wmv
- 生成的网页里直接预览播放（mp4 / mov / webm 系；mkv、avi 等只做索引并给出路径）
- ★ 高光标记，⏱ 一键把播放进度记进时间点，备注随便写
- 搜索过滤、只看高光
- 一键导出 `剪辑清单.md`：按日期分组，含 ★ 标记、时间点和备注，直接对着剪
- 标记和备注存在浏览器 localStorage，纯本地，不联网、不上传
- 零依赖，只用 Python 标准库（3.8+）

## 使用

```bash
python clip_index.py "D:\OBS录像"
```

然后打开素材文件夹里生成的 `clip-index.html`，双击即可。

可选参数：

| 参数 | 说明 |
| --- | --- |
| `-r, --recursive` | 包含子文件夹 |
| `-o, --out` | 输出 html 的路径（默认写到素材文件夹里） |
| `--duration` | 用 ffprobe 读视频时长（需要装过 ffmpeg，会慢一点） |

## 注意

- 如果你双击打开后浏览器禁用了本地存储（少数情况），改用本地服务器打开：
  `python -m http.server --directory "你的素材文件夹"`，然后访问 `http://localhost:8000/clip-index.html`
- 标记数据跟着浏览器走，换机器前记得先导出剪辑清单。

## License

MIT · Author: DeepSeek
