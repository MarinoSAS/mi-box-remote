"""Local Android TV Remote v2 bridge. Python 3.11+."""
import argparse
import asyncio
import ipaddress
import json
import os
from pathlib import Path
import secrets
import ssl
from aiohttp import web
from androidtvremote2 import AndroidTVRemote, InvalidAuth

ROOT = Path(__file__).resolve().parent
KEYS = set('DPAD_UP DPAD_DOWN DPAD_LEFT DPAD_RIGHT DPAD_CENTER BACK HOME POWER VOLUME_UP VOLUME_DOWN VOLUME_MUTE CHANNEL_UP CHANNEL_DOWN MEDIA_PLAY_PAUSE'.split())
APPS = {'netflix': 'netflix://', 'youtube': 'https://www.youtube.com', 'prime': 'https://app.primevideo.com'}


def create_app(remote, token, origins):
    lock = asyncio.Lock()
    state = {'connected': False, 'pairing': False}
    remote.add_is_available_updated_callback(lambda value: state.update(connected=value))

    @web.middleware
    async def guard(request, handler):
        origin = request.headers.get('Origin')
        own_origin = f'{request.scheme}://{request.host}'
        allowed = origin is None or origin == own_origin or origin in origins
        if not allowed:
            return web.json_response({'error': 'Η προέλευση της σελίδας δεν επιτρέπεται.'}, status=403)
        if request.method == 'OPTIONS':
            response = web.Response(status=204)
        elif request.path.startswith('/api/') and not secrets.compare_digest(request.headers.get('Authorization', ''), 'Bearer ' + token):
            response = web.json_response({'error': 'Λάθος κλειδί γέφυρας.'}, status=401)
        else:
            try:
                response = await handler(request)
            except InvalidAuth:
                response = web.json_response({'error': 'Χρειάζεται σύζευξη ή ο κωδικός είναι λάθος.'}, status=409)
            except (asyncio.TimeoutError, OSError):
                response = web.json_response({'error': 'Το Mi Box δεν απαντά. Έλεγξε IP, δίκτυο και ότι είναι ενεργό.'}, status=504)
            except web.HTTPException:
                raise
            except Exception:
                response = web.json_response({'error': 'Η ενέργεια απέτυχε. Έλεγξε το Box και κάνε νέα σύζευξη.'}, status=502)
        if origin:
            response.headers['Access-Control-Allow-Origin'] = origin
            response.headers['Vary'] = 'Origin'
            response.headers['Access-Control-Allow-Headers'] = 'Authorization, Content-Type'
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
            response.headers['Access-Control-Allow-Private-Network'] = 'true'
        response.headers['Cache-Control'] = 'no-store'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        return response

    async def connect():
        state['connected'] = False
        await asyncio.wait_for(remote.async_connect(), 15)
        state['connected'] = True
        remote.keep_reconnecting()

    async def status(request):
        return web.json_response(state)

    async def action(request):
        async with lock:
            verb = request.match_info['verb']
            if verb == 'connect':
                remote.disconnect()
                await connect()
            elif verb == 'pair-start':
                state.update(connected=False, pairing=False)
                remote.disconnect()
                await asyncio.wait_for(remote.async_start_pairing(), 15)
                state['pairing'] = True
            elif verb == 'pair-finish':
                data = await request.json()
                code = str(data.get('code', '')).strip().upper()
                if not state['pairing'] or len(code) != 6 or any(c not in '0123456789ABCDEF' for c in code):
                    return web.json_response({'error': 'Ξεκίνα σύζευξη και βάλε τον εξαψήφιο κωδικό της TV.'}, status=400)
                await asyncio.wait_for(remote.async_finish_pairing(code), 15)
                state['pairing'] = False
                await connect()
            elif verb in ('key', 'app'):
                data = await request.json()
                value = data.get('value')
                choices = KEYS if verb == 'key' else APPS
                if not isinstance(value, str) or value not in choices:
                    return web.json_response({'error': 'Άγνωστη εντολή.'}, status=400)
                if not state['connected']:
                    return web.json_response({'error': 'Το Mi Box δεν είναι συνδεδεμένο.'}, status=409)
                if verb == 'key':
                    remote.send_key_command(value)
                else:
                    remote.send_launch_app_command(APPS[value])
            else:
                raise web.HTTPNotFound()
            return web.json_response({'ok': True, **state})

    async def index(request):
        return web.FileResponse(ROOT / 'web' / 'index.html')

    async def close(app):
        remote.disconnect()

    app = web.Application(middlewares=[guard], client_max_size=4096)
    app.router.add_get('/api/status', status)
    app.router.add_post('/api/{verb}', action)
    app.router.add_route('OPTIONS', '/api/{verb}', status)
    app.router.add_get('/', index)
    app.router.add_static('/', ROOT / 'web', show_index=False)
    app.on_cleanup.append(close)
    return app


async def build(args):
    address = ipaddress.ip_address(args.tv)
    if not address.is_private or address.is_loopback or address.is_unspecified or address.is_multicast:
        raise ValueError('Χρησιμοποίησε την ιδιωτική IP του Mi Box.')
    data = ROOT / 'data'
    data.mkdir(mode=0o700, exist_ok=True)
    tokenfile = data / 'token.txt'
    if not tokenfile.exists():
        tokenfile.write_text(secrets.token_urlsafe(32))
        tokenfile.chmod(0o600)
    token = tokenfile.read_text().strip()
    remote = AndroidTVRemote('Marinos Web Remote', str(data / 'cert.pem'), str(data / 'key.pem'), args.tv)
    await remote.async_generate_cert_if_missing()
    for name in ('key.pem', 'cert.pem'):
        (data / name).chmod(0o600)
    print('Κλειδί γέφυρας (βάλε το στις Ρυθμίσεις της σελίδας):', token)
    print(f'Άνοιξε στο κινητό: http{"s" if args.cert else ""}://IP_ΥΠΟΛΟΓΙΣΤΗ:{args.port}')
    return create_app(remote, token, set(args.origin))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--tv', required=True, help='Τοπική IP του Mi Box')
    parser.add_argument('--port', type=int, default=8787)
    parser.add_argument('--bind', default='0.0.0.0')
    parser.add_argument('--origin', action='append', default=[], help='Επιτρεπόμενη προέλευση, π.χ. https://username.github.io')
    parser.add_argument('--cert', help='HTTPS certificate chain trusted by the phone')
    parser.add_argument('--key', help='HTTPS private key')
    args = parser.parse_args()
    if bool(args.cert) != bool(args.key):
        parser.error('--cert και --key χρειάζονται μαζί')
    context = None
    if args.cert:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(args.cert, args.key)
    web.run_app(build(args), host=args.bind, port=args.port, ssl_context=context)
