from functools import wraps
from flask import redirect, url_for, session

def required_roles(*roles):
    """
    Decorador para verificar se o usuário tem a role necessária.
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            # Verificar se o usuário está logado
            if 'user' not in session:
                return redirect(url_for('login'))
                
            # Verificar se o usuário tem a role necessária
            user_role = session['user'].get('role', 'visitante')
            if user_role not in roles:
                return "Acesso não autorizado", 403
                
            return f(*args, **kwargs)
        return wrapper
    return decorator