import sys

from apk_dependencies import get_direct_dependencies
from config import Config
from errors import ConfigError

def main() -> int:
    config = Config("config.yaml")

    try:
        config.load()
    except ConfigError as e:
        print(f"[ошибка конфигурации] {e}", file=sys.stderr)
        return 1

    try:
        deps = get_direct_dependencies(config.repo_url, config.package_name)
    except ConfigError as e:
        print(f"[ошибка данных репозитория] {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"[неожиданная ошибка] {e}", file=sys.stderr)
        return 1

    print(f"Прямые зависимости пакета '{config.package_name}':")
    if not deps:
        print("(нет прямых зависимостей)")
    else:
        for dep in deps:
            print(dep)

    return 0

if __name__ == "__main__":
    sys.exit(main())