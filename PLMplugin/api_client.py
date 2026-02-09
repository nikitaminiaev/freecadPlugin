import json
import http.client
import urllib.parse
import time
from utils.logger import log

class APIClient:
    def __init__(self, host="localhost", port=8000):
        self.host = host
        self.port = port

    def _send_request_with_body(self, method: str, url: str, payload: dict):
        """Send request with JSON body to the API

        Args:
            method: HTTP method ("POST", "PATCH", etc)
            url: Request URL
            payload: Dictionary to be sent as JSON payload
        """
        start_time = time.time()
        conn = http.client.HTTPConnection(self.host, port=self.port)

        try:
            headers = {
                'Content-Type': 'application/json'
            }

            json_payload = json.dumps(payload)

            conn.request(method, url, body=json_payload, headers=headers)
            response = conn.getresponse()
            log(f"Response status: {response.status} {response.reason}")

            if response.status in [200, 201]:
                data = response.read()
                return data.decode("utf-8")
            else:
                log(f"Error response: {response.status} {response.reason}")
                return json.dumps({"error": f"HTTP {response.status}: {response.reason}"})

        except Exception as e:
            log(f"Exception in send_request_with_body: {str(e)}")
            return json.dumps({"error": str(e)})

        finally:
            conn.close()
            end_time = time.time()
            log(f"Total db time: {end_time - start_time:.2f} seconds")

    def send_post_request(self, url_template: str, payload: dict, path_params: dict | None = None, query_params: dict | None = None):
        full_url = self._build_url(url_template, path_params, query_params)
        return self._send_request_with_body("POST", full_url, payload)

    def send_patch_request(self, url_template: str, payload: dict, path_params: dict | None = None, query_params: dict | None = None):
        full_url = self._build_url(url_template, path_params, query_params)
        return self._send_request_with_body("PATCH", full_url, payload)

    def send_get_request(self, url_template: str, path_params: dict | None = None, query_params: dict | None = None):
        start_time = time.time()
        
        conn = http.client.HTTPConnection(self.host, port=self.port)

        try:
            full_url = self._build_url(url_template, path_params, query_params)
            log(f"Requesting URL: {full_url}")

            conn.request("GET", full_url)
            response = conn.getresponse()
            log(f"Response status: {response.status} {response.reason}")

            if response.status == 200:
                data = response.read()
                decode = data.decode("utf-8")
                return decode
            else:
                log(f"Error response: {response.status} {response.reason}")
                return json.dumps({"error": f"HTTP {response.status}: {response.reason}"})

        except Exception as e:
            log(f"Exception in send_get_request: {str(e)}")
            return json.dumps({"error": str(e)})

        finally:
            conn.close()
            end_time = time.time()
            log(f"Total db time: {end_time - start_time:.2f} seconds")

    def _build_url(self, url_template: str, path_params: dict | None = None, query_params: dict | None = None) -> str:
        full_url = url_template
        if path_params:
            for key, value in path_params.items():
                full_url = full_url.replace(f"{{{key}}}", urllib.parse.quote(str(value)))
        
        if query_params:
            query_string = urllib.parse.urlencode(query_params)
            full_url = f"{full_url}?{query_string}" if "?" not in full_url else f"{full_url}&{query_string}"
            
        return full_url