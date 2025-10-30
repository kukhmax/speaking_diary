class StripeProvider:
    """Заглушка провайдера Stripe Checkout.

    В реальной интеграции здесь создаётся `stripe.checkout.Session`
    и возвращается URL редиректа на оплату.
    """

    def __init__(self, secret_key: str | None = None, price_id: str | None = None):
        """Инициализация провайдера с ключом и ID цены/плана."""
        self.secret_key = secret_key
        self.price_id = price_id

    def create_checkout_session(self, user_id: int, success_url: str, cancel_url: str) -> dict:
        """Создаёт сессию оплаты (stub) и возвращает URL для редиректа."""
        return {
            'url': 'https://checkout.stripe.com/pay/example',
            'client_reference_id': str(user_id),
        }