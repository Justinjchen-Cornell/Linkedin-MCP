# LinkedIn 工作台

本地单人 LinkedIn 内容工作台。Plan 1 已实现：采集信息流、搜索结果、个人主页的帖子，存进本地 SQLite，并在本地网页搜索、筛选、看详情。AI 写稿、排期发布、数据复盘在 Plan 2/3。

## 前置

- Windows 11
- Python 3.12/3.13（`uv` 会自动管理）
- Node 20+
- Edge

## 启动后台

```powershell
scripts\start.ps1
```

打开 <http://127.0.0.1:8765>。

## 构建扩展

```powershell
scripts\build-extension.ps1
```

然后 Edge → `edge://extensions` → 打开“开发者模式” → “加载解压缩的扩展” → 选择 `extension/dist`。

## 首次使用

1. 启动后台，点扩展图标，确认显示“已连接”。
2. 打开 LinkedIn 信息流，点“采集本页”。
3. 到“设置”填本人 LinkedIn 主页 URL，添加 3–5 个关注词。
4. 点“跑一轮采集”，扩展会逐个打开后台标签页采集。
5. 回“情报库”搜索、筛选、看详情。

## 同步账号数据

1. 到“设置”填本人 LinkedIn 主页 URL。
2. 点扩展图标 →“同步账号数据”。
3. 打开 <http://127.0.0.1:8765/analytics> 看账号快照和帖子表现。

同步会抓：粉丝、连接、主页访问、帖子曝光、搜索曝光；最近 5 篇帖子的 impressions、触达、互动。每天 9 点（设置页可改）在浏览器打开时自动同步一次；单次最多 5 篇帖子指标，间隔约 20 秒。

## 写稿与发帖（B1）

1. 到“设置”配置 AI Base URL、模型和 API Key（不配置也能手写）。
2. 打开“草稿”新建一篇；编辑器里填主题/角度，点“生成 3 版”，选一版“采用”。
3. 在编辑器里选发布时间，加入排期。
4. 到点扩展会弹通知；打开 <http://127.0.0.1:8765/calendar>，点“复制并打开 LinkedIn”，粘贴后手动点 Post。
5. 发完回到排期页点“标记已发布”。

B1 不会自动点 LinkedIn 的发布按钮；自动填入发布框和图片上传在 B2。

## 系列与 3+2 周计划

- `/series`：建系列，填名称、slug、星期、模板；下一期编号自动递增。
- `/plan`：周一至周五 5 个槽位。深度槽位点“生成下一期”会按系列模板建草稿；轻量槽位点“新建轻量”。
- 编辑器里点“拆成 2 条轻量”，会从深度草稿生成一张数据卡 + 一条观点，不用从零写。

建议节奏：周一/三/五 深度（GOR Pulse / Energy Watch / AI-Credit），周二/四 轻量，周末不发。

## 图片、预览与自动填入

- 编辑器可以上传配图，右侧显示 LinkedIn 预览（210 字截断）和字符数。
- 排期表单会显示建议发布时间（历史不足时用默认的周二/三/四 9:00）。
- 日历里的“尝试自动填入”会打开 LinkedIn 并尝试填好正文/图片；找不到发布框时用“复制并打开 LinkedIn”兜底。
- 发布前请在 LinkedIn 里检查，确认后自己点 Post。

## 本地数据 API

所有数据可通过本地 REST API 读取，基地址 `http://127.0.0.1:8765/api/v1`。交互文档：<http://127.0.0.1:8765/docs>。

| 端点 | 用途 |
|---|---|
| `GET /api/v1/me` | 账号快照（粉丝/连接/主页访问/曝光/搜索） |
| `GET /api/v1/posts?q=&source=&own=&limit=&offset=` | 帖子列表/搜索 |
| `GET /api/v1/posts/{id}` | 帖子详情 + 评论 |
| `GET /api/v1/posts/{id}/metrics` | 该帖最新指标 |
| `GET /api/v1/people?q=` | 作者/评论者 |
| `GET /api/v1/comments?post_id=` | 评论 |
| `GET /api/v1/analytics/overview` | 账号趋势 |
| `GET /api/v1/analytics/posts` | 帖子表现 |
| `GET /api/v1/search?q=` | 全文搜索 |
| `GET /api/v1/export?format=csv\|json` | 导出帖子 |

### 实时抓取（异步任务）

扩展会轮询任务队列，打开对应 LinkedIn 页面抓取并回填。调用后约 30 秒内完成，用 `GET /api/v1/jobs/{id}` 取结果。

```bash
# 抓自己账号：账号快照 + 本人帖子
curl -X POST http://127.0.0.1:8765/api/v1/fetch -H "Content-Type: application/json" -d '{"type":"profile"}'

# 抓单帖详细指标（按帖子 id）
curl -X POST http://127.0.0.1:8765/api/v1/posts/1/fetch

# 批量抓最近 10 篇帖子的指标
curl -X POST http://127.0.0.1:8765/api/v1/fetch -H "Content-Type: application/json" -d '{"type":"all_post_metrics","limit":10}'

# 查任务
curl http://127.0.0.1:8765/api/v1/jobs/1
```

示例：

```bash
curl "http://127.0.0.1:8765/api/v1/me"
curl "http://127.0.0.1:8765/api/v1/posts?q=Energy&limit=5"
curl "http://127.0.0.1:8765/api/v1/export?format=csv" -o posts.csv
```

## 测试

```powershell
uv run pytest
cd extension
npm test
```

## 常见问题

- **popup 未连接**：后台没启动，或端口不是 8765。
- **采集 0 条**：先在 LinkedIn 页面点“选择器自检”；如果字段取不到，LinkedIn 可能改版，更新 `extension/src/shared/selectors.ts`。
- **出现验证页**：工具会停止并通知，手动完成验证后再采集。
- **Edge 加载扩展失败**：确认 `npm run build` 成功，加载的是 `extension/dist`，不是 `extension`。

## 已知限制

- 本期只做采集与情报库；AI 写稿、发布确认、数据复盘在后续计划。
- 不做自动点赞、评论、关注、私信。
