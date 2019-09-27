import flask
import requests
import docker

base_url = 'unix://var/run/docker.sock'
client = docker.DockerClient(base_url=base_url)
print("Starting up authentication/spawner service")
reload_msg = """
<html>
<head>
<META HTTP-EQUIV="refresh" CONTENT="2">
</head>
<body>
Starting container - will reload in 2 seconds
</body>
</html>
"""
app = flask.Flask(__name__)


@app.route('/')
def hello():
    # resp = flask.Response("Bad auth response",status=404)
    if 'kbase_session' in flask.request.cookies:
        print("Got a request with cookie ", flask.request.cookies['kbase_session'])
        token = flask.request.cookies['kbase_session']
        r = requests.get("https://kbase.us/services/auth/api/V2/token", headers={'Authorization': token})
        authresponse = r.json()
        if r.status_code == 200:
            username = authresponse['user']
            resp = flask.Response(reload_msg, status=200)
            print("Starting container for user " + username)
            cookie = "kbase_session=" + flask.request.cookies['kbase_session']
            labels = dict()
            labels["traefik.enable"] = "True"
            labels["traefik.http.routers." + username + ".rule"] = "Host(\"localhost\") && HeadersRegexp(\"Cookie\",\""+cookie+"\")"
            labels["traefik.http.routers." + username + ".entrypoints"] = "web"
            container = client.containers.run('containous/whoami', detach=True, labels=labels, hostname=username,
                                              auto_remove=True, name=username, network="traefik_poc_default")
            print(container.logs())
        else:
            msg = authresponse['error']['message']
            resp = flask.Response(msg + "\n", status=r.status_code)
    else:
        print("Got a request without kbase_session cookie ")
        if 'backdoor' in flask.request.headers:
            print("Got backdoor header")
            resp = flask.Response("Ok", status=200)
            resp.headers['X-Forwarded-User'] = flask.request.headers['backdoor']
        else:
            resp = flask.Response("No cookie\n", status=401)
    return resp


if __name__ == '__main__':
    app.run()
