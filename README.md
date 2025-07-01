# Blackjack Telegram Bot
Телеграм-бот для гри в блекджек у чатах разом з іншими користувачами.

### **Технології:**
- Python 3.x - основна мова розробки
- aiogram - асинхрона бібліотека для роботи з Telegram Bot API
- PostgreSQL - БД для зберігання даних ігроків
- Redis - СУБД для зберігання плинущих ігор (використовувалась Redis Cloud безкоштовного плану)

## **Встановлення і запуск**
### Docker

1. Потрібно клонувати репозиторій
```bash
git clone https://github.com/tighwm/blckjck_bot.git
cd blckjck_bot
```

2. Створити `.env` файл у `src` директорії з таким наповненням
```.env
APP_CONFIG__DB__URL=your_db_url (якщо не змінювався docker-compose.yml то зазвичай postgresql+asyncpg://postgres:123@localhost/blackjack)
APP_CONFIG__BOT__TOKEN=your_bot_token
APP_CONFIG__REDIS__URL=your_redis_url 
```

3. Запустити
```bash
docker compose up -d
```

