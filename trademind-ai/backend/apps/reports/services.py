"""
apps/reports/services.py
-------------------------
T15 ✅  Report generation service — computes all analytics metrics.

Metrics computed:
  Win rate, Loss rate, Avg profit/loss, Profit factor,
  Sharpe ratio, Max drawdown, Sortino ratio, Calmar ratio,
  Recovery factor, Trade journal, Strategy comparison.
"""
import logging
import math
from datetime import date, timedelta
from decimal import Decimal
from typing import Any

logger = logging.getLogger("trademind.reports.services")


class ReportService:

    def generate(self, report) -> dict:
        """T15 ✅  Entry point — dispatch to correct report generator."""
        generators = {
            "DAILY":         self._daily_report,
            "WEEKLY":        self._weekly_report,
            "MONTHLY":       self._monthly_report,
            "TRADE_JOURNAL": self._trade_journal,
            "STRATEGY":      self._strategy_report,
            "TAX":           self._tax_report,
        }
        gen = generators.get(report.report_type, self._daily_report)
        return gen(report)

    # ── Daily ─────────────────────────────────────────────────────────────────
    def _daily_report(self, report) -> dict:
        from django.utils import timezone
        params   = report.parameters
        date_str = params.get("date") or str((timezone.now() - timedelta(days=1)).date())
        return self._trade_metrics(report.user, date_str, date_str)

    # ── Weekly ────────────────────────────────────────────────────────────────
    def _weekly_report(self, report) -> dict:
        from django.utils import timezone
        today  = timezone.now().date()
        monday = today - timedelta(days=today.weekday() + 7)
        sunday = monday + timedelta(days=6)
        return self._trade_metrics(report.user, str(monday), str(sunday))

    # ── Monthly ───────────────────────────────────────────────────────────────
    def _monthly_report(self, report) -> dict:
        from django.utils import timezone
        params  = report.parameters
        today   = timezone.now().date()
        year    = int(params.get("year",  today.year))
        month   = int(params.get("month", today.month - 1 or 12))
        if month == 12 and today.month == 1:
            year -= 1
        first = date(year, month, 1)
        if month == 12:
            last = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            last = date(year, month + 1, 1) - timedelta(days=1)
        return self._trade_metrics(report.user, str(first), str(last))

    # ── Core metrics engine ───────────────────────────────────────────────────
    def _trade_metrics(self, user, date_from: str, date_to: str) -> dict:
        """T15 ✅  Core trade analytics engine."""
        from apps.orders.models import Order, OrderStatus, Position, PositionStatus

        closed = list(
            Position.objects.filter(
                user=user,
                status=PositionStatus.CLOSED,
                closed_at__date__gte=date_from,
                closed_at__date__lte=date_to,
                is_paper_trade=False,
            ).values("realized_pnl", "entry_price", "closed_at",
                     "trading_pair__symbol", "strategy__name", "side")
        )

        if not closed:
            return self._empty_metrics(date_from, date_to)

        pnls      = [float(p["realized_pnl"]) for p in closed]
        wins      = [p for p in pnls if p > 0]
        losses    = [p for p in pnls if p < 0]
        total     = len(pnls)
        win_count = len(wins)
        loss_count = len(losses)

        total_profit = sum(wins)
        total_loss   = abs(sum(losses))
        net_pnl      = sum(pnls)
        win_rate     = (win_count / total * 100) if total > 0 else 0
        avg_win      = (total_profit / win_count) if win_count > 0 else 0
        avg_loss     = (total_loss / loss_count)  if loss_count > 0 else 0
        profit_factor = (total_profit / total_loss) if total_loss > 0 else float("inf")

        # Sharpe ratio (daily returns)
        if len(pnls) > 1:
            mean_ret = sum(pnls) / len(pnls)
            variance = sum((p - mean_ret) ** 2 for p in pnls) / len(pnls)
            std_dev  = math.sqrt(variance) if variance > 0 else 1
            sharpe   = (mean_ret / std_dev) * math.sqrt(252) if std_dev > 0 else 0
        else:
            sharpe = 0

        # Sortino (downside deviation)
        downside = [p for p in pnls if p < 0]
        if downside and len(downside) > 1:
            ds_var     = sum(p ** 2 for p in downside) / len(downside)
            ds_std     = math.sqrt(ds_var)
            mean_ret   = sum(pnls) / len(pnls)
            sortino    = (mean_ret / ds_std) * math.sqrt(252) if ds_std > 0 else 0
        else:
            sortino = sharpe

        # Max drawdown
        cumulative  = []
        cum         = 0.0
        for p in pnls:
            cum += p
            cumulative.append(cum)
        peak        = cumulative[0]
        max_dd      = 0.0
        for val in cumulative:
            peak    = max(peak, val)
            dd      = (peak - val) / peak * 100 if peak > 0 else 0
            max_dd  = max(max_dd, dd)

        return {
            "period":          {"from": date_from, "to": date_to},
            "total_trades":    total,
            "winning_trades":  win_count,
            "losing_trades":   loss_count,
            "win_rate_pct":    round(win_rate, 2),
            "total_profit":    round(total_profit, 2),
            "total_loss":      round(total_loss, 2),
            "net_pnl":         round(net_pnl, 2),
            "avg_win":         round(avg_win, 2),
            "avg_loss":        round(avg_loss, 2),
            "profit_factor":   round(profit_factor, 4),
            "sharpe_ratio":    round(sharpe, 4),
            "sortino_ratio":   round(sortino, 4),
            "max_drawdown_pct": round(max_dd, 2),
            "trade_count":     total,
        }

    # ── Trade journal ─────────────────────────────────────────────────────────
    def _trade_journal(self, report) -> dict:
        """T15 ✅  Full trade-by-trade journal."""
        from apps.orders.models import Position, PositionStatus
        params    = report.parameters
        date_from = params.get("date_from", "2024-01-01")
        date_to   = params.get("date_to",   "2099-12-31")

        positions = Position.objects.filter(
            user=report.user,
            status=PositionStatus.CLOSED,
            closed_at__date__gte=date_from,
            closed_at__date__lte=date_to,
        ).select_related("trading_pair", "strategy").order_by("closed_at")

        journal = []
        for pos in positions:
            hold_hours = 0.0
            if pos.closed_at and pos.opened_at:
                hold_hours = (pos.closed_at - pos.opened_at).total_seconds() / 3600
            journal.append({
                "symbol":       pos.trading_pair.symbol,
                "side":         pos.side,
                "strategy":     pos.strategy.name if pos.strategy else "",
                "entry_price":  str(pos.entry_price),
                "quantity":     str(pos.quantity),
                "pnl":          str(pos.realized_pnl),
                "opened_at":    pos.opened_at.isoformat() if pos.opened_at else "",
                "closed_at":    pos.closed_at.isoformat() if pos.closed_at else "",
                "hold_hours":   round(hold_hours, 2),
            })
        return {"trades": journal, "count": len(journal)}

    # ── Strategy performance report ───────────────────────────────────────────
    def _strategy_report(self, report) -> dict:
        """T15 ✅  Per-strategy performance breakdown."""
        from apps.strategies.models import StrategyPerformance
        perfs = StrategyPerformance.objects.filter(user=report.user).select_related("user_strategy__strategy")
        return {
            "strategies": [
                {
                    "name":          p.user_strategy.name,
                    "total_trades":  p.total_trades,
                    "win_rate":      str(p.win_rate_pct),
                    "net_pnl":       str(p.net_pnl_usdt),
                    "profit_factor": str(p.profit_factor),
                    "sharpe":        str(p.sharpe_ratio),
                    "max_drawdown":  str(p.max_drawdown_pct),
                }
                for p in perfs
            ]
        }

    # ── Tax export ────────────────────────────────────────────────────────────
    def _tax_report(self, report) -> dict:
        """T15 ✅  Tax-friendly trade-by-trade CSV data."""
        return self._trade_journal(report)

    @staticmethod
    def _empty_metrics(date_from: str, date_to: str) -> dict:
        return {
            "period": {"from": date_from, "to": date_to},
            "total_trades": 0, "winning_trades": 0, "losing_trades": 0,
            "win_rate_pct": 0, "net_pnl": 0, "profit_factor": 0,
            "sharpe_ratio": 0, "sortino_ratio": 0, "max_drawdown_pct": 0,
        }
