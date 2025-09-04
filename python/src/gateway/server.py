import os, gridfs, pika, json, time
from flask import Flask, request, send_file, Response
from flask_pymongo import PyMongo
from auth import validate
from authclient import access
from storage import util
from bson.objectid import ObjectId
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

server = Flask(__name__)

mongo_video = PyMongo(server, uri="mongodb://host.minikube.internal:27017/videos")

mongo_mp3 = PyMongo(server, uri="mongodb://host.minikube.internal:27017/mp3s")

fs_videos = gridfs.GridFS(mongo_video.db)
fs_mp3s = gridfs.GridFS(mongo_mp3.db)

connection = pika.BlockingConnection(pika.ConnectionParameters("rabbitmq"))
channel = connection.channel()

# Prometheus metrics
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"]
)
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "Request latency",
    ["method", "path"]
)


@server.before_request
def _metrics_before():
    request._start_time = time.time()


@server.after_request
def _metrics_after(response):
    path = request.path
    method = request.method
    status = str(response.status_code)
    REQUEST_COUNT.labels(method=method, path=path, status=status).inc()
    if hasattr(request, "_start_time"):
        REQUEST_LATENCY.labels(method=method, path=path).observe(time.time() - request._start_time)
    return response


@server.route("/metrics")
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


@server.route("/login", methods=["POST"])
def login():
    token, err = access.login(request)

    if not err:
        return token
    else:
        return err


@server.route("/upload", methods=["POST"])
def upload():
    access_data, err = validate.token(request)

    if err:
        return err

    access_data = json.loads(access_data)

    if access_data["admin"]:
        if len(request.files) > 1 or len(request.files) < 1:
            return "exactly 1 file required", 400

        for _, f in request.files.items():
            err = util.upload(f, fs_videos, channel, access_data)

            if err:
                return err

        return "success!", 200
    else:
        return "not authorized", 401


@server.route("/download", methods=["GET"])
def download():
    access_data, err = validate.token(request)

    if err:
        return err

    access_data = json.loads(access_data)

    if access_data["admin"]:
        fid_string = request.args.get("fid")

        if not fid_string:
            return "fid is required", 400

        try:
            out = fs_mp3s.get(ObjectId(fid_string))
            return send_file(out, download_name=f"{fid_string}.mp3")
        except Exception as err:
            print(err)
            return "internal server error", 500

    return "not authorized", 401


if __name__ == "__main__":
    server.run(host="0.0.0.0", port=8080)