# ascenditbot
Telegram whitelist bot for a group

## Setup

- `cp .env .env.local` and set veriables
- `docker-compose build`
- `docker-compose up`

### Fast developing
Run compose and stop the bot container  
`docker-compose up && docker-compose stop bot`  
Then in new terminal run  
`docker-compose run bot` works like a ⚡️