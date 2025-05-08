FROM python:3.13.3

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install postgresql gcc python3-dev musl-dev -y \
    && apt-get install gettext -y

RUN pip install --upgrade pip

WORKDIR /usr/src/app
COPY ./requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
