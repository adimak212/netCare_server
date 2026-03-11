from src.algorithm.version2.services.topology_cache import TopologyCache


def main():
    cache = TopologyCache()
    cache.set("fat_tree", 12, {"result": 1})

    print(cache.get("fat_tree", 12))

    print("cache size:", cache.size())


if __name__ == "__main__":
    main()