FROM python:3.11-slim

WORKDIR /app

# Install fonts for Pillow
RUN apt-get update && apt-get install -y fonts-dejavu && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .
COPY supervisor_tools.py .

CMD ["python", "main.py"]
