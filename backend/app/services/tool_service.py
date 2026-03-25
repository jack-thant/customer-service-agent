class ToolService:
    def get_application_status(self) -> str:
        return "Your card application is currently under review."

    def get_transaction_status(self, transaction_id: str) -> str:
        return (
            f"Transaction {transaction_id} appears to have failed due to insufficient funds. "
            f"Please verify your balance or try again later."
        )