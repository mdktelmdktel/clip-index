#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ClipIndex · 素材管家
扫描录像文件夹，生成一份本地高光清单网页。

用法:
    python clip_index.py "D:\\OBS录像"
    python clip_index.py "D:\\OBS" -r --out D:\\cut\\index.html

作者: DeepSeek · MIT License
"""
import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

VIDEO_EXTS = {".mp4", ".mkv", ".mov", ".avi", ".webm", ".flv", ".ts", ".m4v", ".wmv"}
PLAYABLE_EXTS = {".mp4", ".m4v", ".webm", ".mov"}

PAGE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>素材管家 · __COUNT__ 条素材</title>
<style>
:root{--bg:#14161a;--panel:#1d2027;--line:#333a46;--ink:#c8ccd4;--dim:#7d8696;--acc:#d9a441;--hot:#e0574f;}
*{box-sizing:border-box;}
body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.6 Consolas,"Courier New","Microsoft YaHei",monospace;}
header{position:sticky;top:0;z-index:9;display:flex;flex-wrap:wrap;gap:10px;align-items:center;justify-content:space-between;padding:12px 16px;background:rgba(20,22,26,.95);border-bottom:1px solid var(--line);}
h1{margin:0;font-size:15px;font-weight:normal;letter-spacing:1px;}
h1 b{color:var(--hot);}
#stat{color:var(--dim);font-size:13px;}
.tools{display:flex;gap:8px;align-items:center;flex-wrap:wrap;}
input[type=text],textarea{background:var(--panel);border:1px solid var(--line);color:var(--ink);padding:6px 8px;font-family:inherit;font-size:13px;outline:none;}
input[type=text]:focus,textarea:focus{border-color:var(--acc);}
button{background:var(--panel);border:1px solid var(--line);color:var(--ink);padding:6px 12px;font-family:inherit;font-size:13px;cursor:pointer;}
button:hover{border-color:var(--acc);color:#fff;}
button:disabled{opacity:.4;cursor:not-allowed;}
label{font-size:13px;color:var(--dim);cursor:pointer;user-select:none;}
main{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:14px;padding:16px;}
.card{background:var(--panel);border:1px solid var(--line);border-radius:6px;overflow:hidden;display:flex;flex-direction:column;}
.card.starred{border-color:var(--acc);box-shadow:0 0 0 1px var(--acc) inset;}
.media{background:#0d0f12;min-height:150px;display:flex;align-items:center;justify-content:center;}
.media video{width:100%;max-height:240px;display:block;background:#000;}
.media .noplay{color:var(--dim);font-size:12px;padding:20px;text-align:center;word-break:break-all;}
.meta{padding:8px 10px 0;display:flex;justify-content:space-between;gap:8px;flex-wrap:wrap;}
.name{word-break:break-all;font-size:13px;}
.sub{color:var(--dim);font-size:12px;white-space:nowrap;}
.row{display:flex;gap:6px;padding:8px 10px 0;align-items:center;}
.row button{padding:4px 8px;font-size:12px;}
.star-on{color:var(--acc);border-color:var(--acc);}
.ts{width:80px;text-align:center;}
.note{margin:8px 10px 10px;width:calc(100% - 20px);resize:vertical;}
.empty{padding:60px;text-align:center;color:var(--dim);}
footer{padding:20px;color:var(--dim);font-size:12px;text-align:center;}
</style>
</head>
<body>
<header>
  <h1>素材管家 <b>//</b> <span id="stat">__COUNT__ 条 · __TOTAL__ · 扫描于 __NOW__</span></h1>
  <div class="tools">
    <input id="q" type="text" placeholder="搜索文件名…">
    <label><input type="checkbox" id="only"> 只看高光</label>
    <button id="export">导出剪辑清单</button>
  </div>
</header>
<main id="grid"></main>
<div id="empty" class="empty" style="display:none">没扫到能索引的视频。</div>
<footer>ClipIndex · 标记和备注存在浏览器本地（localStorage），不会上传 · 生成于 __NOW__</footer>
<template id="card">
  <article class="card">
    <div class="media"></div>
    <div class="meta"><span class="name"></span><span class="sub"></span></div>
    <div class="row">
      <button class="star">★ 高光</button>
      <button class="stamp">⏱ 记时间</button>
      <input class="ts" type="text" placeholder="00:00">
    </div>
    <textarea class="note" rows="2" placeholder="备注：这段里发生了什么…"></textarea>
  </article>
</template>
<script>
var CLIPS = __CLIPS__;
var KEY = "clipindex::";
function state(id){
  try { return JSON.parse(localStorage.getItem(KEY + id) || "{}"); } catch(e){ return {}; }
}
function save(id, st){
  try { localStorage.setItem(KEY + id, JSON.stringify(st)); } catch(e){}
}
function fmtTime(s){
  s = Math.max(0, Math.floor(s));
  var h = Math.floor(s/3600), m = Math.floor((s%3600)/60), sec = s%60;
  function p(n){ return (n<10?"0":"")+n; }
  return h > 0 ? h+":"+p(m)+":"+p(sec) : p(m)+":"+p(sec);
}
function marked(st){ return st.star || (st.note && st.note.trim()) || (st.ts && st.ts.trim()); }

var grid = document.getElementById("grid");
var tpl = document.getElementById("card");
var showOnly = false, query = "";

function render(){
  var frag = document.createDocumentFragment();
  var shown = 0;
  CLIPS.forEach(function(c){
    var st = state(c.id);
    if (showOnly && !st.star) return;
    if (query && c.name.toLowerCase().indexOf(query) < 0) return;
    shown++;
    var node = tpl.content.firstElementChild.cloneNode(true);
    var media = node.querySelector(".media");
    var vv = null;
    if (c.playable) {
      vv = document.createElement("video");
      vv.controls = true;
      vv.preload = "metadata";
      vv.src = c.rel;
      media.appendChild(vv);
    } else {
      var d = document.createElement("div");
      d.className = "noplay";
      d.textContent = "浏览器放不了这种格式，用播放器直接开：" + c.rel;
      media.appendChild(d);
    }
    node.querySelector(".name").textContent = c.name;
    node.querySelector(".sub").textContent = c.date + " · " + c.size + (c.duration ? " · " + fmtTime(c.duration) : "");
    var star = node.querySelector(".star");
    var stamp = node.querySelector(".stamp");
    var ts = node.querySelector(".ts");
    var note = node.querySelector(".note");
    if (st.star) { node.classList.add("starred"); star.classList.add("star-on"); }
    ts.value = st.ts || "";
    note.value = st.note || "";
    star.addEventListener("click", function(){
      st.star = !st.star;
      save(c.id, st);
      node.classList.toggle("starred", !!st.star);
      star.classList.toggle("star-on", !!st.star);
      if (showOnly && !st.star) node.remove();
    });
    if (vv) {
      stamp.addEventListener("click", function(){
        ts.value = fmtTime(vv.currentTime);
        st.ts = ts.value;
        save(c.id, st);
      });
    } else {
      stamp.disabled = true;
      stamp.title = "这种格式浏览器放不了";
    }
    ts.addEventListener("input", function(){ st.ts = ts.value; save(c.id, st); });
    note.addEventListener("input", function(){ st.note = note.value; save(c.id, st); });
    frag.appendChild(node);
  });
  grid.textContent = "";
  grid.appendChild(frag);
  document.getElementById("empty").style.display = shown ? "none" : "block";
}

document.getElementById("q").addEventListener("input", function(){
  query = this.value.trim().toLowerCase();
  render();
});
document.getElementById("only").addEventListener("change", function(){
  showOnly = this.checked;
  render();
});

document.getElementById("export").addEventListener("click", function(){
  var groups = {};
  var n = 0;
  CLIPS.forEach(function(c){
    var st = state(c.id);
    if (!marked(st)) return;
    n++;
    (groups[c.day] = groups[c.day] || []).push({c:c, st:st});
  });
  if (!n) { alert("还没有标记任何高光/备注/时间点。先标几张卡片再导出。"); return; }
  var lines = ["# 剪辑清单", "", "生成时间：" + "__NOW__", "", "共 " + n + " 条。时间点=播放器进度，直接对着剪。", ""];
  Object.keys(groups).sort().reverse().forEach(function(day){
    lines.push("## " + day, "");
    groups[day].forEach(function(it){
      var mark = it.st.star ? "★ " : "- ";
      var t = (it.st.ts && it.st.ts.trim()) ? " @" + it.st.ts.trim() : "";
      var note = (it.st.note && it.st.note.trim()) ? " — " + it.st.note.trim().replace(/\r?\n/g, " ") : "";
      lines.push(mark + "`" + it.c.name + "`" + t + note + "  ");
      lines.push("  路径: " + it.c.rel + "  ");
    });
    lines.push("");
  });
  var md = lines.join("\n");
  try {
    var p = navigator.clipboard && navigator.clipboard.writeText(md);
    if (p && p.catch) p.catch(function(){});
  } catch(e){}
  var blob = new Blob([md], {type: "text/markdown;charset=utf-8"});
  var a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "剪辑清单.md";
  document.body.appendChild(a);
  a.click();
  a.remove();
});

render();
</script>
</body>
</html>
"""


