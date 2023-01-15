from typing import Optional, List
from logging import getLogger, Logger
from json import dumps
from time import time, sleep

from locust import events
from locust.argument_parser import LocustArgumentParser
from locust.env import Environment


class AggregatedReport:
    pass


class ReportAggregator:
    _raw_reports: List[dict]

    def __init__(self) -> None:
        self._raw_reports = []

    def push(self, report: dict) -> None:
        self._raw_reports.append(report)

    def aggregate(self) -> AggregatedReport:
        return AggregatedReport()


class CWMetricsPlugin:
    """Locust plugin sending stats to AWS CloudWatch metrics
    @link https://docs.locust.io/en/stable/api.html#event-hooks
    @link https://github.com/concurrencylabs/locust-cloudwatch/blob/master/locust_cw.py
    @link https://github.com/SvenskaSpel/locust-plugins/blob/master/locust_plugins/listeners.py
    """

    env: Environment
    """Locust Environment"""

    logger: Logger
    """Logger"""

    aggregator: ReportAggregator
    """Report aggregator"""

    def __init__(self, env: Environment) -> None:
        self.env = env
        self.logger = getLogger(__name__)
        self.logger.setLevel("DEBUG")  # TODO: delete me
        self.aggregator = ReportAggregator()

        # Register listeners to locust events
        events = env.events
        events.test_stop.add_listener(self.on_test_stop)
        events.worker_report.add_listener(self.on_worker_report)

        self.logger.debug("CloudWatch metrics plugin's events are registered")

    def on_test_stop(self, environment: Environment) -> None:
        """テストが終了した時に呼ばれる"""
        self.logger.info("CloudWatch metrics plugin has stopped")
        # TODO: 残ったメトリクスを送信する

    def on_worker_report(self, client_id: str, data: dict) -> None:
        """ワーカーから記録が届いた時に呼ばれる
        client_id : str
        data : dict
        """
        self.aggregator.push(dict(client_id=client_id, data=data))
        sleep(10.0)


_singleton_instance: Optional[CWMetricsPlugin] = None


def load_cw_metrics_plugin():
    """Load and initialize plugin"""

    @events.init_command_line_parser.add_listener
    def _add_arguments(parser: LocustArgumentParser):
        """CloudWatch metrics を有効化するかどうかのフラグを追加"""
        parser.add_argument(
            "--cw-metrics",
            type=int,
            help="Enables CloudWatch metrics logging",
            env_var="LOCUST_CW_METRICS",
            default=0,
        )

    @events.test_start.add_listener
    def _on_test_start(environment: Environment):
        """Make instance when starting test(only master node)"""
        global _singleton_instance
        if not environment.parsed_options.worker and environment.parsed_options.cw_metrics == 1:
            _singleton_instance = CWMetricsPlugin(env=environment)
