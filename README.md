# ascenditbot
Telegram whitelist bot for a chats

## Setup

- `touch env/.env.local` and set variables:
  - *TELEGRAM_BOT_TOKEN*
  - *TELEGRAM_ADMIN_GROUP_ID*
- `docker compose build`
- `docker compose up`
- `docker compose run migrator -e POSTGRES_URL up`
- `sudo chmod u+x scripts/own_project.sh && ./scripts/own_project.sh`

Additional steps for production:
- Create administrator user and perform all steps from him
- Set additional variables:
  - *ENVIRONMENT=production*
  - *POSTGRES_PASSWORD*
  - *POSTGRES_URL="postgres://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_SERVER}:${POSTGRES_PORT}/${POSTGRES_DB}?sslmode=disable"*
  - *REDIS_PASSWORD*
- Use docker compose command with prod file: `docker compose -f docker-compose.yml -f docker-compose.prod.yml build`
- And run in background `docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d`

### Pycharm
- Set bot folder: RClick on bot -> Mark directory as -> Mark as Sources Root
- For Community version you can use local packages environment for packages mapping:
  - `cd bot && python -m venv venv`
  - In Pycharm set Python Interpreter as existing Virtual Environment using venv
  - `source venv/bin/activate`
  - `python -m pip install virtualenv`
  - `deactivate`

### ~~Fast developing~~
<details>
  <summary>Deprecated due to the addition of auto-reload</summary>
  Run compose and stop the bot container<br>
  <code>docker compose up</code><br>
  Then in new terminal run<br>
  <code>docker compose stop -t 1 bot && docker compose run --rm -p 3000:3000 bot</code><br>  
  Works like a ⚡️
</details>

### After generate files using Docker
<details>
  <summary>Required depending on environment</summary>
  Because Docker may run as root, you may need to take ownership of the project files after they are created from containers.<br>
  For example, when creating a new migration with migrator.<br>
  To do so, use  
  <code>./scripts/own_project.sh</code>
</details>

## Migrations
Using [dbmate](https://github.com/amacneil/dbmate)
as migration engine.

Create new migration with  
`docker compose run migrator -e POSTGRES_URL new create_users_table`  
Migrate with  
`docker compose run migrator -e POSTGRES_URL migrate`  
View help and rest of the commands with  
`docker compose run migrator --help`

Don't forget to own the project if necessary.
