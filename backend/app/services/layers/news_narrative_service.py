import math
from datetime import date

from app.dto.news_summary import MarketNewsContextDTO, NewsSummaryDTO
from app.services.layers.company_daily_summary import CompanyDailySummaryService


class NewsNarrativeService:
    def __init__(self, summary_service: CompanyDailySummaryService):
        self.summary_service = summary_service

    def get_narrative_context(self, ticker: str, target_date: date) -> MarketNewsContextDTO:
        # Tutaj używamy Twoich trzech metod z matematyką selekcji (lambda 0.2, 0.05, 0.01)
        return MarketNewsContextDTO(
            short_term_14d=self._fetch_top_news(ticker, target_date, 14, 0.2),
            medium_term_50d=self._fetch_top_news(ticker, target_date, 50, 0.05),
            long_term_200d=self._fetch_top_news(ticker, target_date, 200, 0.01)
        )

    def _fetch_top_news(self, ticker, target_date, limit_days, lambda_val) -> list[NewsSummaryDTO]:
        # 1. Pobieramy wszystkie newsy z okna czasowego z bazy
        news_items = self.summary_service.get_news_window(ticker, target_date, limit_days)

        if not news_items:
            return []

        scored_news = []

        for item in news_items:
            # Obliczamy różnicę dni (delta t)
            delta_t = (target_date - item.date).days

            # Zabezpieczenie przed ujemną deltą (newsy z przyszłości)
            if delta_t < 0:
                continue

            # MATEMATYKA SELEKCJI:
            # Importance do kwadratu premiuje "grube ryby" (10-tki)
            # Funkcja e^(-lambda * t) wygasza znaczenie z upływem czasu
            selection_score = (item.importance ** 2) * math.exp(-lambda_val * delta_t)

            scored_news.append({
                "item": item,
                "selection_score": selection_score
            })

        # 2. Sortujemy według obliczonego wyniku (od najwyższego)
        scored_news.sort(key=lambda x: x["selection_score"], reverse=True)

        # 3. Wybieramy Top 3 i mapujemy na NewsSummaryDTO
        top_3 = []
        for sn in scored_news[:3]:
            obj = sn["item"]
            top_3.append(NewsSummaryDTO(
                summary=obj.summary,
                importance=obj.importance,
                date=obj.date
            ))

        return top_3