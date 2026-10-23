from locust import HttpUser, task, between


class DataFlowUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def summary(self):
        self.client.get("/api/summary")

    @task
    def orders(self):
        self.client.get("/api/orders?page=1&page_size=10")
