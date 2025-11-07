FROM python:3.11

WORKDIR /app

COPY ../requirements.txt /app/requirements.txt
RUN apt-get update && apt-get install -y libportaudio2
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app

CMD ["python", "sensor_noise.py"]
