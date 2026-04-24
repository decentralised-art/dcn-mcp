import unittest

from dcn_mcp.client import DCNClient


class FakeResponse:
    ok = True
    status_code = 200
    text = ""

    def __init__(self, payload):
        self.payload = payload

    def json(self):
        return self.payload

    def raise_for_status(self):
        return None


class FakeSession:
    def __init__(self):
        self.headers = {}
        self.calls = []
        self.closed = False

    def get(self, url, **kwargs):
        self.calls.append(("get", url, kwargs))
        return FakeResponse({"ok": True})

    def close(self):
        self.closed = True


class ClientTests(unittest.TestCase):
    def test_query_params_are_passed_to_requests(self):
        client = DCNClient("https://api.example/chain")
        session = FakeSession()
        client.session = session

        client.list_formats(limit=10, after="abc&limit=999")

        self.assertEqual(session.calls[0][1], "https://api.example/chain/formats")
        self.assertEqual(session.calls[0][2]["params"], {"limit": 10, "after": "abc&limit=999"})

    def test_path_segments_are_url_encoded(self):
        client = DCNClient("https://api.example/chain")
        session = FakeSession()
        client.session = session

        client.get_format("abc/def", limit=1)

        self.assertEqual(session.calls[0][1], "https://api.example/chain/format/abc%2Fdef")

    def test_client_close_closes_session(self):
        client = DCNClient("https://api.example/chain")
        session = FakeSession()
        client.session = session

        client.close()

        self.assertTrue(session.closed)


if __name__ == "__main__":
    unittest.main()
