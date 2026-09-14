import unittest
from aiohttp.test_utils import AioHTTPTestCase
from server import create_app, KEYS
from androidtvremote2.remotemessage_pb2 import RemoteKeyCode

class FakeRemote:
    def __init__(self): self.commands = []
    def add_is_available_updated_callback(self, callback): self.callback = callback
    def disconnect(self): self.callback(False)
    async def async_connect(self): self.callback(True)
    async def async_start_pairing(self): pass
    async def async_finish_pairing(self, code): self.code = code
    def keep_reconnecting(self): pass
    def send_key_command(self, value): self.commands.append(value)
    def send_launch_app_command(self, value): self.commands.append(value)

class BridgeTests(AioHTTPTestCase):
    async def get_application(self):
        self.remote = FakeRemote()
        return create_app(self.remote, 'test-secret', {'https://example.github.io'})

    async def test_static_assets(self):
        for path in ('/', '/style.css', '/app.js', '/favicon.svg'):
            self.assertEqual((await self.client.get(path)).status, 200)

    async def test_auth_and_origin(self):
        self.assertEqual((await self.client.get('/api/status')).status, 401)
        self.assertEqual((await self.client.post('/api/connect', headers={'Origin': 'https://evil.example','Authorization':'Bearer test-secret'})).status, 403)
        response = await self.client.options('/api/status', headers={'Origin':'https://example.github.io'})
        self.assertEqual(response.status, 204)
        self.assertEqual(response.headers['Access-Control-Allow-Origin'], 'https://example.github.io')
        self.assertEqual((await self.client.get('/data/token.txt')).status, 404)

    async def test_pair_controls_and_disconnect(self):
        headers = {'Authorization':'Bearer test-secret'}
        response = await self.client.post('/api/key', json={'value':'DPAD_UP'}, headers=headers)
        self.assertEqual(response.status,409)
        self.assertEqual((await self.client.post('/api/pair-start', headers=headers)).status,200)
        self.assertEqual((await self.client.post('/api/pair-finish', json={'code':'bad'}, headers=headers)).status,400)
        self.assertEqual((await self.client.post('/api/pair-finish', json={'code':'ABC123'}, headers=headers)).status,200)
        for value in KEYS:
            RemoteKeyCode.Value('KEYCODE_' + value)
            self.assertEqual((await self.client.post('/api/key',json={'value':value},headers=headers)).status,200)
        self.assertEqual((await self.client.post('/api/key',json={'value':'INVALID'},headers=headers)).status,400)
        self.remote.callback(False)
        self.assertFalse((await (await self.client.get('/api/status',headers=headers)).json())['connected'])

if __name__ == '__main__': unittest.main()
