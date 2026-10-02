# Kubernetes — Comprehensive, Explainable Guide

> A practical guide to Kubernetes for backend, platform, and AI engineers. Covers what Kubernetes is, how it works, the core objects you must know, common deployment patterns, debugging, security, and interview-ready mental models.

---

## Table of Contents

1. [What Kubernetes Actually Is](#1-what-kubernetes-actually-is)
2. [Why Teams Use Kubernetes](#2-why-teams-use-kubernetes)
3. [The Mental Model](#3-the-mental-model)
4. [Cluster Architecture](#4-cluster-architecture)
5. [Core Kubernetes Objects](#5-core-kubernetes-objects)
6. [Pods — The Smallest Deployable Unit](#6-pods--the-smallest-deployable-unit)
7. [Deployments, ReplicaSets, and Rollouts](#7-deployments-replicasets-and-rollouts)
8. [Services and Networking](#8-services-and-networking)
9. [Ingress and API Traffic](#9-ingress-and-api-traffic)
10. [ConfigMaps and Secrets](#10-configmaps-and-secrets)
11. [Storage — Volumes, PV, PVC, StorageClass](#11-storage--volumes-pv-pvc-storageclass)
12. [Workload Types — Deployment vs StatefulSet vs DaemonSet vs Job](#12-workload-types--deployment-vs-statefulset-vs-daemonset-vs-job)
13. [Scheduling, Requests, Limits, and Autoscaling](#13-scheduling-requests-limits-and-autoscaling)
14. [Health Checks and Self-Healing](#14-health-checks-and-self-healing)
15. [Namespaces, RBAC, and Security](#15-namespaces-rbac-and-security)
16. [Observability and Debugging](#16-observability-and-debugging)
17. [Helm, Kustomize, and GitOps](#17-helm-kustomize-and-gitops)
18. [A Full Example Application](#18-a-full-example-application)
19. [Common Commands Cheat Sheet](#19-common-commands-cheat-sheet)
20. [Common Anti-Patterns](#20-common-anti-patterns)
21. [When Kubernetes Is the Right Choice](#21-when-kubernetes-is-the-right-choice)
22. [Interview Talking Points](#22-interview-talking-points)

---

## 1. What Kubernetes Actually Is

Kubernetes is a **container orchestration platform**.

That means:

- you package your application as containers
- Kubernetes decides where they should run
- Kubernetes keeps them running
- Kubernetes replaces failed containers
- Kubernetes scales them up and down
- Kubernetes exposes them over the network
- Kubernetes helps manage config, secrets, storage, and deployments

The shortest correct definition:

> Kubernetes is a system for running and managing containerized applications across a cluster of machines.

It is often abbreviated as:

- `Kubernetes`
- `K8s`

Why `K8s`?

- there are 8 letters between `K` and `s`

---

## 2. Why Teams Use Kubernetes

Without Kubernetes, teams often end up manually solving:

- how to run many containers across many servers
- how to recover when a container crashes
- how to deploy a new version safely
- how to scale services during peak traffic
- how to route traffic to the right application
- how to give apps config, secrets, and storage

Kubernetes gives standard answers to those problems.

Typical reasons teams choose it:

1. **Standardization**: one deployment model for many services
2. **Portability**: same concepts across cloud and on-prem
3. **Self-healing**: failed workloads are restarted automatically
4. **Scaling**: both manual and automatic scaling
5. **Rolling deployments**: ship new versions without stopping the whole app
6. **Ecosystem**: Helm, Argo CD, Prometheus, Istio, cert-manager, operators

---

## 3. The Mental Model

The easiest way to understand Kubernetes:

- **You declare the desired state**
- **Kubernetes continuously tries to make reality match that desired state**

Example:

You say:

- "I want 3 copies of my API running"
- "I want them exposed internally on port 80"
- "I want them restarted if they crash"

Kubernetes keeps checking:

- Are 3 copies actually running?
- If not, create more
- If one dies, replace it
- If traffic needs routing, keep service discovery updated

This is called a **declarative model**.

You tell Kubernetes **what you want**, not every step of **how to do it**.

---

## 4. Cluster Architecture

A Kubernetes cluster has two big parts:

- **Control plane**
- **Worker nodes**

### 4.1 Control plane

The control plane is the brain of the cluster.

Its job is to:

- store cluster state
- make scheduling decisions
- detect differences between desired and actual state
- trigger corrective actions

Main control plane components:

- `kube-apiserver`: the front door for the cluster; all commands go through it
- `etcd`: the database that stores cluster state
- `kube-scheduler`: decides which node should run a Pod
- `kube-controller-manager`: runs controllers that enforce desired state
- `cloud-controller-manager`: integrates with cloud providers

### 4.2 Worker nodes

Worker nodes are the machines that actually run your application containers.

Each worker node typically has:

- `kubelet`: agent that talks to the control plane
- `container runtime`: runs containers, such as `containerd`
- `kube-proxy`: helps implement service networking

### 4.3 Architecture diagram

```text
kubectl
  |
  v
API Server
  |
  +--> etcd
  +--> Scheduler
  +--> Controllers
  |
  v
Worker Nodes
  +--> kubelet
  +--> container runtime
  +--> kube-proxy
  +--> Pods
```

---

## 5. Core Kubernetes Objects

These are the objects you must know first:

- `Pod`
- `Deployment`
- `ReplicaSet`
- `Service`
- `Ingress`
- `ConfigMap`
- `Secret`
- `PersistentVolume` (`PV`)
- `PersistentVolumeClaim` (`PVC`)
- `Namespace`

Second-wave objects:

- `StatefulSet`
- `DaemonSet`
- `Job`
- `CronJob`
- `HorizontalPodAutoscaler` (`HPA`)
- `NetworkPolicy`

Very simple mapping:

| Need | Object |
|---|---|
| Run a container | Pod |
| Keep many copies running | Deployment |
| Give Pods a stable network identity | Service |
| Expose HTTP from outside the cluster | Ingress |
| Store config | ConfigMap |
| Store sensitive values | Secret |
| Persist data | PVC |

---

## 6. Pods — The Smallest Deployable Unit

A **Pod** is the smallest deployable unit in Kubernetes.

A Pod usually contains:

- one main application container
- optionally sidecar containers

Containers inside the same Pod:

- share the same network namespace
- can talk over `localhost`
- can share volumes

Important point:

> Kubernetes schedules Pods, not individual containers.

### 6.1 Why Pods exist

Pods group containers that belong together.

Example:

- one app container
- one logging or proxy sidecar

### 6.2 Pod example

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: simple-api
spec:
  containers:
    - name: api
      image: nginx:stable
      ports:
        - containerPort: 80
```

### 6.3 Important Pod reality

Pods are **ephemeral**.

That means:

- they can die
- they can be recreated
- they should not be treated like permanent pets

Think of Pods as:

- disposable runtime instances

Not as:

- individually managed servers

---

## 7. Deployments, ReplicaSets, and Rollouts

You almost never manage standalone Pods directly in production.

Instead you use a **Deployment**.

### 7.1 Deployment

A Deployment says:

- which container image to run
- how many replicas you want
- how to update them

Example:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: backend-api
  template:
    metadata:
      labels:
        app: backend-api
    spec:
      containers:
        - name: api
          image: myorg/backend-api:1.0.0
          ports:
            - containerPort: 8000
```

### 7.2 ReplicaSet

A ReplicaSet is the lower-level object that ensures the right number of Pod replicas exist.

In practice:

- Deployment manages ReplicaSet
- ReplicaSet manages Pods

You usually interact with:

- Deployment

Not directly with:

- ReplicaSet

### 7.3 Rolling updates

When you update the image version in a Deployment:

- Kubernetes gradually creates new Pods
- then removes old Pods

This enables:

- rolling deployment
- minimal downtime
- rollback support

Useful commands:

```bash
kubectl rollout status deployment/backend-api
kubectl rollout history deployment/backend-api
kubectl rollout undo deployment/backend-api
```

---

## 8. Services and Networking

Pods are ephemeral, so their IP addresses can change.

That creates a problem:

- how do other services reliably find them?

The answer is a **Service**.

### 8.1 What a Service does

A Service gives a stable network identity to a group of Pods.

It uses labels to select which Pods belong to it.

### 8.2 Service example

```yaml
apiVersion: v1
kind: Service
metadata:
  name: backend-api
spec:
  selector:
    app: backend-api
  ports:
    - port: 80
      targetPort: 8000
```

This means:

- Service listens on port `80`
- traffic is forwarded to Pod container port `8000`

### 8.3 Service types

#### ClusterIP

Default type.

Use when:

- the service is only needed inside the cluster

#### NodePort

Exposes the service on a port on each node.

Use when:

- mostly for testing or simple setups

#### LoadBalancer

Creates a cloud load balancer in providers like AWS, GCP, or Azure.

Use when:

- you want external access without an Ingress setup

### 8.4 Labels and selectors

Services work because of labels.

Example:

```yaml
metadata:
  labels:
    app: backend-api
```

Then the Service says:

```yaml
selector:
  app: backend-api
```

This label model is fundamental in Kubernetes.

---

## 9. Ingress and API Traffic

A Service exposes an app at the Kubernetes networking layer.

An **Ingress** helps manage external HTTP and HTTPS traffic.

Use Ingress when you want:

- host-based routing
- path-based routing
- TLS termination
- one entry point for many services

### 9.1 Example

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: backend-ingress
spec:
  rules:
    - host: api.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: backend-api
                port:
                  number: 80
```

### 9.2 Important nuance

Ingress is just the resource definition.

You also need an **Ingress controller**, such as:

- NGINX Ingress Controller
- AWS Load Balancer Controller
- Traefik

Without a controller:

- the Ingress object does nothing useful

---

## 10. ConfigMaps and Secrets

Applications need configuration.

Examples:

- environment name
- feature flags
- database URL
- API keys

Kubernetes separates config from code.

### 10.1 ConfigMap

Use ConfigMap for non-sensitive configuration.

Example:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: backend-config
data:
  APP_ENV: production
  LOG_LEVEL: info
```

Inject into a Pod:

```yaml
envFrom:
  - configMapRef:
      name: backend-config
```

### 10.2 Secret

Use Secret for sensitive data.

Example:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: backend-secrets
type: Opaque
stringData:
  DATABASE_URL: postgres://user:password@db:5432/app
  API_KEY: super-secret-key
```

Important nuance:

- Kubernetes Secrets are not magically secure by default
- they are base64-encoded, not strongly encrypted by default

Best practice:

- enable encryption at rest
- restrict RBAC access
- consider external secret managers

---

## 11. Storage — Volumes, PV, PVC, StorageClass

Containers are ephemeral.

If the container filesystem disappears, where does data live?

Kubernetes solves this with volumes and persistent storage objects.

### 11.1 Volume

A Pod volume is mounted into one or more containers in the Pod.

Example use cases:

- temporary scratch space
- persistent storage
- config files

### 11.2 PersistentVolume (PV)

A PV is a storage resource in the cluster.

Think of it as:

- actual storage capacity

### 11.3 PersistentVolumeClaim (PVC)

A PVC is a request for storage by an application.

Think of it as:

- "I need 20Gi of persistent storage"

### 11.4 StorageClass

A StorageClass defines how storage should be provisioned.

Example:

- standard SSD storage
- high-IOPS storage

### 11.5 PVC example

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: app-data
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
```

Mount into a Pod:

```yaml
volumes:
  - name: app-storage
    persistentVolumeClaim:
      claimName: app-data

containers:
  - name: app
    image: myorg/app:1.0
    volumeMounts:
      - name: app-storage
        mountPath: /data
```

### 11.6 Key storage idea

Use persistent storage for:

- databases
- queues with disk state
- uploaded files

Do not rely on the container filesystem for important data.

---

## 12. Workload Types — Deployment vs StatefulSet vs DaemonSet vs Job

This is a common interview topic.

### 12.1 Deployment

Use for:

- stateless applications
- APIs
- web apps
- workers without stable identity

### 12.2 StatefulSet

Use for:

- stateful applications
- databases
- systems where each Pod needs stable identity or storage

StatefulSet provides:

- stable Pod names
- stable storage association
- ordered startup and shutdown

Example:

- `postgres-0`, `postgres-1`, `postgres-2`

### 12.3 DaemonSet

Use for:

- one Pod on every node

Common examples:

- log collectors
- monitoring agents
- security agents

### 12.4 Job

Use for:

- run-to-completion tasks

Examples:

- migration script
- data backfill
- report generation

### 12.5 CronJob

Use for:

- scheduled Jobs

Examples:

- nightly cleanup
- hourly sync

### 12.6 Easy decision table

| Workload | Best object |
|---|---|
| API or web service | Deployment |
| PostgreSQL or Kafka broker | StatefulSet |
| Node-level agent | DaemonSet |
| One-time batch task | Job |
| Scheduled batch task | CronJob |

---

## 13. Scheduling, Requests, Limits, and Autoscaling

Kubernetes must decide where Pods run.

That is scheduling.

### 13.1 Requests and limits

Every container can declare:

- CPU request
- memory request
- CPU limit
- memory limit

Example:

```yaml
resources:
  requests:
    cpu: "250m"
    memory: "256Mi"
  limits:
    cpu: "500m"
    memory: "512Mi"
```

Meaning:

- request = minimum guaranteed scheduling amount
- limit = maximum allowed amount

### 13.2 Why this matters

Without requests and limits:

- the scheduler cannot make good placement decisions
- noisy-neighbor problems get worse
- memory issues become harder to control

### 13.3 What happens if a container exceeds memory limit

Usually:

- it gets killed with OOM

### 13.4 Horizontal Pod Autoscaler (HPA)

HPA automatically changes replica count based on metrics.

Common basis:

- CPU
- memory
- custom metrics

Example:

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: backend-api
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: backend-api
  minReplicas: 2
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 60
```

### 13.5 Cluster autoscaling

If Pods cannot fit on existing nodes:

- a cluster autoscaler can add more nodes

This is different from HPA:

- HPA scales Pods
- cluster autoscaler scales nodes

---

## 14. Health Checks and Self-Healing

Kubernetes can only heal workloads if it knows their health.

That is where probes come in.

### 14.1 Liveness probe

Answers:

- "Should this container be restarted?"

Use when:

- the process may deadlock or get stuck

### 14.2 Readiness probe

Answers:

- "Is this container ready to receive traffic?"

If readiness fails:

- the Pod stays running
- but traffic is not sent to it

### 14.3 Startup probe

Answers:

- "Should Kubernetes wait longer before assuming this app is broken?"

Useful for:

- slow-starting apps

### 14.4 Example

```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /ready
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 5
```

Best practice:

- make `/health` mean "process alive"
- make `/ready` mean "can serve real traffic"

---

## 15. Namespaces, RBAC, and Security

### 15.1 Namespace

A Namespace is a logical partition inside a cluster.

Use it to separate:

- teams
- environments
- applications

Examples:

- `dev`
- `staging`
- `prod`
- `ml-platform`

### 15.2 RBAC

RBAC stands for:

- Role-Based Access Control

It controls:

- who can do what in the cluster

Core RBAC objects:

- `Role`
- `ClusterRole`
- `RoleBinding`
- `ClusterRoleBinding`

Simple rule:

- `Role` is namespace-scoped
- `ClusterRole` is cluster-wide

### 15.3 ServiceAccount

Applications running in Pods use ServiceAccounts to authenticate to the Kubernetes API and cloud integrations.

Best practice:

- create dedicated ServiceAccounts for apps
- avoid broad permissions

### 15.4 NetworkPolicy

By default, many clusters are fairly open internally.

NetworkPolicy lets you restrict traffic between Pods.

Use it for:

- zero-trust style internal networking
- limiting blast radius

### 15.5 Pod security mindset

Good defaults:

- do not run as root
- use read-only root filesystem where possible
- drop unnecessary Linux capabilities
- avoid privileged containers
- pin image versions
- scan images for vulnerabilities

---

## 16. Observability and Debugging

Kubernetes adds abstraction, which makes observability more important.

You need:

- logs
- metrics
- traces
- events

### 16.1 What to look at first when something fails

1. `kubectl get pods`
2. `kubectl describe pod <name>`
3. `kubectl logs <pod>`
4. `kubectl get events`

### 16.2 Common Pod states

- `Pending`: not yet scheduled or waiting on resources
- `Running`: active
- `CrashLoopBackOff`: starts, crashes, retries repeatedly
- `ImagePullBackOff`: cannot pull the container image
- `Completed`: finished Job

### 16.3 Useful debugging commands

```bash
kubectl get pods -A
kubectl describe pod my-pod
kubectl logs my-pod
kubectl logs my-pod -c sidecar-name
kubectl exec -it my-pod -- sh
kubectl get events --sort-by=.metadata.creationTimestamp
```

### 16.4 What `describe` is great for

`kubectl describe` helps reveal:

- scheduling failures
- image pull errors
- failed probes
- mount issues
- recent events

---

## 17. Helm, Kustomize, and GitOps

Raw YAML works, but real systems need reusable deployment workflows.

### 17.1 Helm

Helm is the package manager for Kubernetes.

Use it for:

- reusable charts
- parameterized values
- third-party installs

Think of Helm as:

- templates + values + release management

### 17.2 Kustomize

Kustomize lets you customize base YAML for different environments.

Use it for:

- overlays
- environment-specific patches

Think of Kustomize as:

- patching and composing manifests without a full templating language

### 17.3 GitOps

GitOps means:

- Git is the source of truth for desired cluster state
- a controller applies and reconciles changes automatically

Popular tools:

- Argo CD
- Flux

Why teams like GitOps:

- auditable deployments
- safer rollbacks
- consistent environments

---

## 18. A Full Example Application

This example includes:

- a Deployment
- a Service
- a ConfigMap

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: api-config
data:
  APP_ENV: production
  LOG_LEVEL: info
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: simple-api
spec:
  replicas: 2
  selector:
    matchLabels:
      app: simple-api
  template:
    metadata:
      labels:
        app: simple-api
    spec:
      containers:
        - name: api
          image: myorg/simple-api:1.0.0
          ports:
            - containerPort: 8000
          envFrom:
            - configMapRef:
                name: api-config
          resources:
            requests:
              cpu: "250m"
              memory: "256Mi"
            limits:
              cpu: "500m"
              memory: "512Mi"
          readinessProbe:
            httpGet:
              path: /ready
              port: 8000
            initialDelaySeconds: 5
            periodSeconds: 5
          livenessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 10
            periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: simple-api
spec:
  selector:
    app: simple-api
  ports:
    - port: 80
      targetPort: 8000
  type: ClusterIP
```

How to read this:

- ConfigMap provides config
- Deployment runs 2 copies of the app
- Service provides stable networking to those Pods

---

## 19. Common Commands Cheat Sheet

### Cluster and resources

```bash
kubectl get nodes
kubectl get pods
kubectl get pods -A
kubectl get svc
kubectl get deploy
kubectl get ingress
```

### Inspect details

```bash
kubectl describe pod <pod-name>
kubectl describe deployment <deployment-name>
kubectl describe service <service-name>
```

### Logs and shell access

```bash
kubectl logs <pod-name>
kubectl logs -f <pod-name>
kubectl exec -it <pod-name> -- sh
```

### Apply and delete

```bash
kubectl apply -f app.yaml
kubectl delete -f app.yaml
```

### Scaling

```bash
kubectl scale deployment backend-api --replicas=5
```

### Rollouts

```bash
kubectl rollout status deployment/backend-api
kubectl rollout restart deployment/backend-api
kubectl rollout undo deployment/backend-api
```

---

## 20. Common Anti-Patterns

### 20.1 Treating Pods like VMs

Bad mindset:

- "I will SSH into this Pod and fix it manually"

Better mindset:

- update image, config, or manifest
- let Kubernetes recreate correct Pods

### 20.2 No requests and limits

This leads to:

- poor scheduling
- unstable performance
- memory issues

### 20.3 Using a Deployment for a database without understanding storage

Stateful systems need:

- stable identity
- persistent storage
- careful failover design

### 20.4 Storing secrets directly in Git

Use:

- external secret managers
- encrypted secret workflows

### 20.5 Huge multi-purpose containers

Prefer:

- one clearly defined application concern per container

### 20.6 Too much Kubernetes too early

Sometimes teams adopt Kubernetes before they actually need:

- multi-service orchestration
- advanced scheduling
- strong standardization

This creates complexity without payoff.

---

## 21. When Kubernetes Is the Right Choice

Kubernetes is a strong fit when:

- you run many services
- you need standardized deployment across teams
- you need autoscaling and self-healing
- you want strong ecosystem integration
- you need portability across environments
- your team has platform maturity

Kubernetes may be overkill when:

- you have one or two simple services
- your team is small and not platform-focused
- ECS, Nomad, or a PaaS would solve the problem more simply
- you do not need its advanced orchestration features

Good engineering answer:

> Kubernetes is powerful, but it is not free. It trades operational complexity for control, portability, and ecosystem richness.

---

## 22. Interview Talking Points

These are strong, concise answers for interviews.

### What is Kubernetes?

> Kubernetes is a declarative container orchestration platform that schedules, runs, scales, and heals containerized applications across a cluster.

### What is a Pod?

> A Pod is the smallest deployable unit in Kubernetes. It usually contains one application container, but can contain multiple tightly coupled containers that share networking and storage.

### Deployment vs StatefulSet?

> Use Deployment for stateless workloads like APIs. Use StatefulSet for stateful systems like databases, where stable identity and persistent storage matter.

### Why use a Service?

> Pods are ephemeral, so their IPs can change. A Service gives a stable network endpoint and load balances traffic across matching Pods.

### What do readiness and liveness probes do?

> Readiness controls whether a Pod receives traffic. Liveness controls whether Kubernetes should restart the container.

### Why are requests and limits important?

> Requests help the scheduler place Pods correctly. Limits prevent one container from consuming excessive resources and destabilizing the node.

### What is Helm?

> Helm is a package manager and templating system for Kubernetes that makes it easier to install and parameterize applications.

### Biggest Kubernetes trade-off?

> It gives strong orchestration, standardization, and ecosystem power, but it adds operational complexity and requires platform maturity to run well.

---

## Final Summary

If you remember only one mental model, remember this:

1. You declare the desired state
2. Kubernetes continuously reconciles toward that state
3. Pods are ephemeral
4. Deployments manage stateless apps
5. Services give stable networking
6. Config, secrets, storage, health checks, and autoscaling complete the runtime model

If you are learning Kubernetes for backend and AI systems, focus first on:

- Pod
- Deployment
- Service
- Ingress
- ConfigMap
- Secret
- PVC
- requests and limits
- probes
- HPA

Those ten ideas cover most day-to-day usage.
