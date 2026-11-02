# LinkedIn 工作台

本地 LinkedIn 内容工作台：采集、选题、写稿、排期、半自动发布与复盘。

## 开发

```powershell
uv sync
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8765
```

打开 `http://127.0.0.1:8765`。

## 测试

```powershell
uv run pytest -v
```
