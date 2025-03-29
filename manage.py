import os
import sys
import threading
import asyncio
from pathlib import Path
import psutil

PID_FILE = "bot.pid"


def run_bot():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bachelor.settings')

    if Path(PID_FILE).exists():
        with open(PID_FILE, "r") as f:
            try:
                pid = int(f.read().strip())
                if psutil.pid_exists(pid):
                    print("Бот уже запущений. Завершіть інший процес перед стартом.")
                    return
            except ValueError:
                pass

    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))

    try:
        from bot.telegram_bot import main as bot_main
        asyncio.run(bot_main())
    finally:
        if Path(PID_FILE).exists():
            os.remove(PID_FILE)


def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bachelor.settings')

    if os.environ.get('RUN_MAIN') == 'true' and len(sys.argv) > 1 and sys.argv[1] == 'runserver':
        bot_thread = threading.Thread(target=run_bot, daemon=True)
        bot_thread.start()

    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()