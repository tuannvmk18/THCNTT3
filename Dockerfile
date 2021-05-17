FROM python:3.7

COPY ./app /app
WORKDIR /app/app

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", {{PORT}}]