def human_size(n):
    n = float(n)
    for unit in ("B", "KB", "MB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024.0
    return f"{n:.1f} GB"


def ffprobe_duration(path):
    try:
        p = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
            capture_output=True, text=True, timeout=20)
        v = float(p.stdout.strip())
        return round(v, 1) if v > 0 else None
    except Exception:
        return None


def scan(root, recursive):
    it = root.rglob("*") if recursive else root.glob("*")
    files = [p for p in it if p.is_file() and p.suffix.lower() in VIDEO_EXTS]
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    clips = []
    for p in files:
        st = p.stat()
        rel = p.relative_to(root).as_posix()
        mtime = datetime.fromtimestamp(st.st_mtime)
        clips.append({
            "id": rel,
            "name": p.name,
            "rel": rel,
            "bytes": st.st_size,
            "size": human_size(st.st_size),
            "date": mtime.strftime("%Y-%m-%d %H:%M"),
            "day": mtime.strftime("%Y-%m-%d"),
            "playable": p.suffix.lower() in PLAYABLE_EXTS,
        })
    return clips


def build_html(clips):
    total = sum(c["bytes"] for c in clips)
    data = json.dumps(clips, ensure_ascii=False).replace("</", "<\\/")
    return (PAGE
            .replace("__CLIPS__", data)
            .replace("__COUNT__", str(len(clips)))
            .replace("__TOTAL__", human_size(total))
            .replace("__NOW__", datetime.now().strftime("%Y-%m-%d %H:%M")))


def main():
    ap = argparse.ArgumentParser(description="扫描录像文件夹，生成高光清单网页 (ClipIndex)")
    ap.add_argument("folder", help="录像所在文件夹")
    ap.add_argument("-r", "--recursive", action="store_true", help="包含子文件夹")
    ap.add_argument("-o", "--out", default=None, help="输出 html 路径（默认写到素材文件夹里）")
    ap.add_argument("--duration", action="store_true", help="用 ffprobe 读取视频时长（需要 ffmpeg，较慢）")
    args = ap.parse_args()

    root = Path(args.folder).expanduser()
    if not root.is_dir():
        print("文件夹不存在: " + str(root))
        return 1
    root = root.resolve()

    out = Path(args.out).expanduser().resolve() if args.out else root / "clip-index.html"

    clips = scan(root, args.recursive)
    if args.duration:
        for c in clips:
            c["duration"] = ffprobe_duration(root / c["id"])
    for c in clips:
        try:
            c["rel"] = Path(os.path.relpath(root / c["id"], out.parent)).as_posix()
        except ValueError:
            c["rel"] = (root / c["id"]).as_posix()

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(build_html(clips), encoding="utf-8")
    print("OK: {} clips -> {}".format(len(clips), out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
