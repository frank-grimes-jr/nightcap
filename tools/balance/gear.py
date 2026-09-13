"""Exact maximum-score slot assignment under stated item/lore constraints."""


def assign_maximum(scores):
    """Rectangular Hungarian assignment; None means a forbidden pairing."""
    n = len(scores)
    if not n:
        return []
    m = len(scores[0])
    if m < n or any(len(row) != m for row in scores):
        raise ValueError('Assignment requires a rectangular matrix with columns >= rows')
    penalty = (max((abs(x) for row in scores for x in row if x is not None), default=0) + 1) * (2*n + 1)
    costs = [[penalty if x is None else -x for x in row] for row in scores]
    u, v, matching, previous = [0]*(n+1), [0]*(m+1), [0]*(m+1), [0]*(m+1)
    for row in range(1, n+1):
        matching[0] = row
        column = 0
        minimum, used = [float('inf')]*(m+1), [False]*(m+1)
        while True:
            used[column] = True
            active = matching[column]
            delta, following = float('inf'), 0
            for candidate in range(1, m+1):
                if not used[candidate]:
                    reduced = costs[active-1][candidate-1] - u[active] - v[candidate]
                    if reduced < minimum[candidate]:
                        minimum[candidate], previous[candidate] = reduced, column
                    if minimum[candidate] < delta:
                        delta, following = minimum[candidate], candidate
            for candidate in range(m+1):
                if used[candidate]:
                    u[matching[candidate]] += delta
                    v[candidate] -= delta
                else:
                    minimum[candidate] -= delta
            column = following
            if matching[column] == 0:
                break
        while column:
            preceding = previous[column]
            matching[column] = matching[preceding]
            column = preceding
    result = [None]*n
    for column in range(1, m+1):
        if matching[column]:
            result[matching[column]-1] = column-1
    if any(scores[i][j] is None for i, j in enumerate(result)):
        raise ValueError('No complete legal assignment exists')
    return result


def legal_item(item, slot, classes, level, race_mask=1, deity_mask=1):
    """Default fixture: Human, agnostic; native slot/class/race/deity/required-level gates."""
    if not 1 <= len(set(classes)) <= 3 or any(c < 1 or c > 16 for c in classes):
        raise ValueError('Expected one to three playable classes')
    class_mask = sum(1 << (c-1) for c in set(classes))
    return bool(item['slots'] & (1 << slot) and item['classes'] & class_mask
                and item['races'] & race_mask and item['reqlevel'] <= level
                and (item['deity'] == 0 or item['deity'] & deity_mask))


def optimize_gear(items, slots, score, classes, level, *, shield=True):
    """Globally maximize the additive score; never truncates the candidate list.

    This fixture excludes two-handed primary weapons and uses a shield by default;
    non-weapon caster items can still occupy primary. Items above
    recommended level are excluded until recommended-level stat scaling is modeled.
    The objective and eligible pool must accompany every reported result.
    """
    if len(set(slots)) != len(slots) or any(slot < 0 or slot > 21 for slot in slots):
        raise ValueError('Slots must be distinct equipment slots')
    options = {}
    for slot in slots:
        options[slot] = {}
        for item in sorted(items, key=lambda row: row['id']):
            if not legal_item(item, slot, classes, level) or item['reclevel'] > level:
                continue
            if slot == 13 and item['itemtype'] in (1, 4, 35):
                continue
            if slot == 14 and shield and item['itemtype'] != 8:
                continue
            lore = item['loregroup']
            key = f'id:{item["id"]}' if lore == -1 else (f'lore:{lore}' if lore else f'free:{slot}')
            if key not in options[slot] or score(item) > score(options[slot][key]):
                options[slot][key] = item
    groups = sorted({key for mapping in options.values() for key in mapping})
    scores = [[score(options[slot][key]) if key in options[slot] else None for key in groups] for slot in slots]
    assignment = assign_maximum(scores)
    return {slot: options[slot][groups[column]] for slot, column in zip(slots, assignment)}
