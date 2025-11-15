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

    print(f"package_name={config.package_name}")
    print(f"repo_url={config.repo_url}")
    print(f"repo_mode={config.repo_mode}")
    print(f"ascii_tree={config.ascii_tree}")
    print(f"filter_substring={config.filter_substring}")

    return 0

if __name__ == "__main__":
    sys.exit(main())