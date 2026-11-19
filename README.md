# SG Internship Radar

新加坡金融科技 / 金融 / 互联网实习雷达，附 JD 洞察与简历匹配。

在线访问：https://kristen0219.github.io/sg-internship-radar/

> **仅供个人使用。** 本项目是个人找实习用的整理工具，不是商业产品，也不代表任何公司或招聘平台。
> 岗位信息整理自 LinkedIn 公开职位，版权归原发布方所有；行业分类、匹配度等都是个人主观判断，仅作参考，请以原帖为准。
> 不保证信息准确、完整或及时，岗位可能已关闭。

## 功能

- 按行业（FinTech / Finance / Internet）、公司规模、岗位方向筛选，默认按发布时间排序
- 标出可兼职 / 弹性 / 远程的岗位，可收藏岗位（存在本地浏览器）
- JD 洞察：汇总近期产品 / 数据类实习 JD 的要求和技能出现频率
- 简历匹配：上传或粘贴简历，在浏览器本地做关键词匹配，简历不会上传

## 文件

- `index.html`：页面
- `jobs.json`：岗位数据
- `insights.json`：JD 洞察数据
- `scripts/`：每日更新脚本，流程见 [UPDATE.md](UPDATE.md)

## 每日更新

每天 21:00 在本机自动运行：抓取 LinkedIn 新加坡新发布的实习，分类后合并进 `jobs.json` 并推送，GitHub Pages 随之更新。

## 本地运行

页面用 `fetch` 读取 JSON，需要通过本地服务器打开（直接双击 html 会加载失败）：

```powershell
python -m http.server 8080
```

然后打开 http://localhost:8080
