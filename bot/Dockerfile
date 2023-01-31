# FROM python:3.11-alpine
FROM python:3.11
# set work directory
WORKDIR /usr/src/bot/
# copy project
COPY . /usr/src/bot/
# install dependencies
RUN pip install -r requirements.txt

RUN pip-upgrade

# RUN apt update

## Creates a non-root user with an explicit UID and adds permission to access the /app folder
## For more info, please refer to https://aka.ms/vscode-docker-python-configure-containers
#RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /app
#USER appuser

# RUN apt install -y netcat
# COPY entrypoint.sh /usr/bin/
# RUN chmod +x /usr/bin/entrypoint.sh
# ENTRYPOINT ["entrypoint.sh"]

# run app
CMD ["python", "autoreload.py", "python", "main.py"]
