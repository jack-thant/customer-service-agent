import re


class RouterService:
    APPLICATION_STATUS_KEYWORDS = [
        "application status",
        "status of my application",
        "my application",
        "card application",
        "application progress",
    ]

    FAILED_TRANSACTION_KEYWORDS = [
        "transaction failed",
        "failed transaction",
        "declined transaction",
        "card was declined",
        "payment failed",
        "transaction declined",
        "my transaction failed",
    ]

    TRANSACTION_ID_PATTERN = re.compile(r"\bTX[0-9A-Za-z]+\b", re.IGNORECASE)

    def detect_route(self, message: str) -> str:
        normalized = self._normalize(message)

        if self.is_application_status_query(normalized):
            return "application_status"

        if self.is_failed_transaction_query(normalized):
            return "failed_transaction"

        return "rag"

    def is_application_status_query(self, message: str) -> bool:
        return any(keyword in message for keyword in self.APPLICATION_STATUS_KEYWORDS)

    def is_failed_transaction_query(self, message: str) -> bool:
        return any(keyword in message for keyword in self.FAILED_TRANSACTION_KEYWORDS)

    def extract_transaction_id(self, message: str) -> str | None:
        match = self.TRANSACTION_ID_PATTERN.search(message)
        return match.group(0).upper() if match else None

    def is_valid_transaction_id(self, value: str) -> bool:
        return bool(self.TRANSACTION_ID_PATTERN.fullmatch(value.strip()))

    @staticmethod
    def _normalize(message: str) -> str:
        return " ".join(message.lower().strip().split())