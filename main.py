import sys

from config import Config
from errors import ConfigError
from graph_builder import (
    load_test_repo_graph,
    build_graph_test,
    build_graph_real_repo,
    compute_load_order,
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


def main() -> int:
    config = Config("config.yaml")

    try:
        config.load()
    except ConfigError as e:
        print(f"[ошибка конфигурации] {e}", file=sys.stderr)
        return 1

    filter_substring = config.filter_substring or ""

    try:
        if config.repo_mode == "test":
            test_graph = load_test_repo_graph(config.repo_url)
            graph, cycles = build_graph_test(
                test_graph,
                config.package_name,
                filter_substring,
            )
        else:
            graph, cycles = build_graph_real_repo(
                config.repo_url,
                config.package_name,
                filter_substring,
            )
    except ConfigError as e:
        print(f"[ошибка данных репозитория] {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"[неожиданная ошибка] {e}", file=sys.stderr)
        return 1

    # --- НОВОЕ: режим порядка загрузки ---
    if config.load_order:
        load_order = compute_load_order(graph, config.package_name)
        print(f"Порядок загрузки для пакета '{config.package_name}':")
        for name in load_order:
            print(f"  {name}")

        if cycles:
            print("\nВнимание: обнаружены циклические зависимости, порядок частичный:")
            for cycle in cycles:
                print("  " + " -> ".join(cycle))
    else:
        # Поведение этапа 3: выводим граф и циклы
        print_graph(graph, config.package_name)

        if cycles:
            print("\nОбнаружены циклические зависимости:")
            for cycle in cycles:
                print("  " + " -> ".join(cycle))
        else:
            print("\nЦиклические зависимости не обнаружены.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
