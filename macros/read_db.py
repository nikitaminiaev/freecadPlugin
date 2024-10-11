import http.client
import json
import FreeCAD
import Part
from read_db import send_get_request, send_post_request

def send_get_request(url_template: str, path_params: dict = None, query_params: dict = None):
    conn = http.client.HTTPConnection("localhost", port=8000)
    
    if path_params is not None and len(query_params) > 0:
        for key, value in path_params.items():
            full_url = url_template.replace(f"{{{key}}}", str(value))
            print(full_url)
    elif query_params and len(query_params) > 0:
        full_url = url_template + "?" + "&".join([f"{key}={value}" for key, value in query_params.items()])
    else:
        full_url = url_template

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

def get_part_from_db(part_name):
    response = send_get_request("/part", {"name": part_name})
    part_data = json.loads(response)
    # Преобразуйте part_data в объект FreeCAD
    # Например, если part_data содержит координаты точек:
    shape = Part.makePolygon([(p['x'], p['y'], p['z']) for p in part_data['points']])
    return shape

def save_part_to_db(part_name, shape):
    # Преобразуйте объект FreeCAD в формат, понятный вашему API
    part_data = {
        "name": part_name,
        "points": [{"x": p.X, "y": p.Y, "z": p.Z} for p in shape.Vertexes]
    }
    send_post_request("/part", json.dumps(part_data))

#res = send_get_request("/all_parts", {"name": "ramka"})
# res = send_post_request("/part/", "raddddddd")
# print(res)

# Пример использования
send_get_request("/api/basic_object", query_params={"id":"e9723ab7-7808-47fc-9b39-e665949dc2e7"})
# doc = FreeCAD.newDocument()
# Part.show(shape)

# Сохранение изменённой детали
# modified_shape = doc.ActiveObject.Shape
# save_part_to_db("modified_example_part", modified_shape)