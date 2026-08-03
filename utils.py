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
