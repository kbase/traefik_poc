import requests
# import docker
import time
import pprint

# docker_base_url = 'unix://var/run/docker.sock'
# client = docker.DockerClient(base_url=docker_base_url)

traefik_metrics = "http://localhost:8080/metrics"

while True:
    r = requests.get(traefik_metrics)
    if r.status_code == 200:
        body = r.text.split("\n")
        service_conn = [line for line in body if "traefik_service_open_connections{" in line]
        service_websocket_open = [line for line in service_conn if "protocol=\"websocket\"" in line]
        pprint.pprint(service_websocket_open)
        time.sleep(30)
