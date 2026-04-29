"""
Load test configuration using Locust.
Simulates concurrent tradespeople interacting with TradesBot.

Usage:
  pip install locust
  locust -f tests/locustfile.py --host http://localhost:8000
"""
from uuid import uuid4
from locust import HttpUser, task, between


class TradesBotUser(HttpUser):
    """Simulates a tradesperson interacting via WhatsApp."""
    wait_time = between(1, 3)

    def on_start(self):
        self.user_num = self.environment.runner.user_count
        self.phone = f"whatsapp:+9198765{self.user_num:05d}"

    def _webhook(self, body: str):
        """Send a message through the Twilio webhook."""
        self.client.post(
            "/api/webhooks/twilio",
            data={
                "MessageSid": f"SM{uuid4().hex[:32]}",
                "From": self.phone,
                "To": "whatsapp:+14155238886",
                "Body": body,
                "NumMedia": "0",
            },
            name="/api/webhooks/twilio",
        )

    @task(5)
    def send_text_message(self):
        """Most common: general text query."""
        self._webhook("I need a plumber tomorrow morning")

    @task(3)
    def request_quote(self):
        """Request a price quote."""
        self._webhook("How much to fix a leaking tap?")

    @task(2)
    def schedule_job(self):
        """Schedule a job."""
        self._webhook("Book a plumber for Friday at 3 PM at my house")

    @task(1)
    def request_invoice(self):
        """Generate an invoice."""
        self._webhook("Generate invoice for tap repair, 2 hours for Mr. Kumar")

    @task(1)
    def check_job_status(self):
        """Check job status."""
        self._webhook("Show me my pending jobs")

    @task(1)
    def request_marketing(self):
        """Request a marketing promo."""
        self._webhook("Create a promo ad for plumbing services")

    @task(2)
    def health_check(self):
        """Lightweight health check."""
        self.client.get("/health", name="/health")

    @task(1)
    def detect_language(self):
        """Test language detection API."""
        self.client.get(
            "/api/language/detect",
            params={"text": "Mujhe ek plumber chahiye"},
            name="/api/language/detect",
        )
