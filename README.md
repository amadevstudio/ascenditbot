# ascenditbot
Telegram whitelist bot for a group

## Setup

- `touch env/.env.local` and set variables:
  - *TELEGRAM_BOT_TOKEN*
- `docker-compose build`
- `docker-compose up`
- `docker-compose run migrator up`
- `sudo chmod u+x scripts/own_project.sh && ./scripts/own_project.sh`

### Fast developing
Run compose and stop the bot container  
`docker-compose up`  
Then in new terminal run  
`docker-compose stop bot && docker-compose run bot`  
works like a ⚡️

### After generate files using Docker
Because Docker runs as root, you must take ownership of the project files after generating them from containers.  
For example, when creating a new migration with migrator.  
To do so, use  
`./scripts/own_project.sh`

## Migrations
Using [dbmate](https://github.com/amacneil/dbmate)
as migration engine.

__TODO: Production migrations runs automatically.__

Create new migration with  
`docker-compose run migrator -e POSTGRES_URL new create_users_table`  
Migrate with  
`docker-compose run migrator -e POSTGRES_URL migrate`  
View help and rest of the commands with  
`docker-compose run migrator --help`

Don't forget to own the project.
