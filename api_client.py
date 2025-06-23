import requests
from config import Config

class ApiClient:
    def __init__(self):
        self.base_api_url = Config.BASE_API_URL
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
        if not self.token:
            raise Exception("API client is not authenticated. Please authenticate first.")
        
        url = f"{self.base_api_url}/api/planning/courses"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}"
        }
        resp = requests.post(url, json=course_data, headers=headers)
        resp.raise_for_status()
        return resp.json()

    def patch_user_pass_id(self, user_id: int, pass_id: int):
        if not self.token:
            raise Exception("API client is not authenticated. Please authenticate first.")
        
        url = f"{self.base_api_url}/api/planning/users/{user_id}/passid"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}"
        }

        data = {"pass_id": int(pass_id)}
        resp = requests.patch(url, json=data, headers=headers)
        resp.raise_for_status()
        return resp.json()

    def get_all_users(self):
        if not self.token:
            raise Exception("API client is not authenticated. Please authenticate first.")

        url = f"{self.base_api_url}/api/planning/users"
        headers = {
            "Authorization": f"Bearer {self.token}"
        }
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        return resp.json()
