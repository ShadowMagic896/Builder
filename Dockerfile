FROM python:3.8

LABEL maintainer="Ryan Peckham"

COPY data/requirements.txt .

RUN pip install -r requirements.txt

RUN pip install --upgrade pip setuptools wheel poetry

COPY ./ .

CMD [ "python", "bot.py" ] 