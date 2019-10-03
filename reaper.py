import requests
import docker
import time
import pprint
import re
import pdb

docker_base_url = 'unix://var/run/docker.sock'
client = docker.DockerClient(base_url=docker_base_url)

traefik_metrics = "http://localhost:8080/metrics"
narr_img = "kbase/narrative:latest"

# 5 minute timeout for inactive containers
timeout_secs = 300

narr_activity = dict()

while True:
    r = requests.get(traefik_metrics)
    if r.status_code == 200:
        body = r.text.split("\n")
        service_conn = [line for line in body if "traefik_service_open_connections{" in line]
        service_websocket_open = [line for line in service_conn if "protocol=\"websocket\"" in line]
        pprint.pprint(service_websocket_open)
        containers = dict()
        for line in service_websocket_open:
            matches = re.search(r"service=\"(\w+).+ (\d+)", line)
            containers[matches.group(1)] = int(matches.group(2))
        pprint.pprint(containers)
        now = time.time()
        for name in containers.keys():
            try:
                svc_container = client.containers.get(name)
            except docker.errors.NotFound:
                print("Service {} not found (might be part of core stack)".format(name))
                continue
            if (narr_img in svc_container.image.attrs["RepoTags"]):
                # only update timestamp if the container has active websockets or this is the first
                # time we've seen it
                if (containers[name] > 0) or (name not in containers):
                    narr_activity[name] = now
                # pdb.set_trace()
                msg = "Container {} has {} websocket connections at {}".format(name, containers[name], time.ctime(now))
                print(msg)
        # pdb.set_trace()
        for name, timestamp in narr_activity.items():
            print("{} last activity {}".format(name, time.ctime(timestamp)))
            if (now - timestamp) > timeout_secs:
                msg = "Container {} has been inactive longer than {}. Reaping.".format(name, timeout_secs)
                print(msg)
                try:
                    killit = client.containers.get(name)
                    killit.stop()
                except docker.errors.NotFound:
                    print("Container not found - may have been reaped already")
        time.sleep(30)
