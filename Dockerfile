FROM python:3.10-slim

WORKDIR /app

# dépendances système
RUN apt-get update && apt-get install -y \
    build-essential \
    wget \
    unzip \
    gcc \
    make \
    && rm -rf /var/lib/apt/lists/*

# télécharger Swiss Ephemeris (source officielle miroir)
RUN wget https://github.com/aloistr/swisseph/archive/refs/heads/master.zip \
    && unzip master.zip \
    && cd swisseph-master \
    && make swetest \
    && cp swetest /app/

# copier projet
COPY . /app

# python deps
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

ENV PORT=9393
EXPOSE 9393

CMD ["python", "main.py"]
