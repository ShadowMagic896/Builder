FROM python:3.10

RUN pip install --upgrade pip

CMD [ "python", "./main.py" ] 