"""Local gateway access and redaction; never emits credentials."""
import json
import os
import re
import subprocess
import urllib.request
from urllib.parse import urlparse
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def api_key():
    for name in ('LITELLM_API_KEY', 'LITELLM_MASTER_KEY', 'OPENAI_API_KEY'):
        if os.environ.get(name):
            return os.environ[name]
    try:
        import yaml
        config = yaml.safe_load(Path('/opt/litellm/config.yaml').read_text())
        key = config.get('general_settings', {}).get('master_key', '')
        if not isinstance(key, str):
            raise ValueError()
        if key.startswith('os.environ/'):
            key = os.environ.get(key.split('/', 1)[1], '')
        if key:
            return key
    except Exception:
        pass
    raise RuntimeError('Gateway credential unavailable; set LITELLM_API_KEY or provide readable config with general_settings.master_key.')

def redact(value):
    text = str(value)
    try:
        key = api_key()
        text = text.replace(key, '[REDACTED]')
    except RuntimeError:
        pass
    text = re.sub(r'(?i)(Bearer\s+)\S+', r'\1[REDACTED]', text)
    text = re.sub(r'sk-[A-Za-z0-9_-]+', '[REDACTED]', text)
    text = re.sub(r'''(?i)(["']?[\w-]*(?:api[_-]?key|token|password|secret|master_key)[\w-]*["']?\s*[:=]\s*)("[^"]*"|'[^']*'|[^\s,;}]+)''', r'\1[REDACTED]', text)
    return text

def gateway(path, payload=None, timeout=180):
    base = os.environ.get('LITELLM_BASE_URL', 'http://127.0.0.1:4000/v1').rstrip('/')
    parsed = urlparse(base)
    if parsed.scheme != 'http' or parsed.hostname not in ('localhost', '127.0.0.1', '::1') or parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise RuntimeError('LITELLM_BASE_URL must be a local HTTP endpoint without credentials/query/fragment.')
    request = urllib.request.Request(base + path, data=None if payload is None else json.dumps(payload).encode(), headers={'Authorization': 'Bearer ' + api_key(), 'Content-Type': 'application/json'})
    # Local calls must never use environment HTTP proxies or follow redirects with credentials.
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *args, **kwargs):
            return None
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    with opener.open(request, timeout=timeout) as response:
        return json.load(response)

def command(args, timeout=20):
    try:
        p = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
        return p.returncode, redact(p.stdout + p.stderr)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return 1, redact(exc)
