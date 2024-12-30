FROM python:3.9-slim

WORKDIR /botname

COPY requirements.txt /botname/
RUN pip install -r /botname/requirements.txt
COPY .env /botname/

# Add this to force Docker to use the latest code
ARG CACHEBUST=1
COPY . /botname/

CMD python3 /botname/app.py