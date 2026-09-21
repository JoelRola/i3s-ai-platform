#!/usr/bin/env python3
import datetime
import re
import sys
from ops_common import command, gateway, redact

def main():
    watch = '--watch' in sys.argv
    failed = False
    print(datetime.datetime.now(datetime.timezone.utc).isoformat(), flush=True)
    checks = [('GPU', ['nvidia-smi']), ('Loaded Ollama models', ['ollama', 'ps']), ('RAM', ['free', '-h']), ('Disk', ['df', '-h', '/', '/mnt/ai-data']), ('Docker containers', ['docker', 'inspect', '--format', '{{.Name}} status={{.State.Status}} {{if .State.Health}}health={{.State.Health.Status}}{{end}}', 'open-webui', 'litellm'])]
    if not watch:
        checks += [('Installed Ollama models', ['ollama', 'list']), ('Ollama service', ['systemctl', 'is-active', 'ollama'])]
    for title, args in checks:
        code, output = command(args)
        failed |= bool(code) or ('status=' in output and output.count('status=running') != 2) or 'health=unhealthy' in output
        print('\n' + title + (f' [CHECK FAILED: {code}]' if code else '') + '\n' + output, flush=True)
    if not watch:
        print('\nLiteLLM model aliases', flush=True)
        try:
            print('\n'.join(str(m['id']) for m in gateway('/models', timeout=20)['data']))
        except Exception as exc:
            failed = True
            print('CHECK FAILED: ' + redact(exc))
        for name in ('open-webui', 'litellm'):
            print(f'\n{name}: errors in last 50 log lines (past 24 hours)')
            code, logs = command(['docker', 'logs', '--since', '24h', '--tail', '50', '--timestamps', name])
            if code:
                failed = True
                print('CHECK FAILED: ' + logs)
            else:
                errors = [line for line in logs.splitlines() if re.search(r'(?i)\b(error|exception|traceback|fatal|critical|failed)\b', line)]
                print('\n'.join(errors[-50:]) or 'No matching errors in sampled log lines.')
    return int(failed)

if __name__ == '__main__':
    sys.exit(main())
