from locust import HttpUser, task
from time import sleep
from cw_metrics_plugin import load_cw_metrics_plugin

load_cw_metrics_plugin()


class HelloWorldUser(HttpUser):
    @task
    def hello_world(self):
        self.client.get("/hello.html")
        sleep(1.0)
        self.client.get("/world.html")
        sleep(1.0)

    @task
    def error404(self):
        self.client.get("/not_exists.html")
