FROM python:3.8

LABEL maintainer="Ryan Peckham"

WORKDIR /src

COPY requirements.txt .

RUN pip install -r requirements.txt

# RUN apt update \
#     && apt-get install gcc git curl python3-venv -y \
#     && pip install --upgrade pip setuptools wheel poetry

COPY src/ .

CMD [ "python", "./bot.py" ] 