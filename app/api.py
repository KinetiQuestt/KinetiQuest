from functools import wraps

def login_required(role):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                print("checking if logged in")
            except Exception as e:
                return {"message": f"Verification failed: {str(e)}"}, 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator