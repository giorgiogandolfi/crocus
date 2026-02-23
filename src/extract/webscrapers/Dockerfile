FROM python:3.13.2-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /ishares

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "ishares.py"]