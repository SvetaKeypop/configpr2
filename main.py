import sys

from config import Config
from errors import ConfigError
from graph_builder import (
    load_test_repo_graph,
    build_graph_test,
    build_graph_real_repo,
    compute_load_order,
    graph_to_dot,
)


def print_graph(graph: dict, root: str) -> None:
    print("Граф зависимостей:")
    printed = set()
    if root in graph:
        _print_node(graph, root, printed, indent="")
    for node in graph:
        if node not in printed:
            _print_node(graph, node, printed, indent="")


def _print_node(graph: dict, node: str, printed: set, indent: str) -> None:
    if node in printed:
        return
    printed.add(node)
    deps = graph.get(node, [])
    print(f"{indent}{node}")
    for dep in deps:
        print(f"{indent}  -> {dep}")

def print_ascii_tree(graph: dict, root: str) -> None:
    visited = set()

    def dfs(node: str, prefix: str, is_last: bool) -> None:
        connector = "└─ " if is_last else "├─ "
        print(prefix + connector + node)

        if node in visited:
            return
        visited.add(node)

        deps = graph.get(node, [])
        entries = []
        for dep in deps:
            dep_name = dep.split()[0]
            entries.append((dep_name, dep))

        for i, (dep_name, dep_raw) in enumerate(entries):
            last_child = (i == len(entries) - 1)
            child_prefix = prefix + ("   " if is_last else "│  ")

            if dep_name in visited:
                print(child_prefix + ("└─ " if last_child else "├─ ") + dep_raw)
            else:
                dfs(dep_raw, child_prefix, last_child)

    dfs(root, "", True)

def main() -> int:
    config = Config("config.yaml")

    try:
        config.load()
    except ConfigError as e:
        print(f"[ошибка конфигурации] {e}", file=sys.stderr)
        return 1

    try:
        if config.repo_mode == "test":
            test_graph = load_test_repo_graph(config.repo_url)
            graph, cycles = build_graph_test(
                test_graph,
                config.package_name,
                config.filter_substring,
            )
        else:
            graph, cycles = build_graph_real_repo(
                config.repo_url,
                config.package_name,
                config.filter_substring,
            )
    except ConfigError as e:
        print(f"[ошибка данных репозитория] {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"[неожиданная ошибка] {e}", file=sys.stderr)
        return 1

    if config.load_order:
        load_order = compute_load_order(graph, config.package_name)
        print(f"Порядок загрузки для пакета '{config.package_name}':")
        for name in load_order:
            print(f"  {name}")

        if cycles:
            print("\nВнимание: обнаружены циклические зависимости, порядок частичный:")
            for cycle in cycles:
                print("  " + " -> ".join(cycle))
        print()

    dot = graph_to_dot(graph, config.package_name)
    print("Описание графа в формате Graphviz (DOT):")
    print(dot)
    print()

    if config.ascii_tree:
        print("Зависимости в виде ASCII-дерева:")
        print_ascii_tree(graph, config.package_name)
    else:
        print("Граф зависимостей (строчный вывод):")
        print_graph(graph, config.package_name)

    return 0


if __name__ == "__main__":
    sys.exit(main())
