import time
import uuid
import hashlib
import threading
from functools import wraps
from flask import request, redirect, jsonify, flash, url_for
from flask_login import current_user

class IdempotencyManager:
    def __init__(self, ttl=300):
        self.ttl = ttl
        self._tokens = {}
        self._fingerprints = {}
        self._lock = threading.Lock()

    def _cleanup_nolock(self):
        now = time.time()
        expired_tokens = [k for k, v in self._tokens.items() if now - v['timestamp'] > self.ttl]
        for k in expired_tokens:
            del self._tokens[k]
        
        expired_fp = [k for k, v in self._fingerprints.items() if now - v['timestamp'] > self.ttl]
        for k in expired_fp:
            del self._fingerprints[k]

    def check_and_start(self, token_str=None, payload_fingerprint=None):
        with self._lock:
            self._cleanup_nolock()
            now = time.time()

            # 1. Check token_str if provided
            if token_str and token_str in self._tokens:
                entry = self._tokens[token_str]
                return entry['status'], entry.get('result')

            # 2. Check payload fingerprint if provided
            if payload_fingerprint and payload_fingerprint in self._fingerprints:
                entry = self._fingerprints[payload_fingerprint]
                # If fingerprint seen within last 10 seconds, treat as duplicate
                if now - entry['timestamp'] < 10:
                    return entry['status'], entry.get('result')

            # 3. Register as PENDING
            if token_str:
                self._tokens[token_str] = {'status': 'PENDING', 'result': None, 'timestamp': now}
            if payload_fingerprint:
                self._fingerprints[payload_fingerprint] = {'status': 'PENDING', 'result': None, 'timestamp': now}

            return 'NEW', None

    def complete(self, token_str=None, payload_fingerprint=None, result=None):
        with self._lock:
            now = time.time()
            if token_str:
                self._tokens[token_str] = {'status': 'DONE', 'result': result, 'timestamp': now}
            if payload_fingerprint:
                self._fingerprints[payload_fingerprint] = {'status': 'DONE', 'result': result, 'timestamp': now}

    def clear(self, token_str=None, payload_fingerprint=None):
        with self._lock:
            if token_str and token_str in self._tokens:
                del self._tokens[token_str]
            if payload_fingerprint and payload_fingerprint in self._fingerprints:
                del self._fingerprints[payload_fingerprint]


idempotency_store = IdempotencyManager()


def generate_request_token():
    return uuid.uuid4().hex


def compute_request_fingerprint():
    try:
        user_id = str(current_user.id) if current_user and current_user.is_authenticated else 'anonymous'
        path = request.path
        body = request.get_data() or b''
        h = hashlib.sha256(f"{user_id}:{path}:".encode('utf-8') + body).hexdigest()
        return h
    except Exception:
        return None


def get_submitted_token():
    if request.is_json:
        data = request.get_json(silent=True) or {}
        if isinstance(data, dict) and data.get('request_token'):
            return data.get('request_token')
    
    if request.form and request.form.get('request_token'):
        return request.form.get('request_token')

    header_token = request.headers.get('X-Request-Token')
    if header_token:
        return header_token

    return None


def idempotent_route(redirect_endpoint=None):
    """
    Decorator to prevent duplicate form or AJAX submissions on CREATE/POST endpoints.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if request.method != 'POST':
                return f(*args, **kwargs)

            token = get_submitted_token()
            fingerprint = compute_request_fingerprint()

            status, cached_result = idempotency_store.check_and_start(token, fingerprint)
            is_ajax = request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest'

            if status in ('PENDING', 'DONE'):
                # Duplicate submission detected!
                if cached_result is not None:
                    return cached_result
                
                if is_ajax:
                    return jsonify({
                        'success': True,
                        'duplicate': True,
                        'message': 'Requête déjà traitée ou en cours.'
                    }), 200
                else:
                    flash('Requête déjà enregistrée.', 'info')
                    if redirect_endpoint:
                        return redirect(url_for(redirect_endpoint))
                    return redirect(request.referrer or url_for('dashboard.index'))

            try:
                response = f(*args, **kwargs)
                # Store completed response
                idempotency_store.complete(token, fingerprint, response)
                return response
            except Exception as e:
                idempotency_store.clear(token, fingerprint)
                raise e

        return decorated_function
    return decorator
