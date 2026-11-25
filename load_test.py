"""Locust load test for Reqres GET /users?page=2.

Usage (keep total calls <= 100/day!):
    export REQRES_API_KEY=your_key
    locust -f load_test.py --host https://reqres.in/api --headless \
           -u 5 -r 1 -t 30s --csv results/run2
Web UI instead:  locust -f load_test.py --host https://reqres.in/api
"""
import os

from locust import HttpUser, between, task


class ReqresUser(HttpUser):
    # Slow think-time keeps total request count low (API quota friendly)
    wait_time = between(3, 5)

    def on_start(self):
        """Runs once per simulated user: attach the API key."""
        self.client.headers.update({"x-api-key": os.getenv("REQRES_API_KEY", "")})

    @task
    def list_users(self):
        with self.client.get("/users?page=2", name="GET /users", catch_response=True) as r:
            if r.status_code != 200:
                r.failure(f"Unexpected status {r.status_code}")
            elif "data" not in r.json():
                r.failure("'data' key missing in response")
            else:
                r.success()
