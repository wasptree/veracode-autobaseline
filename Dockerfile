FROM python:3.10.14-slim

WORKDIR /github/workspace

COPY modules modules

COPY autoBaseline.py autoBaseline.py

COPY requirements.txt requirements.txt

RUN pip install -r /github/workspace/requirements.txt

ENTRYPOINT ["python", "/github/workspace/autoBaseline.py"]