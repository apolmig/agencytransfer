import tempfile
import unittest
from pathlib import Path

from evals.run_openrouter_ape_pilot import public_error, response_text, validate_output_paths


class RunnerHelpersTest(unittest.TestCase):
    def test_response_text_extracts_content(self) -> None:
        result = {"choices": [{"message": {"content": "ok"}}]}
        self.assertEqual(response_text(result), "ok")
        self.assertEqual(response_text(None), "")
        self.assertEqual(response_text({"choices": []}), "")

    def test_public_error_removes_provider_detail(self) -> None:
        self.assertEqual(public_error("OpenRouter HTTP 429: private detail"), "OpenRouter HTTP 429")
        self.assertEqual(public_error("judge parse error: private detail"), "judge parse error")
        self.assertEqual(public_error("socket detail"), "request error")
        self.assertIsNone(public_error(None))

    def test_private_output_must_be_outside_checkout_and_run_tree(self) -> None:
        repository_root = Path(__file__).resolve().parents[1]
        with self.assertRaises(ValueError):
            validate_output_paths(repository_root / "data/run", repository_root / "private")
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            with self.assertRaises(ValueError):
                validate_output_paths(base / "public", base)
            run_dir, raw_dir = validate_output_paths(base / "public", base / "private")
            self.assertNotEqual(run_dir, raw_dir)


if __name__ == "__main__":
    unittest.main()
