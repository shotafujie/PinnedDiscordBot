FROM python:3.11-slim

# 作業ディレクトリを設定
WORKDIR /app

# 必要なパッケージをインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションファイルをコピー
COPY main.py .

# ポートを公開（Koyebで必要）
EXPOSE 8000

# アプリケーションを実行
CMD ["python", "app/main.py"]
