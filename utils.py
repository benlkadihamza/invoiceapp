import re
from urllib.parse import quote


def format_price(val, force_decimals=None):
    if val is None:
        val = 0.0
    try:
        val = float(val)
    except (ValueError, TypeError):
        val = 0.0

    if force_decimals is not None:
        show_decimals = force_decimals
    else:
        from flask_login import current_user
        from flask import session
        try:
            if current_user and current_user.is_authenticated:
                show_decimals = getattr(current_user, 'show_decimals', False)
            else:
                show_decimals = session.get('show_decimals', False)
        except Exception:
            show_decimals = False

    if show_decimals:
        return f"{val:,.2f}".replace(',', ' ')
    else:
        if val.is_integer():
            return f"{int(val):,}".replace(',', ' ')
        else:
            return f"{val:,.2f}".replace(',', ' ')


def waze_url(address):
    if not address:
        return "#"
    addr_str = str(address).strip()
    if not addr_str:
        return "#"
    # Check if address contains GPS coordinates (e.g. "35.244560, -3.931240" or "Address (35.244560, -3.931240)")
    coord_match = re.search(r'(-?\d{1,2}\.\d+)\s*,\s*(-?\d{1,3}\.\d+)', addr_str)
    if coord_match:
        lat, lon = coord_match.group(1), coord_match.group(2)
        return f"https://waze.com/ul?ll={lat},{lon}&navigate=yes"
    return f"https://waze.com/ul?q={quote(addr_str)}&navigate=yes"

