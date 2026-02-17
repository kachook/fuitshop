FROM python:3.12

WORKDIR /app

COPY requirements.txt /app
RUN pip install -r requirements.txt

COPY fruitshop /app/fruitshop

ENV FLASK_APP=/app/fruitshop

CMD ["flask", "run", "--host=0.0.0.0"]