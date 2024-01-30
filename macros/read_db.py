import http.client
import json

def send_get_request(url: str, query_params: dict = None):
    conn = http.client.HTTPConnection("localhost", port=8000)
    if query_params:
        full_url = url + "?" + "&".join([f"{key}={value}" for key, value in query_params.items()])
    else:
        full_url = url
    print(full_url)
    conn.request("GET", full_url)
    response = conn.getresponse()
    print(response.status, response.reason)
    data = response.read()
    conn.close()
    return data.decode("utf-8")

def send_post_request(url: str, name: str):
    conn = http.client.HTTPConnection("localhost", port=8000)
    params = json.dumps({"name": name})
    headers = {'Content-type': 'application/json'}
    conn.request("POST", url, params, headers)
    response = conn.getresponse()
    print(response.status, response.reason)
    conn.close()

#res = send_get_request("/all_parts", {"name": "ramka"})
res = send_post_request("/part/", "raddddddd")
print(res)