# Blackjack Telegram Bot

A Telegram bot for playing blackjack in group chats with other users.

## **Technologies Used:**
- **Python 3.x** - Primary development language
- **aiogram** - Asynchronous library for Telegram Bot API
- **PostgreSQL** - Database for storing player data
- **Redis** - In-memory database for storing active games (Redis Cloud free tier was used)

## **Installation & Setup**

### Prerequisites
- Docker and Docker Compose installed
- Telegram bot token (obtain from [@BotFather](https://t.me/BotFather))
- Redis instance (local or cloud)

### Docker Setup
1. Clone the repository
```bash
git clone https://github.com/tighwm/blckjck_bot.git
cd blckjck_bot
```

2. Create a `.env` file in the `src` directory with the following content:
```env
APP_CONFIG__DB__URL=your_db_url
APP_CONFIG__BOT__TOKEN=your_bot_token
APP_CONFIG__REDIS__URL=your_redis_url
```

**Note:** If you haven't modified the `docker-compose.yml` file, the default database URL is:
```
postgresql+asyncpg://postgres:123@localhost/blackjack
```

3. Start the application
```bash
docker compose up -d
```

## **Features**
- Multi-player blackjack games in Telegram group chats
- Persistent player data storage
- Real-time game state management
- Easy deployment with Docker

## **Usage**
1. Add the bot to your Telegram group chat
2. Start a new game and invite other players
3. Follow the bot's instructions to play blackjack

## **Contributing**
Feel free to submit issues and pull requests to improve the bot.
