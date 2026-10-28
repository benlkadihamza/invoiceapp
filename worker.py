"""Cloudflare Python Workers WSGI entrypoint (experimental)."""
from workers import wsgi
from app import app

Default = wsgi.entrypoint(app)
