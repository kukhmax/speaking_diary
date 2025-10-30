class TelegramProvider:
    """Заглушка провайдера Telegram Payments.

    В реальной интеграции вызывает Bot API `createInvoiceLink` и возвращает ссылку
    на оплату. Здесь возвращается тестовый stub.
    """

    def __init__(self, bot_token: str | None = None, provider_token: str | None = None):
        """Инициализация провайдера с токенами бота и провайдера платежей."""
        self.bot_token = bot_token
        self.provider_token = provider_token

    def create_invoice_link(
        self,
        title: str,
        description: str,
        payload: str,
        amount_cents: int,
        currency: str = 'USD',
    ) -> dict:
        """Создаёт ссылку на инвойс (stub).

        Возвращает словарь с полями `invoice_link`, `payload`, `amount_cents`, `currency`.
        """
        return {
            'invoice_link': 'https://t.me/pay?stub=example',
            'payload': payload,
            'amount_cents': amount_cents,
            'currency': currency,
        }