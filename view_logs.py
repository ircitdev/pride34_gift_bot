"""View bot logs - show last N lines or follow in real-time."""
import sys
from pathlib import Path

def view_logs(lines=50, follow=False):
    """View bot logs."""
    log_file = Path("logs/bot.log")

    if not log_file.exists():
        print("❌ Лог-файл не найден. Бот еще не запускался.")
        return

    print("=" * 80)
    print(f"📋 ЛОГИ БОТА (последние {lines} строк)")
    print("=" * 80)
    print()

    with open(log_file, 'r', encoding='utf-8') as f:
        all_lines = f.readlines()

        # Show last N lines
        for line in all_lines[-lines:]:
            print(line.rstrip())

    print()
    print("=" * 80)
    print(f"Всего строк в логе: {len(all_lines)}")
    print("=" * 80)


if __name__ == "__main__":
    # Get number of lines from command line argument
    lines = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    view_logs(lines)
