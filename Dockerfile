FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    swig \
    git \
    make \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY . /app

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

ENV PORT=9393

EXPOSE 9393

CMD ["python", "main.py"]
