import unittest

from decentralised_art_mcp.client import DecentralisedArtClient, parse_sse_replay_lines


class FakeResponse:
    ok = True
    status_code = 200
    text = ""

    def __init__(self, payload, *, lines=None):
        self.payload = payload
        self.lines = lines or []
        self.closed = False

    def json(self):
        return self.payload

    def raise_for_status(self):
        return None

    def iter_lines(self, decode_unicode=False):
        return iter(self.lines)

    def close(self):
        self.closed = True


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
        client = DecentralisedArtClient("https://api.example/chain")
        session = FakeSession()
        client.session = session

        cursor = "ab" * 32
        client.list_formats(limit=10, after=cursor)

        self.assertEqual(session.calls[0][1], "https://api.example/chain/formats")
        self.assertEqual(session.calls[0][2]["params"], {"limit": 10, "after": cursor})

    def test_path_segments_are_url_encoded(self):
        client = DecentralisedArtClient("https://api.example/chain")
        session = FakeSession()
        client.session = session

        client.get_format("abc/def", limit=1)

        self.assertEqual(session.calls[0][1], "https://api.example/chain/format/abc%2Fdef")

    def test_condition_uses_condition_endpoint(self):
        client = DecentralisedArtClient("https://api.example/chain")
        session = FakeSession()
        client.session = session

        client.get_condition("cond/a")

        self.assertEqual(session.calls[0][1], "https://api.example/chain/condition/cond%2Fa")

    def test_feed_page_uses_current_cursor_and_type_params(self):
        client = DecentralisedArtClient("https://api.example/chain")
        session = FakeSession()
        client.session = session

        client.get_feed_page(limit=7, before="42:abc", event_type="connector_added", include_unfinalized=True)

        self.assertEqual(session.calls[0][1], "https://api.example/chain/feed")
        self.assertEqual(
            session.calls[0][2]["params"],
            {"limit": 7, "before": "42:abc", "type": "connector_added", "include_unfinalized": 1},
        )

    def test_parse_sse_replay_lines_stops_at_stream_meta(self):
        payload = parse_sse_replay_lines(
            [
                ": connected",
                "id: 9",
                "event: event_delta",
                'data: {"feed_id":"connector:demo","seq":9}',
                "",
                "event: stream_meta",
                'data: {"replay_count":1,"live":false}',
                "",
                "event: event_delta",
                'data: {"feed_id":"ignored"}',
                "",
            ]
        )

        self.assertEqual(payload["comments"], ["connected"])
        self.assertEqual(payload["deltas"][0]["id"], "9")
        self.assertEqual(payload["deltas"][0]["data"]["feed_id"], "connector:demo")
        self.assertEqual(payload["meta"], {"replay_count": 1, "live": False})

    def test_client_close_closes_session(self):
        client = DecentralisedArtClient("https://api.example/chain")
        session = FakeSession()
        client.session = session

        client.close()

        self.assertTrue(session.closed)


if __name__ == "__main__":
    unittest.main()
