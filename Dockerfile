FROM python:3.10.14-slim

COPY modules /modules

COPY autoBaseline.py /autoBaseline.py

COPY requirements.txt /requirements.txt

RUN pip install -r requirements.txt

ENTRYPOINT ["python", "/autoBaseline.py"]