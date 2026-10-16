import importlib.util
import io
import json
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location("replacement", Path(__file__).resolve().parents[1] / "deploy/replace-blessrom-token.py")
replacement = importlib.util.module_from_spec(spec)
spec.loader.exec_module(replacement)

class ReplacementTests(unittest.TestCase):
    def test_correct_page_and_read_are_checked_without_token_in_url(self):
        requests = []
        def opener(request, timeout):
            requests.append(request)
            self.assertNotIn("test-token", request.full_url)
            self.assertEqual(request.get_header("Authorization"), "Bearer test-token")
            data = {"id": replacement.PAGE} if len(requests) == 1 else {"data": []}
            return io.BytesIO(json.dumps(data).encode())
        replacement.verify_token("test-token", "v26.0", opener)
        self.assertEqual(len(requests), 2)

    def test_user_token_is_rejected_before_page_read(self):
        def opener(request, timeout):
            return io.BytesIO(b'{"id":"user-id"}')
        with self.assertRaises(ValueError):
            replacement.verify_token("test-token", "v26.0", opener)

    def test_invalid_version_never_makes_a_request(self):
        def opener(*args, **kwargs):
            self.fail("No network call expected")
        with self.assertRaises(ValueError):
            replacement.verify_token("test-token", "../../another-host", opener)

if __name__ == "__main__":
    unittest.main()
