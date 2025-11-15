import gzip
import tarfile
import io
import urllib.request
from typing import List

from errors import ConfigError


def _download_apkindex(repo_url: str) -> str:
    # Скачивает индекс репозитория APKINDEX (или APKINDEX.tar.gz) и возвращает его содержимое как строку

    base = repo_url.rstrip("/")

    candidates = []

    lower = base.lower()
    # eсли в конфиге уже явно указан APKINDEX или APKINDEX.tar.gz
    if lower.endswith("apkindex") or lower.endswith("apkindex.tar.gz"):
        candidates.append(base)
    else:
        # иначе пробуем стандартные варианты Alpine
        candidates.append(base + "/APKINDEX.tar.gz")
        candidates.append(base + "/APKINDEX")

    errors = []

    for url in candidates:
        try:
            with urllib.request.urlopen(url) as resp:
                data = resp.read()
            text = _decode_apkindex(data, url)
            return text
        except Exception as e:
            errors.append(f"{url} → {e}")

    raise ConfigError(
        "Не удалось загрузить индекс репозитория APKINDEX.\n" + "\n".join(errors)
    )


def _decode_apkindex(data: bytes, url: str) -> str:
    """
    Распаковывает данные APKINDEX:
    APKINDEX.tar.gz - извлекает файл APKINDEX из tar.gz
    APKINDEX.gz - распаковывает gzip
    APKINDEX - декодирует как текст
    """
    url_lower = url.lower()

    # случай APKINDEX.tar.gz (tar-архив внутри gzip)
    if url_lower.endswith(".tar.gz"):
        try:
            # снимаем gzip
            try:
                decompressed = gzip.decompress(data)
            except OSError:
                # если это чистый tar без gzip
                decompressed = data

            # открываем tar из байтового буфера
            with tarfile.open(fileobj=io.BytesIO(decompressed)) as tar:
                try:
                    member = tar.getmember("APKINDEX")
                except KeyError:
                    raise ConfigError("В архиве APKINDEX.tar.gz не найден файл 'APKINDEX'")

                f = tar.extractfile(member)
                if f is None:
                    raise ConfigError("Не удалось извлечь файл 'APKINDEX' из архива")

                inner_data = f.read()
            return inner_data.decode("utf-8", errors="replace")
        except ConfigError:
            raise
        except Exception as e:
            raise ConfigError(f"Ошибка распаковки APKINDEX.tar.gz: {e}")

    # случай APKINDEX.gz (просто gzip, без tar)
    if url_lower.endswith(".gz"):
        try:
            data = gzip.decompress(data)
        except OSError:
            # если не gzip — пробуем как есть
            pass

    # текстовый APKINDEX
    try:
        return data.decode("utf-8", errors="replace")
    except Exception as e:
        raise ConfigError(f"Не удалось декодировать APKINDEX как текст: {e}")


def _parse_apkindex(apkindex_text: str, package_name: str) -> List[str]:
    """
    Находит в тексте APKINDEX блок P:package_name
    и возвращает список прямых зависимостей (строка D:).
    """
    if not isinstance(apkindex_text, str):
        # на всякий случай жёстко проверяем тип, чтобы не было 'list.strip'
        raise ConfigError(
            f"Внутренняя ошибка: apkindex_text имеет тип {type(apkindex_text)}, ожидалась str"
        )

    blocks = apkindex_text.split("\n\n")

    for block in blocks:
        block = block.strip()
        if not block:
            continue

        pkg = None
        deps_line = None

        for line in block.splitlines():
            if line.startswith("P:"):
                pkg = line[2:].strip()
            elif line.startswith("D:"):
                deps_line = line[2:].strip()

        if pkg == package_name:
            if not deps_line:
                return []
            deps = [d for d in deps_line.split() if d]
            return deps

    raise ConfigError(f"Пакет '{package_name}' не найден в индексе репозитория.")


def get_direct_dependencies(repo_url: str, package_name: str) -> List[str]:
    # скачивает индекс и возвращает прямые зависимости пакета
    apkindex_text = _download_apkindex(repo_url)
    return _parse_apkindex(apkindex_text, package_name)
