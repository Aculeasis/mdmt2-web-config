# Web config plugin for mdmTerminal2
Позволяет настраивать терминал и смотреть логи в браузере.

# Установка
```
mdmTerminal2/env/bin/python -m pip install bottle
cd mdmTerminal2/src/plugins
git clone https://github.com/Aculeasis/mdmt2-web-config
```
И перезапустить терминал.

## Настройка
Настройки хранятся в `mdmTerminal2/src/data/web_config_config.json`, файл будет создан при первом запуске:
- **ip**: Интерфейс который будет слушать сервер. По умолчанию `"0.0.0.0"`.
- **port**: Порт сервера. По умолчанию `8989`.
- **quiet**: Не логгировать запросы в консоль. По умолчанию `true`.
- **username**, **password**: Если оба значение заданы, будет включена базовая аутентификация. По умолчанию `"root"`, `"root"`.

# Особенности
- Плагин автоматически получает и обновляет описание настроек из wiki, они хранятся в `mdmTerminal2/src/data/web_config_wiki.json`.

# Ссылки
- [mdmTerminal2](https://github.com/Aculeasis/mdmTerminal2)
- [Google Assistant SDK for devices - Python](https://github.com/googlesamples/assistant-sdk-python)
