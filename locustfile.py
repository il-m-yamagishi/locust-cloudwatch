from locust import HttpUser, task
from time import sleep
from locust_cloudwatch import CWMetricsPlugin


class HelloWorldUser(HttpUser):
    @task
    def hello_world(self):
        self.client.get("/hello.html")
        sleep(1.0)
        self.client.get("/world.html")
        sleep(1.0)
