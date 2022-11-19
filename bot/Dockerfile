# FROM python:3.11-alpine
FROM python:3.11
# set work directory
WORKDIR /usr/src/bot/
# copy project
COPY . /usr/src/bot/
# install dependencies
RUN pip install -r requirements.txt

## Creates a non-root user with an explicit UID and adds permission to access the /app folder
## For more info, please refer to https://aka.ms/vscode-docker-python-configure-containers
#RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /app
#USER appuser

# run app
CMD ["python", "main.py"]
