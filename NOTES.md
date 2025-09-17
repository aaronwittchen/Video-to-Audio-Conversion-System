Conversion Flow
When a user uploads a video for MP3 conversion, the request is first handled by the **API Gateway**. The Gateway stores the uploaded video in **MongoDB** and publishes a message to a **RabbitMQ** queue, notifying downstream services that a new video is available for processing.

The **Video-to-MP3 Converter Service** subscribes to this queue. Upon receiving a message, it extracts the video ID, retrieves the corresponding video file from MongoDB, performs the conversion to MP3 format, and stores the resulting MP3 file back into MongoDB. After successful conversion, it publishes a new message to the queue indicating that the process is complete.

The **Notification Service** listens for these completion messages. When it detects that a conversion has finished, it sends an email to the user with a unique download link or ID, notifying them that their MP3 file is ready.

To download the MP3, the client uses the unique ID provided in the notification along with their **JWT** to make an authenticated request to the **API Gateway**. Dowload request: `Authorization: Bearer <token>` The Gateway then retrieves the MP3 file from MongoDB and serves it to the client.

This architecture demonstrates how **RabbitMQ** enables decoupled communication between services and ensures scalability and reliability in the video conversion workflow.

get kubernetes command line tool
we're going to be deploying our services within a kubernetes cluster
on our local machine without having to actually have a kubernetes cluster deployed to like a
production environment
install minikube
This will allow us to run a **Kubernetes cluster locally**, enabling us to build and test a **microservice architecture** on our local machine without needing to deploy a Kubernetes cluster to a production environment.
We'll install **K9s**, a terminal-based UI that helps us manage and monitor our Kubernetes cluster more efficiently.

https://github.com/derailed/k9s

kubect
minikube start
k9s

Use **Flask** when:

- You want **simplicity** and **full control**.
- You're building a **small to medium** project or **API**.
- You prefer choosing your own tools (ORM, auth, etc.).
- You want a **lightweight** framework to build quickly.
  > Think: Microservices, APIs, MVPs, or learning projects.

Use **Django** when:

- You need a **full-featured** framework with everything built-in (auth, admin, ORM, etc.).
- You're building a **large** or **complex** web app (e.g., e-commerce, social platform).
- You want **rapid development** with convention over configuration.
- You need **admin panel**, **user management**, and **ORM** out of the box.
  > Think: Web apps with user accounts, dashboards, or data-heavy workflows.

![[Pasted image 20250805211048.png]]

secure mysql follow all of the best security practices when working with and installing a database server in a production environment

deploy to our cluster on our local environment and just quick note everything's going to be deployed on our

local environment in our mini Cube cluster we're not going to deploy anything to a server I might create

another tutorial on how to actually deploy this to a server or to a production like environment but for now

we're only focused on the actual architecture so everything's going to be done on our local system within this

mini Cube cluster

we're going to create the directory for our auth service so
we'll make their auth and this author is going to contain our auth service code so let's CD auth
and from here to start we're going to want to create a virtual environment
and we're going to write all of the code for the service in one file that we're going to call server.pi and the reason
we're doing this in one file is because it's going to be less than 700 lines of code and like I said before the service
is going to be relatively small it's just going to be a very simple auth service

flask is our server
so we'll go here and we're going to create a cursor by doing mysql.connection.cursor
and we're going to use that cursor to execute queries so we're going to say the result of the query is going to be
equal to cursor.execute and within this execute method we're going to put in our query
database then we should have a result so if result is greater than zero because results going to be an array of rows I
believe so if result is greater than zero then that means that we have at least one row with that username and in
this situation we should only have one row with that username because the username should be unique
and next we just want to check to see if the username and the password returned
in the row is equal to the credentials passed in the request and if that's not the case we'll say that the credential
is invalid and if it is the case then we're going to return a Json web token
