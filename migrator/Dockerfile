FROM amacneil/dbmate as base
WORKDIR /usr/src/migrator/
COPY . /usr/src/migrator/

# RUN apk update

# RUN apk add bash netcat-openbsd
# COPY entrypoint.sh /usr/src/migrator/
# RUN chmod +x /usr/src/migrator/entrypoint.sh
# ENTRYPOINT ["/bin/bash", "/usr/src/migrator/entrypoint.sh"]

# CMD ["dbmate", "-e", "POSTGRES_URL", "status"]
CMD ["-e", "POSTGRES_URL", "status"]

FROM base as prod
CMD ["-e", "POSTGRES_URL", "up"]
