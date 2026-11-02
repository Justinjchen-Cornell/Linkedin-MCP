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
