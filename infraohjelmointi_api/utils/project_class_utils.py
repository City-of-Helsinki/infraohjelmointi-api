def get_programmer_from_hierarchy(project_class, max_depth=10):
    if not project_class:
        return None
    visited = set()
    current = project_class
    depth = 0
    while current:
        if current.id in visited:
            raise ValueError(f"Cycle detected in ProjectClass hierarchy at class '{current.name}' (ID: {current.id})")
        visited.add(current.id)
        depth += 1
        if depth > max_depth:
            raise ValueError(f"Maximum hierarchy depth ({max_depth}) exceeded")
        if current.defaultProgrammer:
            return current.defaultProgrammer
        current = current.parent
    return None
