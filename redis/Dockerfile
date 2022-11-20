FROM redis:7.0-alpine as base
CMD redis-server --save 20 1 --maxmemory 100mb --loglevel warning --requirepass $REDIS_PASSWORD
