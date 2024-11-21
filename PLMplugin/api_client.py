import json
import http.client

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
        conn = http.client.HTTPConnection(self.host, port=self.port)

        try:
            headers = {
                'Content-Type': 'application/json'
            }

            json_payload = json.dumps(payload)
            print(f"Sending {method} to URL: {url}")
            print(f"Payload: {json_payload}")

            conn.request(method, url, body=json_payload, headers=headers)
            response = conn.getresponse()
            print(f"Response status: {response.status} {response.reason}")

            if response.status in [200, 201]:
                data = response.read()
                return data.decode("utf-8")
            else:
                print(f"Error response: {response.status} {response.reason}")
                return json.dumps({"error": f"HTTP {response.status}: {response.reason}"})

        except Exception as e:
            print(f"Exception in send_request_with_body: {str(e)}")
            return json.dumps({"error": str(e)})

        finally:
            conn.close()

    def send_post_request(self, url: str, payload: dict):
        return self._send_request_with_body("POST", url, payload)

    def send_patch_request(self, url: str, payload: dict):
        return self._send_request_with_body("PATCH", url, payload)

    def send_get_request(self, url_template: str, path_params: dict = None, query_params: dict = None):
        conn = http.client.HTTPConnection(self.host, port=self.port)

        try:
            full_url = self._build_url(url_template, path_params, query_params)
            print(f"Requesting URL: {full_url}")

            conn.request("GET", full_url)
            response = conn.getresponse()
            print(f"Response status: {response.status} {response.reason}")

            if response.status == 200:
                data = response.read()
                decode = data.decode("utf-8")
                print(decode)
                return decode
            else:
                print(f"Error response: {response.status} {response.reason}")
                return json.dumps({"error": f"HTTP {response.status}: {response.reason}"})

        except Exception as e:
            print(f"Exception in send_get_request: {str(e)}")
            return json.dumps({"error": str(e)})

        finally:
            conn.close()

    def _build_url(self, url_template: str, path_params: dict = None, query_params: dict = None) -> str:
        if path_params:
            full_url = url_template
            for key, value in path_params.items():
                full_url = full_url.replace(f"{{{key}}}", str(value))
        elif query_params:
            full_url = url_template + "?" + "&".join([f"{key}={value}" for key, value in query_params.items()])
        else:
            full_url = url_template
        return full_url