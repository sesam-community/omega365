FROM python:3.12-slim

LABEL org.opencontainers.image.authors="Tarjei N Skrede, tarjei.skrede@sesam.io"
LABEL org.opencontainers.image.source="https://github.com/sesam-community/omega365"
LABEL updated_by="Geir Atle Hegsvold, geir.hegsvold@bouvet.no"

COPY ./service /service

RUN pip install --upgrade pip
RUN pip install -r /service/requirements.txt

EXPOSE 5000/tcp

CMD ["python3", "-u", "./service/omega365.py"]
