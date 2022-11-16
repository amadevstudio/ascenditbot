# FROM python:3.11-alpine
FROM python:3.11
# set work directory
WORKDIR /usr/src/bot/
# copy project
COPY . /usr/src/bot/
# install dependencies
RUN pip install -r requirements.txt
# run app
CMD ["python", "main.py"]