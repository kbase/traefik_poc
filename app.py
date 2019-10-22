import flask
import requests
import docker
import hashlib

base_url = 'unix://var/run/docker.sock'
client = docker.DockerClient(base_url=base_url)
print("Starting up authentication/spawner service")
reload_msg = """
<html>
<head>
<META HTTP-EQUIV="refresh" CONTENT="5;URL='/narrative/{}'">
</head>
<body>
Starting container - will reload in 5 seconds
</body>
</html>
"""
app = flask.Flask(__name__)


@app.route('/narrative/<path:narrative>')
def hello(narrative):
    # resp = flask.Response("Bad auth response",status=404)
    if 'kbase_session' in flask.request.cookies:
        print("Got a request with cookie ", flask.request.cookies['kbase_session'])
        token = flask.request.cookies['kbase_session']
        r = requests.get("https://ci.kbase.us/services/auth/api/V2/token", headers={'Authorization': token})
        authresponse = r.json()
        if r.status_code == 200:
            username = authresponse['user']
            resp = flask.Response(reload_msg.format(narrative), status=200)
            print("Starting container for user " + username)
            hashFunc = hashlib.md5()
            hashFunc.update(token)
            hashFunc.update(flask.request.remote_addr)
            session = hashFunc.hexdigest()
            cookie = "narrative_session=" + session
            print("Routing based on " + cookie)
            resp.set_cookie('narrative_session', session)
            labels=dict()
            labels["traefik.enable"] = "True"
            labels["traefik.http.routers." + username + ".rule"] = "Host(\"localhost\") && PathPrefix(\"/narrative\") && HeadersRegexp(\"Cookie\",\""+cookie+"\")"
            labels["traefik.http.routers." + username + ".entrypoints"] = "web"
#            container = client.containers.run('containous/whoami', detach=True, labels=labels, hostname=username,
#                                              auto_remove=True, name=username, network="traefik_poc_default")
            container = client.containers.run('kbase/narrative', detach=True, labels=labels, hostname=username,
                                              auto_remove=True, name=username, network="traefik_poc_default")
            print(container.logs())
        else:
            msg = authresponse['error']['message']
            resp = flask.Response(msg + "\n", status=r.status_code)
    else:
        print("Got a request without kbase_session cookie ")
        resp = flask.Response("No cookie: requires kbase_session cookie from ci environment\n", status=401)
    return resp


if __name__ == '__main__':
    app.run()
