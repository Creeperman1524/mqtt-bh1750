FROM python:3.9-alpine

WORKDIR /app

RUN apk add --no-cache i2c-tools

RUN pip install --no-cache-dir paho-mqtt smbus2

ADD bh1750.py .

CMD ["python", "-u", "bh1750.py"]
