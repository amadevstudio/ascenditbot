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

### Pycharm
- Set bot folder: RClick on bot -> Mark directory as -> Mark as Sources Root
- For Community version you can use local packages environment for packages mapping:
  - `cd bot && python -m venv venv`
  - In Pycharm set Python Interpreter as existing Virtual Environment using venv
  - `source venv/bin/activate`
  - `python -m pip install virtualenv`
  - `deactivate`

### Fast developing (deprecated because auto-reload added)
Run compose and stop the bot container  
`docker compose up`  
Then in new terminal run  
`docker compose stop -t 1 bot && docker compose run --rm -p 3000:3000 bot`  
works like a ⚡️

### After generate files using Docker
Because Docker runs as root, you must take ownership of the project files after generating them from containers.  
For example, when creating a new migration with migrator.  
To do so, use  
`./scripts/own_project.sh`

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
