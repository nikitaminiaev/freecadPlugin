import http.client
import json
import Part
from read_db import send_get_request

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

# res = send_get_request("/api/basic_object/{id}", query_params={"name":"detal"})
res = send_get_request("/api/basic_object/{id}", path_params={"id":"e9723ab7-7808-47fc-9b39-e665949dc2e7"})
print(json.loads(res))
data = json.loads(res)

# Извлечение значения ключа path
file_path = data['bounding_contour']['brep_files']['path']
print(file_path)

import FreeCAD
FreeCAD.open(file_path)

#res = send_get_request("/all_parts", {"name": "ramka"})
# res = send_post_request("/part/", "raddddddd")
# print(res)
# Пример использования
# doc = FreeCAD.newDocument()
# Part.show(shape)
# Сохранение изменённой детали
# modified_shape = doc.ActiveObject.Shape
# save_part_to_db("modified_example_part", modified_shape)

