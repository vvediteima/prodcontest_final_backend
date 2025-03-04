FROM python:3.11-slim

ENV POSTGRES_DB=prod_db
ENV POSTGRES_USER=prod
ENV POSTGRES_PASSWORD=prod_password
ENV POSTGRES_LINK=postgresql+psycopg2://prod:prod_password@database:5432/prod_db

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir poetry


COPY . /app


RUN pip install -r requirements.txt

EXPOSE 8080
CMD ["waitress-serve", "--port", "8080", "--host=0.0.0.0", "src.main:application"]
