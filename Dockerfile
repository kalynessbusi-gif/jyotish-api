FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    build-essential gcc make wget git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN git clone https://github.com/aloistr/swisseph.git /tmp/swisseph \
    && cd /tmp/swisseph \
    && make swetest \
    && cp swetest /app/swetest \
    && chmod +x /app/swetest \
    && rm -rf /tmp/swisseph

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["flask", "run", "--host=0.0.0.0", "--port=9393"]
```

---

## requirements.txt
```
flask>=2.3.0
