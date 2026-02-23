FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    make \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Swiss Ephemeris (source officielle GitHub)
RUN wget https://github.com/aloistr/swisseph/archive/refs/heads/master.tar.gz -O swisseph.tar.gz

RUN tar -xzf swisseph.tar.gz && \
    cd swisseph-master && \
    make && \
    cp swetest /app/swetest && \
    chmod +x /app/swetest

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 9393

CMD ["python", "main.py"]
