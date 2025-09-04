import pika, sys, os, time
from send import email
from prometheus_client import Counter, Histogram, start_http_server

JOBS_TOTAL = Counter("notification_jobs_total", "Jobs processed", ["result"])
JOB_DURATION = Histogram("notification_job_duration_seconds", "Job processing time")


def main():
    start_http_server(int(os.environ.get("METRICS_PORT", "9100")))
    # rabbitmq connection
    connection = pika.BlockingConnection(pika.ConnectionParameters(host="rabbitmq"))
    channel = connection.channel()

    def callback(ch, method, properties, body):
        start = time.time()
        err = email.notification(body)
        duration = time.time() - start
        JOB_DURATION.observe(duration)
        if err:
            JOBS_TOTAL.labels(result="error").inc()
            ch.basic_nack(delivery_tag=method.delivery_tag)
        else:
            JOBS_TOTAL.labels(result="success").inc()
            ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_consume(
        queue=os.environ.get("MP3_QUEUE"), on_message_callback=callback
    )

    print("Waiting for messages. To exit press CTRL+C")

    channel.start_consuming()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Interrupted")
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
