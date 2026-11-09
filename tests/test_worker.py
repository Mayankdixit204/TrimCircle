import unittest
from unittest.mock import patch

import worker
from app.provider import ProviderUnavailable


class WorkerTests(unittest.TestCase):
    @patch("worker.cleanup_expired")
    @patch("worker.update_job")
    @patch("worker.process_remote_job")
    @patch("worker.next_job")
    def test_unconfigured_provider_returns_job_to_waiting(self, next_job, process, update, cleanup):
        next_job.return_value = {"id": "private-test-job"}
        process.side_effect = ProviderUnavailable("not configured")
        self.assertEqual(worker.run_once(), 0)
        self.assertEqual(update.call_args_list[-1].kwargs["status"], "awaiting_gpu")

    @patch("worker.cleanup_expired")
    @patch("worker.process_remote_job")
    @patch("worker.update_job")
    @patch("worker.next_job")
    def test_configured_provider_completes_one_job(self, next_job, update, process, cleanup):
        next_job.return_value = {"id": "private-test-job"}
        self.assertEqual(worker.run_once(), 1)
        process.assert_called_once_with("private-test-job")


if __name__ == "__main__":
    unittest.main()
