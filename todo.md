Immediate tasks

- Verify `AUTH_SVC_ADDRESS` is set for all runtime environments
- Confirm RabbitMQ queues exist: `video`, `mp3`
- Smoke test gateway endpoints: `/login`, `/upload`, `/download`
- Run converter and notification workers against real queues
- Validate MongoDB writes and reads via GridFS (videos, mp3s)
- Configure Prometheus scrape for gateway `/metrics` and workers (METRICS_PORT)
- Import basic Grafana dashboards and wire Prometheus datasource

Operational checklists

- Logs: tail gateway, converter, notification processes during e2e test
- Failure modes: simulate auth down and verify gateway errors are clear
- Scaling: increase converter replicas and verify work distribution

Deferred

- Add basic rate limiting at the gateway
- Add request/response metrics and dashboards
- Grafana & prometheus , Helm charts for Kubernetes.
- testing

- Add Support for other file types for both video and audio
