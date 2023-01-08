def apply(items, func):
    return list(map(func, items))


def get_map(items: list, key: str, is_dict: bool = True):
    if is_dict:
        return {
            item.get(key): item
            for item in items
        }

    else:
        return {
            getattr(item, key): item
            for item in items
        }
