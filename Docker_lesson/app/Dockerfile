FROM python:3.11

# Create app directory
WORKDIR /app

# Install app dependencies1
COPY src/requirements.txt ./

RUN pip install -r requirements.txt

# Bundle app source
COPY src /app

EXPOSE 8000
CMD [ "python", "server.py" ]