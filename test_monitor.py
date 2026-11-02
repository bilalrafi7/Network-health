import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
import server

class MonitorTests(unittest.TestCase):
    def test_successful_http(self):
        response = MagicMock()
        response.__enter__.return_value.status = 200
        with patch('server.urllib.request.urlopen', return_value=response):
            status, latency, detail = server.probe({'type':'http','url':'https://example.com'})
        self.assertEqual(status, 'up')
        self.assertGreaterEqual(latency, 0)
        self.assertEqual(detail, 'HTTP 200')

    def test_failure_is_recorded_without_fake_latency(self):
        with patch('server.socket.create_connection', side_effect=TimeoutError('Timed out')):
            status, latency, detail = server.probe({'type':'tcp','host':'example.com','port':443})
        self.assertEqual(status, 'down')
        self.assertIsNone(latency)

    def test_history_and_availability(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(server, 'DB', Path(folder)/'test.db'):
            server.initialize()
            targets=[{'name':'Test','type':'tcp','host':'localhost','port':8000}]
            with patch('server.probe', side_effect=[('up',10,'OK'),('down',None,'timeout')]):
                server.collect(targets)
                server.collect(targets)
            data=server.snapshot(targets)['targets'][0]
            self.assertEqual(data['uptime'],50)
            self.assertEqual(data['latest']['status'],'down')
            self.assertEqual(len(data['history']),2)

if __name__ == '__main__':
    unittest.main()
