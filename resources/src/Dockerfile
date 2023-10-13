FROM python:3.8-slim

WORKDIR /rb-aioutliers

COPY . /rb-aioutliers

RUN pip install --no-cache-dir -r requirements.txt

ENV ENVIRONMENT=production

CMD ["python", "__main__.py"]
