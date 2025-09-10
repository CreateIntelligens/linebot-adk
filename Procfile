# Heroku Procfile - 定義應用程式的啟動命令
# web: 表示這是一個 Web 應用程式
# 使用 Uvicorn ASGI 伺服器啟動 FastAPI 應用程式
# ${PORT:-8892} 表示使用環境變數 PORT，如果未設定則預設為 8892
web: uvicorn main:app --host=0.0.0.0 --port=${PORT:-8892}
