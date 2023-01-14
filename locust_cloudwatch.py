from typing import Union, Optional
from logging import getLogger, Logger
from json import dumps

from locust import events
from locust.argument_parser import LocustArgumentParser
from locust.env import Environment
from locust.web import Response
from locust.contrib.fasthttp import FastResponse


class CWMetricsPlugin:
    """CloudWatch に Locust のメトリクスを送信するプラグイン
    @link https://docs.locust.io/en/stable/api.html#event-hooks
    @link https://github.com/concurrencylabs/locust-cloudwatch/blob/master/locust_cw.py
    @link https://github.com/SvenskaSpel/locust-plugins/blob/master/locust_plugins/listeners.py
    """

    env: Environment
    """Locust Environment"""

    logger: Logger
    """Logger"""

    is_worker: bool
    """worker process かどうか"""

    def __init__(self, env: Environment) -> None:
        self.env = env
        self.logger = getLogger(__name__)
        self.logger.setLevel("DEBUG")
        self.is_worker = env.parsed_options.worker

        # Register funcs to locust events
        events = env.events
        events.test_stop.add_listener(self.on_test_stop)
        if not self.is_worker:
            events.worker_report.add_listener(self.on_worker_report)

        self.logger.debug("CloudWatch metrics plugin's events are registered.")

    def on_request(
        self,
        request_type: str,
        name: str,
        context: dict,
        response: Union[Response, FastResponse, None],
        exception: Optional[Exception] = None,
        start_time: Optional[float] = None,
        url: Optional[str] = None,
        response_length: Optional[int] = None,
        response_time: Optional[int] = None,
    ) -> None:
        """リクエストが終了した時に呼ばれる
        @link https://docs.locust.io/en/stable/api.html#locust.event.Events.request
        Parameters
        ----------
        request_type: str
            HTTP リクエストタイプ(GET/POST等)
        name: str
            リクエスト名(デフォルトでは path, 名前を付けることも可能)
            @link https://docs.locust.io/en/stable/api.html#locust.clients.HttpSession.request
        context: dict
            リクエストコンテキスト
            @link https://docs.locust.io/en/stable/extending-locust.html#request-context
        response: Union[Response, FastResponse, None]
            レスポンスクラス
        exception: Optional[Exception]
            失敗時の例外クラス
        start_time: Optional[float]
            リクエストを開始した時間(float unixtime)
        url: Optional[str]
            リクエストした URL
        response_length: Optional[int]
            レスポンスサイズ(byte)
        response_time: Optional[int]
            レスポンスにかかった時間(milliseconds)
        """
        # self.logger.debug(
        #     f"Request finished: name={name} exception={exception} time={response_time} worker={self.is_worker}")
        # TODO: バッチでメトリクスを送信する

    def on_test_stop(self, environment: Environment) -> None:
        """テストが終了した時に呼ばれる"""
        self.logger.info("CloudWatch metrics plugin has stopped")
        # TODO: 残ったメトリクスを送信する

    def on_spawning_complete(self, user_count: int) -> None:
        """ユーザーが生成された時に呼ばれる
        ワーカーは新しいユーザーが生成されたら、マスターは全てのユーザー生成が終わったら呼ばれる
        user_count : int
            生成した現在のユーザー数
        """
        self.logger.info(f"User spawning complete user_count={user_count}")

    def on_worker_report(self, **kwargs) -> None:
        self.logger.info(f"reporting: {dumps(kwargs)}")


@ events.init_command_line_parser.add_listener
def add_arguments(parser: LocustArgumentParser):
    """CloudWatch metrics を有効化するかどうかのフラグを追加"""
    parser.add_argument(
        "--cw-metrics",
        type=int,
        help="Enables CloudWatch metrics logging",
        env_var="LOCUST_CW_METRICS",
        default=0
    )


singletonInstance: Optional[CWMetricsPlugin] = None


@events.test_start.add_listener
def on_test_start(environment: Environment):
    """テスト開始時にインスタンスを生成する"""
    global singletonInstance
    if environment.parsed_options.cw_metrics == 1:
        singletonInstance = CWMetricsPlugin(env=environment)
