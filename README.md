# mlds-chatstat-bot

## Навигация

- [Описание проекта](#description)
- [Установка](#installation)
- [Запуск](#launch)

<a name='description'></a>

## Описание проекта

Данный содержит исходный код телеграм чат-бота, используемого для выгрузки статистики сообщений, отправленных в чатах учебных курсов программы МОВС 2023-2025.

Для простоты использования сообщения не подгружаются из чатов динамически, а хранятся в папке ```/data``` в csv формате.

**NOTE**: Код бота мог бы быть оформлен модульно, но имеем что имеем :)

---

<a name='installation'></a>

## Установка

- `git clone https://github.com/Melon-peel/mlds-chatstat-bot.git`
- `python -m venv path/to/your/venv`
- `source path/to/your/venv/bin/activate`
- `cd mlds-chatstat-bot`
- `poetry install`
- Необходимо создать файл ```chatbot/bot_config.json``` в следующем формате: ```{"token": "your_token_here"}```. ```your_token_here``` можно получить, зарегистрировав бота у [BotFather](https://telegram.me/BotFather)

---

<a name='launch'></a>

## Запуск

- `cd chatbot && python app.py`
  
