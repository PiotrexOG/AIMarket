class NewsNarrativeBuilder:
    """
    Transformuje MarketNewsContextDTO na listy kluczowych wydarzeń (summaries).
    Dostarcza LLM surową, ale wyselekcjonowaną treść newsów z podziałem na horyzonty.
    """

    def build(self, news_context) -> dict:
        if not news_context:
            return {"news_narrative": "NO_DATA"}

        return {
            "short_term_14d": self._format_list(news_context.short_term_14d),
            "medium_term_50d": self._format_list(news_context.medium_term_50d),
            "long_term_200d": self._format_list(news_context.long_term_200d)
        }

    def _format_list(self, news_list) -> list[str]:
        if not news_list:
            return ["No significant news reported"]

        # Zwracamy listę sformatowanych stringów
        return [
            n.summary
            for n in news_list
        ]