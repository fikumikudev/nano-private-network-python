FROM python:3.7

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY nano_prvnet/ nano_prvnet/

ENTRYPOINT [ "python", "-m" ]