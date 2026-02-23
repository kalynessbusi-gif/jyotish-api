FROM python:3.10-slim

WORKDIR /app

# Installer dépendances système
RUN apt-get update && apt-get install -y \
    build-essential \
    wget \
    gcc \
    make \
    && rm -rf /var/lib/apt/lists/*

# Télécharger Swiss Ephemeris
RUN wget https://www.astro.com/ftp/swisseph/swe_unix_src_2.10.03.tar.gz \
    && tar xzf swe_unix_src_2.10.03.tar.gz \
    && cd swe_unix_src_2.10.03/src \
    && make swetest \
    && cp swetest /app/

# Copier projet
COPY . /app

# Installer Python deps
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

ENV PORT=9393
EXPOSE 9393

CMD ["python", "main.py"]
