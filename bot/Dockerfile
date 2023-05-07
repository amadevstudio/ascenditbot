# FROM python:3.11-alpine
FROM python:3.11 as base
# set work directory
WORKDIR /usr/src/bot/
# copy project
COPY . /usr/src/bot/

RUN pip install -r requirements.txt # Install packages from requirements.txt

RUN pip-upgrade --skip-virtualenv-check # Interactively upgrade packages from requirements file, and also update the pinned version from requirements file(s).

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
FROM base as dev
CMD ["python", "autoreload.py", "python", "main.py"]

FROM base as prod
CMD ["python", "main.py"]
