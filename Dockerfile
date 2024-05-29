FROM python:3.10.14-slim

RUN pip install -r requirements.txt

COPY modules /modules

COPY autoBaseline.py /autoBaseline.py

COPY requirements.txt /requirements.txt

ENTRYPOINT ["python", "/autoBaseline.py"]