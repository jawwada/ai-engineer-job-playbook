# Python and Backend Development Brush-Up Guide

This README is a practical refresh guide for an intermediate Python developer who wants to revisit core Python concepts, backend development fundamentals, and common framework and tooling tradeoffs.

It is designed for:

- Interview preparation
- Backend system design review
- API development refresh
- Async and distributed processing revision

## Table of Contents

- [Terminology Glossary](#terminology-glossary)
- [Python Core Refresh](#python-core-refresh)
- [Backend Development Concepts](#backend-development-concepts)
- [Django vs FastAPI](#django-vs-fastapi)
- [Swagger and Postman Alternatives](#swagger-and-postman-alternatives)
- [Celery, Async I/O, and Distributed Processing](#celery-async-io-and-distributed-processing)
- [WebSockets and Realtime Communication](#websockets-and-realtime-communication)
- [Other Python Backend Alternatives](#other-python-backend-alternatives)
- [Recommended Study Order](#recommended-study-order)
- [Official References](#official-references)

## Terminology Glossary

This section defines the most important terms mentioned in this guide and gives a quick example for each.

### Python terms

- Mutability: whether an object can be changed after creation.
  Example: `numbers = [1, 2]` is mutable because `numbers.append(3)` changes it. `point = (1, 2)` is immutable because tuples cannot be modified in place.
- Hashability: whether an object has a stable hash value and can be used as a dictionary key or set member.
  Example: `(1, 2)` is hashable, but `[1, 2]` is not.
- Comprehension: a compact syntax for building collections.
  Example: `[x * x for x in range(5) if x % 2 == 0]` produces `[0, 4, 16]`.
- Iterator: an object that yields one value at a time via `next()`.
  Example: `it = iter([10, 20, 30])`; `next(it)` returns `10`.
- Generator: a lazy iterator created with `yield` or a generator expression.
  Example: `(x * x for x in range(3))` yields values one by one instead of building a full list immediately.
- Closure: a function that remembers variables from its outer scope.
  Example: a function returned by `make_adder(5)` can remember the value `5`.
- Decorator: a function that wraps another function to extend or alter its behavior.
  Example: `@login_required` can check authentication before running a view.
- Descriptor: an object that customizes attribute access using methods like `__get__` and `__set__`.
  Example: Python methods are descriptors, which is why `obj.method` becomes a bound method.
- Shallow copy: copies the outer container, but still references the same inner objects.
  Example: copying `[[1], [2]]` with `copy.copy()` creates a new outer list, but the inner lists are shared.
- Deep copy: recursively copies nested objects too.
  Example: `copy.deepcopy([[1], [2]])` creates fully independent nested lists.
- GIL: the Global Interpreter Lock in CPython that allows only one thread to execute Python bytecode at a time.
  Example: threads help with blocking I/O, but usually do not speed up CPU-heavy pure Python code.

### Backend terms

- Idempotency: repeating the same request should have the same final effect on server state.
  Example: sending the same `PUT /users/1` payload twice should still leave one updated user, not create duplicates.
- CORS: Cross-Origin Resource Sharing, a browser security mechanism that controls whether one origin can call another.
  Example: a frontend at `https://app.example.com` calling `https://api.example.com` may require CORS headers.
- Authentication: verifying who a user is.
  Example: checking a username/password or validating a JWT.
- Authorization: checking what an authenticated user is allowed to do.
  Example: a normal user can read their own profile, but only an admin can delete accounts.
- Session: server-side user state usually identified by a cookie.
  Example: the browser sends a session cookie and the server loads the user from session storage.
- Token: a portable credential sent with each request.
  Example: `Authorization: Bearer <token>`.
- Resource-based routing: modeling API URLs around nouns rather than actions.
  Example: use `/users/42/orders` instead of `/getUserOrders`.
- OpenAPI: a standard machine-readable format for describing HTTP APIs.
  Example: FastAPI can generate an OpenAPI schema that powers `/docs` and `/openapi.json`.
- WSGI: the traditional sync Python web server interface.
  Example: classic Django and Flask deployments historically used WSGI servers like Gunicorn.
- ASGI: the async-capable Python server interface.
  Example: FastAPI commonly runs on Uvicorn using ASGI.
- ORM: Object-Relational Mapper, a layer that maps Python objects to database tables.
  Example: `User.objects.get(id=1)` in Django ORM.
- Migration: a versioned change to the database schema.
  Example: adding an `email` column to the `users` table through a migration file.
- Connection pooling: reusing database connections instead of opening a new one for every request.
  Example: a pool of 20 PostgreSQL connections shared across requests.
- `N+1` query problem: one query for a parent list plus one extra query per item.
  Example: fetching 100 blog posts and then lazily fetching each author separately causes 101 queries.
- Rate limiting: restricting how often a client can call an endpoint.
  Example: 100 requests per minute per API key.
- Observability: the ability to understand system behavior from logs, metrics, and traces.
  Example: tracing a slow request across the API, cache, and database.
- Horizontal scaling: increasing capacity by adding more machines or worker instances.
  Example: running 10 API containers behind a load balancer instead of one large server.

### Async and distributed processing terms

- Coroutine: a function declared with `async def` that can be paused and resumed.
  Example: `await fetch_user()` inside an async view.
- Event loop: the scheduler that runs coroutines and handles async I/O.
  Example: `asyncio.run(main())` creates and runs an event loop.
- Task queue: a system for deferring work to background workers.
  Example: queue an email job after signup instead of sending it during the request.
- Broker: the message transport between producers and workers.
  Example: Redis or RabbitMQ used by Celery.
- Worker: a process that consumes queued jobs and executes them.
  Example: a Celery worker pulling tasks from Redis.
- Retry: re-attempting failed work, usually with limits and delays.
  Example: retry a webhook delivery after a temporary `503` response.
- SSE: Server-Sent Events, a one-way streaming protocol from server to client over HTTP.
  Example: streaming job progress updates to a dashboard.
- WebSocket: a persistent bidirectional connection between client and server.
  Example: a chat app where both browser and server send messages over the same connection.
- Socket.IO: a higher-level realtime framework layered above transport details.
  Example: using event names like `"join_room"` and `"new_message"` with reconnect behavior built in.

## Python Core Refresh

### High-priority data structures

Revisit the built-in types first:

- `list`: ordered, mutable, indexable, great for iteration and append-heavy workflows
- `tuple`: ordered, immutable, hashable when contents are hashable
- `dict`: key-value mapping with average `O(1)` lookup
- `set`: unique values with average `O(1)` membership checks

Know the tradeoffs:

- Use `list` when order matters and duplicates are allowed
- Use `tuple` for fixed, immutable records
- Use `dict` for keyed access and structured objects
- Use `set` for deduplication and membership testing

Quick example:

```python
items = [1, 2, 3]
point = (10, 20)
user = {"id": 1, "name": "Ada"}
tags = {"python", "backend", "api"}

# list: ordered, mutable
items.append(4)           # [1, 2, 3, 4]
items[0]                  # 1

# dict: O(1) keyed access
user["name"]              # "Ada"
user.get("age", 0)        # 0 (safe default)

# set: dedup + membership
"python" in tags          # True
tags.add("fastapi")

# tuple: immutable, hashable — can be a dict key
coords = {(0, 0): "origin", (1, 2): "point A"}
```

### Important adjacent structures

Know when built-ins are not enough:

- `collections.deque`: efficient append/pop from both ends
- `collections.defaultdict`: avoids repetitive key initialization
- `collections.Counter`: frequency counting
- `heapq`: priority queue behavior
- `bisect`: binary search in sorted lists
- `itertools`: lazy iteration and composition helpers

```python
from collections import deque, defaultdict, Counter
import heapq

# deque: O(1) on both ends (list.insert(0) is O(n))
q = deque([1, 2, 3])
q.appendleft(0)   # deque([0, 1, 2, 3])
q.pop()           # 3

# defaultdict: no KeyError on first access
word_lists = defaultdict(list)
word_lists["a"].append("apple")   # no need to init the key first

# Counter: instant frequency map
counts = Counter(["a", "b", "a", "c", "a"])
counts.most_common(2)   # [("a", 3), ("b", 1)]

# heapq: min-heap (always gives smallest first)
heap = [5, 3, 8, 1]
heapq.heapify(heap)
heapq.heappop(heap)   # 1
```

### Must-review Python concepts

- List, set, and dict comprehensions
- Nested comprehensions
- Iterators and generators
- `yield` and lazy evaluation
- Unpacking and extended unpacking
- Slicing semantics
- Shallow copy vs deep copy
- Hashability and mutability
- `is` vs `==`
- Exception handling and custom exceptions
- Context managers and `with`
- Decorators and closures
- Descriptors at a conceptual level
- `*args`, `**kwargs`, positional-only, and keyword-only arguments

Quick examples:

```python
# Comprehensions
squares = [x * x for x in range(5)]                         # [0, 1, 4, 9, 16]
even_squares = [x * x for x in range(10) if x % 2 == 0]    # [0, 4, 16, 36, 64]
word_lengths = {w: len(w) for w in ["hello", "world"]}      # {"hello": 5, "world": 5}
unique_evens = {x for x in range(10) if x % 2 == 0}        # {0, 2, 4, 6, 8}

# Generator: lazy — values produced on demand, not all at once
def countdown(n):
    while n > 0:
        yield n
        n -= 1

for val in countdown(3):
    print(val)   # 3, 2, 1 one at a time

# Generator expression (like list comprehension but lazy)
gen = (x * x for x in range(1_000_000))   # no memory spike
next(gen)   # 0

# Closures
def make_adder(n):
    def add(x):
        return x + n   # n is remembered from outer scope
    return add

add5 = make_adder(5)
add5(3)   # 8

# Decorators
import time

def timer(func):
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        print(f"{func.__name__} took {time.time() - start:.3f}s")
        return result
    return wrapper

@timer
def slow_function():
    time.sleep(0.1)

# Context managers
class ManagedFile:
    def __init__(self, path):
        self.path = path

    def __enter__(self):
        self.file = open(self.path)
        return self.file

    def __exit__(self, *args):
        self.file.close()

with ManagedFile("data.txt") as f:
    content = f.read()   # file always closed after block

# Unpacking
first, *rest = [1, 2, 3, 4]   # first=1, rest=[2, 3, 4]
a, b = b, a                    # swap without temp variable

# *args and **kwargs
def flexible(required, *args, keyword_only=False, **kwargs):
    print(required, args, keyword_only, kwargs)

flexible("x", 1, 2, keyword_only=True, extra="yes")
# "x" (1, 2) True {"extra": "yes"}
```

### Typing and modern Python

Refresh modern type-hint usage:

- `list[str]`, `dict[str, int]`
- `TypedDict`
- `Protocol`
- `Literal`
- `Annotated`
- Generic classes and functions
- `Self`

Know the purpose of typing:

- Better editor support
- Easier refactoring
- Better API contracts
- Stronger validation ecosystems via tools like Pydantic

```python
from typing import TypedDict, Protocol, Literal, Annotated
from typing import Generic, TypeVar

# Basic annotations
def greet(name: str, times: int = 1) -> list[str]:
    return [f"Hello {name}"] * times

# TypedDict: typed dict shape (no runtime validation, just hints)
class UserDict(TypedDict):
    id: int
    name: str
    email: str

# Protocol: structural typing (duck typing with type safety)
class Serializable(Protocol):
    def to_json(self) -> str: ...

# Literal: restrict to specific values
Status = Literal["pending", "active", "banned"]

def set_status(user_id: int, status: Status) -> None:
    ...

# Generic class
T = TypeVar("T")

class Stack(Generic[T]):
    def __init__(self) -> None:
        self._items: list[T] = []

    def push(self, item: T) -> None:
        self._items.append(item)

    def pop(self) -> T:
        return self._items.pop()

stack: Stack[int] = Stack()
stack.push(1)
stack.pop()   # int

# Annotated: attach metadata (used heavily by Pydantic/FastAPI)
from typing import Annotated
PositiveInt = Annotated[int, "must be > 0"]
```

### Common interview gotchas

- Mutable default arguments
- Late binding in closures
- Loop variable capture in lambdas
- Difference between copying references and copying objects
- Why tuples can sometimes be dictionary keys
- Why sets require hashable elements

Example of a mutable default argument bug:

```python
def add_item(item, bucket=[]):
    bucket.append(item)
    return bucket

print(add_item("a"))  # ["a"]
print(add_item("b"))  # ["a", "b"] <- surprising if you expected a fresh list
```

### Concurrency mental model

- Threads: useful for blocking I/O, but limited by the GIL for CPU-heavy Python code
- Processes: useful for CPU-bound parallelism
- `asyncio`: best for I/O-bound concurrency inside a single process

Rule of thumb:

- CPU-bound work: processes
- I/O-bound concurrent work: `asyncio` or threads
- Work that must survive request lifecycles: task queue

```python
import asyncio
import threading
from concurrent.futures import ProcessPoolExecutor

# asyncio: concurrent I/O (e.g. multiple API calls at once)
async def fetch(url: str) -> str:
    await asyncio.sleep(0.1)   # simulates network call
    return f"data from {url}"

async def main():
    # run 3 fetches concurrently, not sequentially
    results = await asyncio.gather(
        fetch("https://api.example.com/users"),
        fetch("https://api.example.com/orders"),
        fetch("https://api.example.com/products"),
    )
    print(results)   # all 3 done in ~0.1s total, not 0.3s

asyncio.run(main())

# threading: I/O-bound work (e.g. file reads, legacy blocking calls)
def blocking_read(filename):
    with open(filename) as f:
        return f.read()

t = threading.Thread(target=blocking_read, args=("data.txt",))
t.start()
t.join()

# multiprocessing: CPU-bound work (e.g. image resize, number crunching)
def cpu_heavy(n):
    return sum(i * i for i in range(n))

with ProcessPoolExecutor() as executor:
    results = list(executor.map(cpu_heavy, [1_000_000, 2_000_000, 3_000_000]))
```

### Practical Python development stack

- `pyproject.toml` for project configuration
- Virtual environments for dependency isolation
- `pytest` for tests
- `ruff` for linting and formatting
- `mypy` or `pyright` for static typing
- `uv` as a modern Python package and project manager

## Backend Development Concepts

### HTTP fundamentals

Be comfortable with:

- HTTP methods: `GET`, `POST`, `PUT`, `PATCH`, `DELETE`
- Idempotency
- Status codes: `2xx`, `4xx`, `5xx`
- Headers, cookies, sessions, and tokens
- Authentication vs authorization
- Pagination, filtering, sorting
- CORS
- Caching and cache headers
- Content negotiation
- Rate limiting

Quick examples:

- `GET /users/1`: fetch one user
- `POST /orders`: create a new order
- `PUT /users/1`: replace or fully update one user resource
- `PATCH /users/1`: partially update one user resource
- Idempotent example: repeating the same `PUT /users/1` request should not create extra users
- Non-idempotent example: repeating the same `POST /orders` request may create multiple orders

```python
# HTTP requests in Python with httpx (async) or requests (sync)
import httpx

# Sync client (requests-style)
with httpx.Client() as client:
    # GET
    r = client.get("https://api.example.com/users/1")
    r.status_code    # 200
    r.json()         # {"id": 1, "name": "Ada"}

    # POST with JSON body
    r = client.post(
        "https://api.example.com/users",
        json={"name": "Ada", "email": "ada@example.com"},
        headers={"Authorization": "Bearer my-token"},
    )
    r.status_code    # 201

    # PATCH — partial update
    r = client.patch("https://api.example.com/users/1", json={"name": "Ada Lovelace"})

    # DELETE
    r = client.delete("https://api.example.com/users/1")
    r.status_code    # 204 No Content

# Status code reference:
# 200 OK, 201 Created, 204 No Content
# 400 Bad Request, 401 Unauthorized, 403 Forbidden, 404 Not Found, 422 Unprocessable
# 429 Too Many Requests, 500 Internal Server Error, 503 Service Unavailable

# JWT auth header pattern
headers = {"Authorization": f"Bearer {jwt_token}"}

# Pagination pattern
r = client.get("/users", params={"page": 2, "limit": 50})
# URL becomes: /users?page=2&limit=50
```

### API design basics

Know how to structure APIs:

- Resource-based routing
- Consistent naming
- Stable versioning strategy
- Clear error responses
- Validation at boundaries
- Separation between transport and business logic

```python
# Pydantic — validation at the boundary (used by FastAPI automatically)
from pydantic import BaseModel, EmailStr, field_validator, model_validator
from datetime import datetime

class OrderCreate(BaseModel):
    product_id: int
    quantity: int
    email: EmailStr

    @field_validator("quantity")
    @classmethod
    def quantity_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("quantity must be > 0")
        return v

# FastAPI uses this automatically — invalid requests return 422
# POST /orders  body: {"product_id": 1, "quantity": -1, "email": "bad"}
# → 422 Unprocessable Entity with field-level error details

# JWT authentication pattern with FastAPI
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt   # pip install pyjwt

SECRET = "your-secret-key"
security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET, algorithms=["HS256"])
        return payload["sub"]   # user id
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.get("/me")
async def get_me(user_id: str = Depends(verify_token)):
    return {"user_id": user_id}

# Resource-based URL design
# Good                          Bad
# GET    /users                 GET /getUsers
# GET    /users/42              GET /getUserById?id=42
# POST   /users                 POST /createUser
# PATCH  /users/42              POST /updateUser
# DELETE /users/42              POST /deleteUser
# GET    /users/42/orders       GET /getOrdersForUser?userId=42

# Versioning
# /api/v1/users
# /api/v2/users

# Error response shape (consistent across all endpoints)
# {"error": "not_found", "message": "User 42 does not exist", "request_id": "abc-123"}
```

### WSGI vs ASGI

- `WSGI` is the traditional Python web interface for synchronous applications
- `ASGI` supports async request handling, WebSockets, streaming, and long-lived connections

Use `ASGI` when:

- You need async request handling
- You need WebSockets
- You need server push, streaming, or long-lived connections

### Database fundamentals

Know these well:

- Transactions
- Indexes
- Connection pooling
- Query planning basics
- `N+1` query problems
- Migrations
- Isolation and locking concepts
- ORM tradeoffs vs raw SQL

Quick examples:

- Transaction: transfer money by debiting one account and crediting another as one unit of work
- Index: add an index on `email` so user lookup by email is fast
- Migration: create a new column `last_login_at` in the `users` table
- `N+1`: query 50 orders, then fetch each customer separately inside a loop

```python
# SQLAlchemy (async) — common in FastAPI apps
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import select, ForeignKey

engine = create_async_engine("postgresql+asyncpg://user:pass@localhost/db")

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(unique=True, index=True)
    orders: Mapped[list["Order"]] = relationship(back_populates="user")

class Order(Base):
    __tablename__ = "orders"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    user: Mapped[User] = relationship(back_populates="orders")

# Transaction — both operations succeed or both roll back
async with AsyncSession(engine) as session:
    async with session.begin():
        sender = await session.get(User, sender_id)
        receiver = await session.get(User, receiver_id)
        sender.balance -= 100
        receiver.balance += 100
    # commit happens automatically on exit

# N+1 problem and fix
async with AsyncSession(engine) as session:
    # BAD: 1 query for orders + 1 per order for the user = N+1 queries
    orders = (await session.execute(select(Order))).scalars().all()
    for order in orders:
        print(order.user.email)   # lazy load fires a new query each time

    # GOOD: JOIN upfront — 1 query total
    from sqlalchemy.orm import selectinload
    stmt = select(Order).options(selectinload(Order.user))
    orders = (await session.execute(stmt)).scalars().all()
    for order in orders:
        print(order.user.email)   # already loaded, no extra queries

# Raw SQL when ORM gets in the way
from sqlalchemy import text
result = await session.execute(
    text("SELECT id, email FROM users WHERE created_at > :since"),
    {"since": "2026-01-01"},
)
rows = result.fetchall()
```

### Backend architecture habits

Good backend design usually separates:

- Request layer
- Validation layer
- Business logic layer
- Persistence layer
- Async/background execution layer

### Production concerns

Do not ignore:

- Structured logging
- Metrics
- Tracing
- Health checks
- Retries and timeouts
- Secret management
- Deployment strategy
- Observability
- Error reporting

## Django vs FastAPI

### Django

Choose Django when you want:

- A full-stack framework
- Built-in ORM and migrations
- Built-in admin
- Strong authentication and permissions primitives
- Convention-heavy architecture
- Rapid delivery of product backends and internal tools

Strengths:

- Mature ecosystem
- Excellent for CRUD-heavy applications
- Great admin experience
- Strong batteries-included approach
- Stable long-term maintainability

Tradeoffs:

- Heavier than API-first frameworks
- Async support is improving, but not every part of Django is equally async-native
- Can feel opinionated if you want a very lightweight service

```python
# models.py
from django.db import models

class User(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

# views.py (class-based)
from django.http import JsonResponse
from django.views import View
from .models import User

class UserDetailView(View):
    def get(self, request, user_id):
        try:
            user = User.objects.get(pk=user_id)
            return JsonResponse({"id": user.id, "name": user.name})
        except User.DoesNotExist:
            return JsonResponse({"error": "not found"}, status=404)

# urls.py
from django.urls import path
from .views import UserDetailView

urlpatterns = [
    path("users/<int:user_id>/", UserDetailView.as_view()),
]

# Django admin — free out of the box
# admin.py
from django.contrib import admin
from .models import User
admin.site.register(User)   # instant CRUD admin panel at /admin/

# Django ORM queries
users = User.objects.filter(email__endswith="@example.com").order_by("-created_at")
user = User.objects.select_related("profile").get(pk=1)   # avoids N+1
```

### FastAPI

Choose FastAPI when you want:

- API-first development
- Strong async ergonomics
- Modern typing-driven request and response modeling
- Automatic OpenAPI generation
- Very fast iteration on service APIs

Strengths:

- Great developer experience for APIs
- Built-in OpenAPI docs
- Excellent with Pydantic-style validation
- Natural fit for microservices and ML-facing APIs
- ASGI-native

Tradeoffs:

- Less batteries-included for full product workflows
- No equivalent of Django admin out of the box
- You assemble more of the stack yourself

```python
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from typing import Annotated

app = FastAPI()

# Pydantic models — request validation + response schema + OpenAPI docs
class UserCreate(BaseModel):
    name: str
    email: EmailStr

class UserResponse(BaseModel):
    id: int
    name: str
    email: str

# In-memory store for illustration
db: dict[int, dict] = {}
counter = 0

# Basic route — GET /
@app.get("/")
async def root():
    return {"message": "Hello World"}

# POST with request body validation
@app.post("/users/", response_model=UserResponse, status_code=201)
async def create_user(user: UserCreate):
    global counter
    counter += 1
    db[counter] = {"id": counter, **user.model_dump()}
    return db[counter]

# GET with path parameter
@app.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int):
    if user_id not in db:
        raise HTTPException(status_code=404, detail="User not found")
    return db[user_id]

# Dependency injection
def get_db():
    return db   # real app: yield a DB session here

@app.get("/users/")
async def list_users(store: Annotated[dict, Depends(get_db)]):
    return list(store.values())

# Background tasks
from fastapi import BackgroundTasks

def send_welcome_email(email: str):
    print(f"Sending welcome email to {email}")

@app.post("/users/register")
async def register(user: UserCreate, background_tasks: BackgroundTasks):
    background_tasks.add_task(send_welcome_email, user.email)
    return {"message": "registered"}

# Auto docs available at:
#   http://localhost:8000/docs   (Swagger UI)
#   http://localhost:8000/redoc  (ReDoc)
```

### Real-world recommendation

Use Django if:

- You are building a product backend
- You need admin panels quickly
- You want strong conventions and a broad ecosystem
- Your application is database-heavy and business-workflow-heavy

Use FastAPI if:

- You are building an API service
- You need async-first patterns
- You want automatic docs and schema generation
- You are integrating ML, external APIs, or high-I/O workloads

### Important current note

As of May 15, 2026:

- `Django 5.2` is the current LTS release
- `Django 4.2` support ended in April 2026

## Swagger and Postman Alternatives

There are two categories to distinguish clearly:

- API documentation and visualization tools
- API client and testing tools

### API documentation tools

- `Swagger UI`: interactive API docs from OpenAPI
- `ReDoc`: cleaner documentation-focused OpenAPI rendering
- `Scalar`: modern API reference/docs experience
- `Redocly`: OpenAPI linting, validation, transformation, and docs workflows

### API client and testing tools

- `Postman`: feature-rich API platform
- `Bruno`: git-friendly and offline-first
- `Insomnia`: mature desktop client
- `Hoppscotch`: lightweight and open-source
- `HTTPie`: excellent CLI and desktop/web workflow for quick testing

### Recommendations by use case

- Best git-friendly option: `Bruno`
- Best mature desktop alternative: `Insomnia`
- Best lightweight open-source option: `Hoppscotch`
- Best terminal-first option: `HTTPie`
- Best docs-first option: `ReDoc`, `Scalar`, or `Redocly`

### Best practice

Prefer this workflow:

1. Define your API contract in OpenAPI
2. Generate docs from OpenAPI
3. Use a client tool for manual testing
4. Use automated API tests in CI

Quick example:

- Write `openapi.yaml`
- Render docs with Swagger UI or ReDoc
- Test requests manually in Bruno or Insomnia
- Run automated API tests in CI with `pytest` or collection runners

## Celery, Async I/O, and Distributed Processing

### `asyncio`

`asyncio` is for concurrency inside one process.

Use it for:

- Concurrent HTTP calls
- Async DB drivers
- Streams
- WebSockets
- High-I/O workloads

Do not use it as a replacement for a task queue when work must:

- Survive restarts
- Retry reliably
- Be distributed across machines
- Be decoupled from request lifecycles

Quick example:

```python
import asyncio
import httpx   # async HTTP client

async def fetch_user(client: httpx.AsyncClient, user_id: int) -> dict:
    response = await client.get(f"https://api.example.com/users/{user_id}")
    return response.json()

async def main():
    async with httpx.AsyncClient() as client:
        # Sequential: 3 calls × ~0.5s each = ~1.5s total
        # u1 = await fetch_user(client, 1)
        # u2 = await fetch_user(client, 2)
        # u3 = await fetch_user(client, 3)

        # Concurrent: all 3 run at once = ~0.5s total
        u1, u2, u3 = await asyncio.gather(
            fetch_user(client, 1),
            fetch_user(client, 2),
            fetch_user(client, 3),
        )
        print(u1, u2, u3)

asyncio.run(main())

# asyncio.create_task: fire a task without waiting immediately
async def background_job():
    await asyncio.sleep(5)
    print("done")

async def main2():
    task = asyncio.create_task(background_job())   # starts now
    print("doing other work")                       # runs while background_job waits
    await task                                      # wait for it to finish

# Timeout
async def main3():
    try:
        result = await asyncio.wait_for(fetch_user(None, 1), timeout=2.0)
    except asyncio.TimeoutError:
        print("request took too long")
```

### Celery

Use Celery when you need:

- Background jobs
- Retries
- Scheduled jobs
- Worker fleets
- Routing across queues
- Horizontal scale
- Durable asynchronous execution

Typical Celery use cases:

- Email sending
- Report generation
- Video or document processing
- Batch pipelines
- Cache warmups
- External webhook workflows

Quick terminology example:

- Producer: your web app calling `send_welcome_email.delay(user_id)`
- Broker: Redis or RabbitMQ carrying the task message
- Worker: a Celery process executing `send_welcome_email`
- Result backend: optional store for task state or return values

```python
# celery_app.py
from celery import Celery

app = Celery(
    "myapp",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/1",
)

# tasks.py
from celery_app import app
import time

@app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_welcome_email(self, user_id: int):
    try:
        # simulate email sending
        print(f"Sending email to user {user_id}")
        time.sleep(2)
        return {"status": "sent", "user_id": user_id}
    except Exception as exc:
        raise self.retry(exc=exc)   # retry up to 3 times

@app.task
def generate_report(report_id: int):
    print(f"Generating report {report_id}")
    return f"report_{report_id}.pdf"

# Calling tasks from your web app (producer side)
# Fire and forget
send_welcome_email.delay(user_id=42)

# Call with countdown delay (run in 30 seconds)
send_welcome_email.apply_async(args=[42], countdown=30)

# Schedule for a specific time
from datetime import datetime, timezone
send_welcome_email.apply_async(args=[42], eta=datetime(2026, 6, 1, tzinfo=timezone.utc))

# Check task result
result = generate_report.delay(report_id=7)
result.id        # task UUID
result.status    # "PENDING" / "SUCCESS" / "FAILURE"
result.get()     # blocks until done: "report_7.pdf"

# Run a worker (in terminal):
# celery -A celery_app worker --loglevel=info

# Periodic tasks (like cron) with Celery Beat:
app.conf.beat_schedule = {
    "cleanup-every-midnight": {
        "task": "tasks.cleanup_old_sessions",
        "schedule": 86400.0,   # every 24 hours in seconds
    },
}
```

### Task queue alternatives

- `RQ`: simpler Redis-backed jobs
- `Dramatiq`: simpler API with good production features
- `Arq`: async-native Redis-backed job queue
- `APScheduler`: scheduling library, not a full distributed task queue

### Tool selection guidance

Use:

- `Celery` for mature, feature-rich distributed task processing
- `RQ` for simple Redis-backed background jobs
- `Dramatiq` for a clean middle ground
- `Arq` for deeply async-native applications
- `APScheduler` for recurring in-process scheduling

## WebSockets and Realtime Communication

### When to use WebSockets

Use WebSockets when you need true bidirectional realtime communication:

- Chat
- Realtime dashboards with client interaction
- Multiplayer or collaborative workflows
- Live operations/control channels

### When not to use WebSockets

If the server only needs to push updates to the client, consider `SSE` first:

- Notifications
- Progress updates
- Activity feeds
- Monitoring streams

`SSE` is often simpler than WebSockets when communication is one-way.

Quick examples:

- `SSE`: a progress page that receives `10%`, `20%`, `30%` updates from the server
- WebSocket: a chat room where the browser sends `"hello"` and the server broadcasts it to other clients

### Python ecosystem options

- FastAPI has built-in WebSocket support
- Django commonly uses `Channels`
- `Starlette` gives lower-level ASGI WebSocket control
- `python-socketio` is useful if you specifically want the Socket.IO model

```python
# FastAPI WebSocket — bidirectional chat example
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI()

class ConnectionManager:
    def __init__(self):
        self.active: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)

    def disconnect(self, ws: WebSocket):
        self.active.remove(ws)

    async def broadcast(self, message: str):
        for ws in self.active:
            await ws.send_text(message)

manager = ConnectionManager()

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(f"Client {client_id}: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"Client {client_id} left")

# FastAPI SSE — one-way server push (progress updates, notifications)
from fastapi.responses import StreamingResponse
import asyncio

@app.get("/progress/{job_id}")
async def stream_progress(job_id: int):
    async def event_generator():
        for pct in range(0, 101, 10):
            await asyncio.sleep(0.5)
            yield f"data: {pct}%\n\n"   # SSE format

    return StreamingResponse(event_generator(), media_type="text/event-stream")

# JavaScript client side (SSE):
# const es = new EventSource("/progress/42");
# es.onmessage = (e) => console.log(e.data);  // "10%", "20%", ...

# JavaScript client side (WebSocket):
# const ws = new WebSocket("ws://localhost:8000/ws/1");
# ws.onmessage = (e) => console.log(e.data);
# ws.send("hello");
```

### Practical guidance

Prefer:

- `SSE` for one-way server-to-client streaming
- raw WebSockets for standard bidirectional realtime apps
- `Socket.IO` only if you need its event/room/reconnect abstraction

## Other Python Backend Alternatives

### Django REST Framework

Use when:

- You are already in Django
- You want a mature REST layer on top of Django

```python
# serializers.py
from rest_framework import serializers
from .models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "name", "email"]

# views.py
from rest_framework import viewsets, permissions
from .models import User
from .serializers import UserSerializer

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

# urls.py — one line registers GET/POST/PUT/PATCH/DELETE
from rest_framework.routers import DefaultRouter
router = DefaultRouter()
router.register("users", UserViewSet)
```

### Django Ninja

Use when:

- You want Django plus a more modern API experience
- You like type hints and automatic docs but want to stay on Django

```python
# api.py
from ninja import NinjaAPI, Schema
from .models import User

api = NinjaAPI()

class UserOut(Schema):
    id: int
    name: str
    email: str

@api.get("/users/{user_id}", response=UserOut)
def get_user(request, user_id: int):
    return User.objects.get(pk=user_id)   # auto-serialized via UserOut
```

### Flask

Use when:

- You want a lightweight sync-first framework
- You prefer assembling your own stack

```python
from flask import Flask, jsonify, request, abort

app = Flask(__name__)

users = {}

@app.route("/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    user = users.get(user_id)
    if not user:
        abort(404)
    return jsonify(user)

@app.route("/users", methods=["POST"])
def create_user():
    data = request.get_json()
    user_id = len(users) + 1
    users[user_id] = {"id": user_id, **data}
    return jsonify(users[user_id]), 201

if __name__ == "__main__":
    app.run(debug=True)
```

### Quart

Use when:

- You like Flask ergonomics
- You want async support and WebSockets

```python
from quart import Quart, jsonify
import asyncio

app = Quart(__name__)

@app.route("/users/<int:user_id>")
async def get_user(user_id: int):
    await asyncio.sleep(0)   # can use await here, unlike Flask
    return jsonify({"id": user_id})
```

### Starlette

Use when:

- You want lower-level ASGI control
- You are building custom async services

```python
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route

async def homepage(request):
    return JSONResponse({"message": "Hello"})

async def get_user(request):
    user_id = request.path_params["user_id"]
    return JSONResponse({"id": user_id})

app = Starlette(routes=[
    Route("/", homepage),
    Route("/users/{user_id:int}", get_user),
])
# Run: uvicorn app:app
```

### Litestar

Use when:

- You want a modern ASGI framework with strong typing and OpenAPI support

```python
from litestar import Litestar, get, post
from litestar.dto import DTOConfig
from dataclasses import dataclass

@dataclass
class User:
    id: int
    name: str

@get("/users/{user_id:int}")
async def get_user(user_id: int) -> User:
    return User(id=user_id, name="Ada")

@post("/users")
async def create_user(data: User) -> User:
    return data

app = Litestar([get_user, create_user])
```

## Recommended Study Order

### Phase 1: Python fundamentals

- Built-in data structures
- `collections`
- comprehensions and generators
- decorators and context managers
- typing
- copying, mutability, and hashing

### Phase 2: Async and concurrency

- event loop basics
- coroutines
- `async` and `await`
- tasks and cancellation
- I/O concurrency
- threads vs processes vs async

### Phase 3: Backend foundations

- HTTP semantics
- API design
- auth
- caching
- database performance
- deployment and observability

### Phase 4: Framework comparison

Build the same small API in:

- Django
- FastAPI

Then compare:

- project structure
- validation
- authentication
- performance ergonomics
- async ergonomics
- developer experience

### Phase 5: Production patterns

- add Redis
- add one background worker system
- add one realtime endpoint
- add tests
- add OpenAPI docs
- containerize it

## Official References

### Python

- [Python data structures](https://docs.python.org/3/tutorial/datastructures.html)
- [Python typing](https://docs.python.org/3/library/typing.html)
- [Python asyncio](https://docs.python.org/3/library/asyncio.html)

### Django

- [Django 5.2 release notes](https://docs.djangoproject.com/en/5.2/releases/5.2/)
- [Django async support](https://docs.djangoproject.com/en/5.2/topics/async/)
- [Django documentation](https://docs.djangoproject.com/en/5.2/)

### FastAPI

- [FastAPI first steps](https://fastapi.tiangolo.com/tutorial/first-steps/)
- [FastAPI WebSockets](https://fastapi.tiangolo.com/advanced/websockets/)

### Task queues and async processing

- [Celery](https://docs.celeryq.dev/en/stable/getting-started/introduction.html)
- [RQ](https://python-rq.org/docs/)
- [Dramatiq](https://dramatiq.io/)
- [Arq](https://arq-docs.helpmanual.io/)

### API tooling and OpenAPI

- [What is OpenAPI](https://www.openapis.org/what-is-openapi)
- [OpenAPI specifications](https://spec.openapis.org/oas/)
- [Bruno docs](https://docs.usebruno.com/)
- [Insomnia docs](https://developer.konghq.com/index/insomnia/)
- [Hoppscotch docs](https://docs.hoppscotch.io/index)
- [HTTPie docs](https://httpie.io/docs)
- [Redocly docs](https://redocly.com/docs/redoc)
- [Scalar API references](https://guides.scalar.com/scalar/scalar-api-references/getting-started)

### Realtime tools and frameworks

- [Django Channels](https://channels.readthedocs.io/en/latest/)
- [Starlette WebSockets](https://www.starlette.io/websockets/)
- [python-socketio](https://python-socketio.readthedocs.io/)
- [Django Ninja](https://django-ninja.dev/)
- [Litestar](https://litestar.dev/)
- [Quart](https://quart.palletsprojects.com/en/stable/)

## Final Notes

If you are brushing up for interviews, focus on:

- data structure tradeoffs
- Python internals and gotchas
- HTTP and API design
- async vs task queues
- framework selection tradeoffs
- database performance patterns

If you are brushing up for practical backend work, focus on:

- testing
- observability
- retries and resilience
- schema validation
- queues and realtime tradeoffs
- deployment and operations
