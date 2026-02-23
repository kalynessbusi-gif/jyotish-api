FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    make \
    swig \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY . /app

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

ENV PORT=9393
EXPOSE 9393

CMD ["gunicorn", "-b", "0.0.0.0:9393", "main:app"]
