# SG Internship Radar

新加坡金融科技 / 金融 / 互联网实习雷达，附 JD 洞察与简历匹配。

- `index.html` — 页面
- `jobs.json` — 岗位数据
- `insights.json` — JD 洞察数据

## 本地运行

页面用 `fetch` 读取 JSON，需要通过本地服务器打开（直接双击 html 会加载失败）：

```powershell
python -m http.server 8080
```

然后打开 http://localhost:8080

## 与线上版的差异

线上 Artifact 版依赖 claude.ai 运行时（`claude.use`）。本地运行时：

- 收藏只保存在浏览器 localStorage，不跨设备同步
- 「AI 深度分析」按钮不会出现；关键词简历匹配照常可用
