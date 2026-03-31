from collections import defaultdict
from datetime import datetime
from typing import Dict

import numpy as np
from sqlalchemy import Boolean

from app.config import TICKERS, USER_PROFILES, GENERATE_NEW_INDIVIDUAL, GENERATE_NEW_CROSS
from app.db.schemas.portfolio import PortfolioHistoryCreate, PortfolioShareCreate
from app.decisionMakers.tickerMaster.GEMINI_MASTER import GEMINI_MASTER
from app.decisionMakers.horizonRanker.GEMINI_HORIZON import GEMINI_HORIZON
from app.decisionMakers.tickerMaster.TickerDataSerializer import TickerDataSerializer
from app.services.layers.news_narrative_service import NewsNarrativeService
from app.simulation.DeterministicDecisionMaker import  DeterministicDecisionMaker
from app.simulation.portfolio import Portfolio
from app.core import market_hours
from app.testy.compute import data_valuation


class UserSimulator:
    def __init__(
        self,
        user_id: int,
        starting_cash: float,
        decision_maker,
        portfolio_service,
        market_data_service,
        valuation_service,
        fundamental_service,
        transaction_service,
        analyst_service,
        company_daily_summary_service,
        shares: Dict[str, int] = None,
        with_explanation: bool = False,
    ):
        self.user_id = user_id
        self.portfolio = Portfolio(
            portfolio_id=user_id,
            starting_cash=starting_cash,
            user_profile=USER_PROFILES[decision_maker],
            shares=shares
        )

        self.decision_maker = decision_maker
        self.portfolio_service = portfolio_service
        self.market_data_service = market_data_service
        self.valuation_service = valuation_service
        self.engine = DeterministicDecisionMaker(self.valuation_service)
        self.company_daily_summary_service=company_daily_summary_service
        self.news_narrative_service = NewsNarrativeService(company_daily_summary_service)
        self.transaction_service = transaction_service
        self.with_explanation = with_explanation
        self.fundamental_service = fundamental_service
        self.analyst_service = analyst_service

        self.llm_models = {ticker: GEMINI_MASTER() for ticker in TICKERS}
        self.horizon_master = GEMINI_HORIZON()

        self.serializer = TickerDataSerializer()

    def get_crucial_indicators(self, date_time: datetime, ticker: str):
        if not market_hours.is_market_open_by_exchange(ticker, date_time):
            return

        analyst_grades = self.analyst_service.get_latest(ticker, date_time, 2)

        fundamentals = self.fundamental_service.get_latest(
            ticker,
            date_time
        )

        ohlcv = self.market_data_service.get_indicators(
            ticker,
            date_time,
            use_daily=True
        )

        current_valuation = data_valuation.calculate(
            fundamentals,
            ohlcv["Close"]
        )

        news_narrative = self.news_narrative_service.get_narrative_context(ticker, date_time.date())

        llm_result = self.llm_models[ticker].analyze(
            ticker,
            analyst_grades,
            fundamentals,
            ohlcv,
            current_valuation,
            news_narrative
        )

        results = {
            "structured_input": llm_result["input"],
            "llm_output": llm_result["output"]
        }

        return results

    # ---------------------------------------------------------
    # Główny proces jednego dnia
    # ---------------------------------------------------------

    def fetch_or_load_indicators(self, date_time: datetime) -> dict:
        crucial_indicators = {}
        for ticker in TICKERS:
            if GENERATE_NEW_INDIVIDUAL:
                data = self.get_crucial_indicators(date_time, ticker)
                if data and "structured_input" in data and "llm_output" in data:
                    crucial_indicators[ticker] = data
                    self.serializer.serialize(ticker, date_time, "structured_input", data["structured_input"])
                    self.serializer.serialize(ticker, date_time, "llm_output", data["llm_output"])
            else:
                try:
                    crucial_indicators[ticker] = {
                        "structured_input": self.serializer.deserialize(ticker, date_time, "structured_input"),
                        "llm_output": self.serializer.deserialize(ticker, date_time, "llm_output")
                    }
                except FileNotFoundError:
                    continue
        return crucial_indicators

    def process_day(self, date_time: datetime, crucial_indicators, cross_section_result) -> None:

        if not cross_section_result:
            return

        self._execute_trading_logic(
            cross_section_result,
            date_time
        )

    def build_overlapping_groups(self):

        return [
            ["NVDA", "AAPL", "TSM", "MSFT", "V", "JPM"], # Sektor: Technologiczny + Finansowy
            ["MSFT", "NVDA", "DIS", "NFLX", "WMT", "COST"], # Sektor: Technologiczny  + Konsumencki
            ["JPM", "V", "XOM", "CVX", "GE", "BA"], # Sektor: Finansowy + Energetyczny + Przemysłowy
            ["WMT", "COST", "NKE", "SBUX", "DIS", "NFLX"],  # Sektor: Konsumencki
            ["XOM", "CVX", "JNJ", "PFE", "BA", "GE"] # Sektor: Energetyczny + Ochrona zdrowia + Przemysłowy
        ]

    def perform_cross_section_once(self, date_time: datetime, indicators: dict) -> dict:

        cross_section = {
            t: d["llm_output"]["horizons"]
            for t, d in indicators.items()
            if d.get("llm_output", {}).get("horizons")
        }

        if len(cross_section) < 2:
            return None

        if not GENERATE_NEW_CROSS:
            try:
                return {
                    "llm_ranker": self.serializer.deserialize(
                        "CROSS_SECTION", date_time, "llm_ranker"
                    )
                }
            except FileNotFoundError:
                return None

        groups = self.build_overlapping_groups()

        group_results = []

        for group in groups:

            group_data = {
                t: cross_section[t]
                for t in group
                if t in cross_section
            }

            if len(group_data) < 3:
                continue

            result = self.horizon_master.analyze(date_time, group_data)

            if result and "llm_ranker" in result:
                group_results.append(result["llm_ranker"])

        if not group_results:
            return None

        merged = self.merge_group_results(group_results)

        self.serializer.serialize(
            "CROSS_SECTION",
            date_time,
            "llm_ranker",
            merged
        )

        return {"llm_ranker": merged}

    def merge_group_results(self, group_results):

        horizons = ["short_term_14d", "medium_term_50d", "long_term_200d"]

        accumulator = {
            h: defaultdict(lambda: defaultdict(list))
            for h in horizons
        }

        summaries = {
            h: defaultdict(list)
            for h in horizons
        }

        for result in group_results:
            for h in horizons:
                for ticker, data in result[h].items():

                    for metric, value in data["relative_scores"].items():
                        accumulator[h][ticker][metric].append(value)

                    summaries[h][ticker].append(data["relative_summary"])

        merged = {h: {} for h in horizons}

        for h in horizons:
            for ticker in accumulator[h]:
                scores = {
                    m: float(np.mean(v))
                    for m, v in accumulator[h][ticker].items()
                }

                merged[h][ticker] = {
                    "relative_scores": scores,
                    "relative_summary": summaries[h][ticker][0]
                }

        return merged

    def _execute_trading_logic(self, analysis_result: dict, date_time: datetime) -> None:
        decisions = self.engine.make_decision(analysis_result["llm_ranker"], self.portfolio, date_time)

        pre_state = (self.portfolio.cash, dict(self.portfolio.shares))
        self._execute_decisions(decisions, date_time)

        if self._portfolio_changed(*pre_state):
            history_data = PortfolioHistoryCreate(
                datetime=date_time,
                cash=self.portfolio.cash,
                shares=[PortfolioShareCreate(ticker=t, amount=a) for t, a in self.portfolio.shares.items()]
            )
            self.portfolio_service.evaluate(self.portfolio.portfolio_id, history_data)

    # ---------------------------------------------------------
    # Wspomagające funkcje
    # ---------------------------------------------------------

    def _execute_decisions(self, decisions: dict, date_time: datetime):
        """
        Przetwarza słownik decyzji: {'AAPL': {'DECISION': 'BUY', 'NUMBER': 10}, ...}
        """
        for ticker, d in decisions.items():
            decision_type = d.get("DECISION")  # "BUY" lub "SELL"
            quantity = d.get("NUMBER")  # int

            # 1. Sprawdzenie godzin rynkowych (korzystając z Twojej logiki)
            if not market_hours.is_market_open_by_exchange(ticker, date_time):
                # print(f"Market closed for {ticker} at {date_time}")
                continue

            # 2. Pobranie aktualnej ceny z MarketDataService
            price = self.market_data_service.get_price(ticker, date_time)

            if price is None or price <= 0:
                print(f"Skipping {ticker}: Price not available")
                continue

            # 3. Wykonanie fizycznej transakcji
            self.execute_decision(ticker, decision_type, quantity, price, date_time)

    def execute_decision(self, ticker: str, decision: str, num: int, price: float, date_time: datetime):
        if decision in ["BUY", "SELL"]:
            if decision == "BUY":
                self.portfolio.buy(ticker, num, price)
            elif decision == "SELL":
                self.portfolio.sell(ticker, num, price)

            print(f"{self.user_id} ➤ {date_time} ➤ {ticker} ➤ {decision} {num}")

            self.transaction_service.record_transaction(
                portfolio_id=self.portfolio.portfolio_id,
                ticker=ticker,
                type_=decision,
                quantity=num,
                price=price,
                datetime_=date_time,
            )

    def _portfolio_changed(self, pre_cash, pre_shares) -> bool:
        return self.portfolio.cash != pre_cash or self.portfolio.shares != pre_shares


    def _print_nested_dict(self, data, indent=0):
        """Rekurencyjnie wypisuje słownik z wcięciami."""
        indent_str = "  " * indent

        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, dict):
                    print(f"{indent_str}{key}:")
                    self._print_nested_dict(value, indent + 1)
                else:
                    print(f"{indent_str}{key}: {value}")
        else:
            print(f"{indent_str}{data}")
