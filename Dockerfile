FROM python:3.10.14-slim

COPY modules /modules

COPY autoBaseline.py autoBaseline.py

RUN pip install requirements.txt

ENTRYPOINT  ["python", "./autoBaseline.py"]