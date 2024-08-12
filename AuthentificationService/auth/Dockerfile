FROM python:3.11

WORKDIR /app

# Install app dependencies1
COPY requirements.txt ./

RUN pip install -r requirements.txt

# Bundle app source
COPY src /app

EXPOSE 8000
CMD [ "python", "app.py" ]