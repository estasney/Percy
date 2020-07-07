from datetime import datetime
from dateutil.relativedelta import relativedelta


def last_seen_time(dt: datetime, from_time=None):
    if not from_time:
        from_time = datetime.utcnow()
    d = relativedelta(from_time, dt).normalized()
    components = []
    attributes = ['years', 'months', 'days', 'hours', 'minutes', 'seconds']
    attr_idx_start = 0
    attr_idx_end = 0
    for attr in attributes:
        attr_value = getattr(d, attr)
        if attr_value <= 0:
            attr_idx_start += 1
        else:
            attr_idx_end = attr_idx_start + 3
            break

    attributes_trimmed = attributes[attr_idx_start:attr_idx_end]
    if not attributes_trimmed:
        return "Just Now"

    for attr in attributes_trimmed:
        attr_value = getattr(d, attr)
        attr_name = attr.title() if attr_value > 1 else attr.title()[:-1]
        components.append(f"{attr_value} {attr_name}")

    return ", ".join(components)
