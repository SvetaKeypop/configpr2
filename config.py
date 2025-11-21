from typing import Optional
import yaml

from errors import ConfigError


class Config:
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path

        # параметры
        self.package_name: str = ""
        self.repo_url: str = ""
        self.repo_mode: str = ""
        self.ascii_tree: bool = False
        self.filter_substring: str = ""
        self.load_order: bool = False

    def load(self) -> None:
        # загрузка конфигурации и валидация
        try:
            with open(self.config_path, "r") as f:
                data = yaml.safe_load(f)
        except FileNotFoundError:
            raise ConfigError(f"Config file {self.config_path} not found")

        except yaml.YAMLError:
            raise ConfigError("некорректный YAML")

        if not isinstance(data, dict):
            raise ConfigError("Корень YAML файла должен быть объектом ключ-значение")

        # проверка наличия обязательных полей
        required_keys = ["package_name", "repo_url", "repo_mode", "ascii_tree", "filter_substring"]
        for key in required_keys:
            if key not in data:
                raise ConfigError(f"Отсутствует обязательный параметр '{key}'")

        # проверка типов
        package_name = data["package_name"]
        if not isinstance(package_name, str) or not package_name.strip():
            raise ConfigError("'package_name' должен быть непустой строкой")

        repo_url = data["repo_url"]
        if not isinstance(repo_url, str) or not repo_url.strip():
            raise ConfigError("'repo_url' должен быть непустой строкой")

        repo_mode = data["repo_mode"]
        if not isinstance(repo_mode, str) or not repo_mode.strip():
            raise ConfigError("'repo_mode' должен быть непустой строкой (режим работы)")

        ascii_tree = data["ascii_tree"]
        if not isinstance(ascii_tree, bool):
            raise ConfigError("'ascii_tree' должен быть булевым значением (true/false)")

        filter_substring = data["filter_substring"]
        if not isinstance(filter_substring, str):
            raise ConfigError("'filter_substring' должен быть строкой")

        load_order = data.get("load_order", False)
        if not isinstance(load_order, bool):
            raise ConfigError("'load_order' должен быть булевым значением (true/false)")

        #сохранение в поля объекта
        self.package_name = package_name.strip()
        self.repo_url = repo_url.strip()
        self.repo_mode = repo_mode.strip()
        self.ascii_tree = ascii_tree
        self.filter_substring = filter_substring
        self.load_order = load_order