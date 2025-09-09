FROM python:3.10.17

# 設置工作目錄
WORKDIR /app

# 先複製 requirements.txt 來利用 Docker 緩存
COPY requirements.txt .

# 安裝必要的套件
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# 創建非 root 用戶來執行應用（可選，提高安全性）
RUN groupadd -r louis && useradd -r -g louis louis
RUN chown -R louis:louis /app
USER louis

EXPOSE 8080

# 默認命令（會被 docker-compose.yml 覆蓋）
CMD ["uvicorn", "main:app", "--host=0.0.0.0", "--port=8080"]