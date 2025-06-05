import os
import requests

class ApiClient:
    def __init__(self, env="dev"):
        if env == "prod":
            self.base_api_url = os.getenv("PROD_API_URL", "https://transat.destimt.fr")
        else:
            self.base_api_url = os.getenv("DEV_API_URL", "http://host.docker.internal:3000")
        self.token = None

    def authenticate(self, email, password):
        url = f"{self.base_api_url}/api/auth/login"
        headers = {"Content-Type": "application/json"}
        resp = requests.post(url, json={"email": email, "password": password}, headers=headers)
        resp.raise_for_status()

        data = resp.json()
        self.token = data.get("token")
        if not self.token:
            raise Exception(f"No token found in API response: {data}")
        return self.token

    def post_course(self, course_data):
        url = f"{self.base_api_url}/api/planning/courses"
        headers = {"Authorization": f"Bearer {self.token}"}
        resp = requests.post(url, json=course_data, headers=headers)
        resp.raise_for_status()
        return resp.json()
