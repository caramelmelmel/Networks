FROM python:3.8-slim-buster

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
RUN pip install aiofiles

EXPOSE 80

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]