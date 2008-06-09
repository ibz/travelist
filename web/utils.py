
def group_items(items, func):
    groups = []
    for item in items:
        group_found = False
        for group in groups:
            if func(group[0], item):
                group.append(item)
                group_found = True
                break
        if not group_found:
            groups.append([item])
    return groups

def find(l, func):
    for item in l:
        if func(item):
            return item
