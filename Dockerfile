FROM python:3.10.14-slim

COPY requirements.txt /requirements.txt

RUN pip install -r requirements.txt

COPY modules /modules

COPY autoBaseline.py /autoBaseline.py

ENTRYPOINT ["python", "/autoBaseline.py"]