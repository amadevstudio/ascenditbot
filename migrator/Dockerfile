FROM amacneil/dbmate as base
WORKDIR /usr/src/migrator/
COPY . /usr/src/migrator/
CMD ["-e", "POSTGRES_URL", "status"]

FROM base as prod
CMD ["-e", "POSTGRES_URL", "up"]
