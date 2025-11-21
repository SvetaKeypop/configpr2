# graph_builder.py

from typing import Dict, List, Set, Tuple

from errors import ConfigError
from apk_dependencies import get_direct_dependencies


Graph = Dict[str, List[str]]
Cycles = List[List[str]]


def _should_skip(name: str, filter_substring: str) -> bool:
    if not filter_substring:
        return False
    return filter_substring in name


# РАБОТА С ТЕСТОВЫМ РЕПОЗИТОРИЕМ

def load_test_repo_graph(path: str) -> Graph:
    graph: Graph = {}

    try:
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except FileNotFoundError:
        raise ConfigError(f"Файл тестового репозитория '{path}' не найден")

    for lineno, line in enumerate(lines, start=1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        if ":" not in line:
            raise ConfigError(
                f"Некорректный формат в строке {lineno}: ожидается 'A: B C D'"
            )

        name_part, deps_part = line.split(":", 1)
        name = name_part.strip()

        if not name:
            raise ConfigError(f"Пустое имя пакета в строке {lineno}")

        # По условию задания имя пакета — большая латинская буква
        if not name.isalpha() or not name.isupper():
            raise ConfigError(
                f"Имя пакета '{name}' в строке {lineno} должно быть "
                f"большой латинской буквой."
            )

        deps_str = deps_part.strip()
        if not deps_str:
            deps: List[str] = []
        else:
            deps = [d.strip() for d in deps_str.split() if d.strip()]

        graph[name] = deps

    # Добавим узлы без исходящих рёбер, если они встречались только как зависимости
    for deps in list(graph.values()):
        for d in deps:
            if d not in graph:
                graph.setdefault(d, [])

    return graph


def build_graph_test(
    graph: Graph,
    root: str,
    filter_substring: str,
) -> Tuple[Graph, Cycles]:
    result: Graph = {}
    visited: Set[str] = set()
    stack: List[str] = []
    cycles: Cycles = []

    def dfs(node: str) -> None:
        if _should_skip(node, filter_substring):
            return
        if node in visited:
            return

        visited.add(node)
        stack.append(node)

        deps = [
            d for d in graph.get(node, [])
            if not _should_skip(d, filter_substring)
        ]
        result[node] = []

        for dep in deps:
            if dep in stack:
                # нашли цикл
                result[node].append(dep + " (цикл)")
                cycle_start = stack.index(dep)
                cycles.append(stack[cycle_start:] + [dep])
                continue

            result[node].append(dep)
            dfs(dep)

        stack.pop()

    dfs(root)
    return result, cycles


# РАБОТА С РЕАЛЬНЫМ APKINDEX

def build_graph_real_repo(
    repo_url: str,
    root: str,
    filter_substring: str,
) -> Tuple[Graph, Cycles]:
    result: Graph = {}
    visited: Set[str] = set()
    stack: List[str] = []
    cycles: Cycles = []

    def dfs(pkg: str) -> None:
        if _should_skip(pkg, filter_substring):
            return
        if pkg in visited:
            return

        visited.add(pkg)
        stack.append(pkg)

        try:
            direct_deps = get_direct_dependencies(repo_url, pkg)
        except ConfigError:
            # Если пакет не найден в индексе — считаем его листом
            direct_deps = []

        deps = [
            d for d in direct_deps
            if not _should_skip(d, filter_substring)
        ]
        result[pkg] = []

        for dep in deps:
            if dep in stack:
                # цикл
                result[pkg].append(dep + " (цикл)")
                cycle_start = stack.index(dep)
                cycles.append(stack[cycle_start:] + [dep])
                continue

            result[pkg].append(dep)
            dfs(dep)

        stack.pop()

    dfs(root)
    return result, cycles

def compute_load_order(graph: Graph, root: str) -> List[str]:
    # Вычисляет порядок загрузки зависимостей для заданного пакета.
    visited: Set[str] = set()
    visiting: Set[str] = set()
    order: List[str] = []

    def dfs(node: str) -> None:
        if node in visited:
            return
        if node in visiting:
            # узел в текущем стеке → цикл, не углубляемся дальше
            return

        visiting.add(node)

        for dep in graph.get(node, []):
            # dep может быть, например, "X (cycle)" — возьмём только имя до пробела
            dep_name = dep.split()[0]
            dfs(dep_name)

        visiting.remove(node)
        visited.add(node)
        order.append(node)

    dfs(root)
    return order
