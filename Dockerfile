FROM python:3.10-slim

WORKDIR /app

# Installer dépendances système
RUN apt-get update && apt-get install -y \
    gcc \
    make \
    wget \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Télécharger Swiss Ephemeris
RUN wget https://www.astro.com/ftp/swisseph/swe_unix_src_2.10.03.tar.gz \
    && tar xzf swe_unix_src_2.10.03.tar.gz

# Compiler swetest
RUN cd swe_unix_src_2.10.03 && \
    make swetest && \
    cp swetest /app/swetest

# Installer Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier ton code
COPY . .

EXPOSE 9393

CMD ["python", "main.py"]
