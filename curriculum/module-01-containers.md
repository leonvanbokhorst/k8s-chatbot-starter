# Module 01 — Containers & Twelve-Factor Flow

## Why this matters

Kubernetes is just a massive container orchestrator. Before you spar with the control plane, you need to wield container images like dual lightsabers. This module locks in the 12-factor habits that keep your services composable when the cluster dragons wake up.

## Learning Objectives

- Explain image immutability, layers, and registries in your own words.
- Design a containerized FastAPI “hello” service that respects 12-factor constraints.
- Use environment variables and health endpoints to configure behavior without baking secrets.
- Push/pull images from a registry (Docker Hub, GHCR) confidently.

## Prerequisite Check

- Python 3.11+ installed
- Docker Desktop or nerdctl/podman with OCI support running locally
- Basic FastAPI knowledge (route, uvicorn basics)

## Core Concepts

- **Immutable images**: why you rebuild rather than mutate containers.
- **Configuration outside the image**: env vars, secrets, config files.
- **Stateless vs stateful**: isolate data services or use external volumes.
- **Health checks**: readiness vs liveness semantics.

## Hands-On Drills

1. Scaffold the app

   - Create `services/gateway/app.py` if not already present (reuse existing or build a `hello` variant).
   - Add `/hello` route returning JSON; include `/health` returning status.

2. Dockerize the service

   - Write a slim `Dockerfile` using `python:3.11-slim` base.
   - Pin dependencies in `requirements.txt` and copy only what you need.
   - Add a non-root user or at least note the tradeoff.

3. Build and run

   ```bash
   docker build -t ghcr.io/<you>/fastapi-hello:0.1.0 .
   docker run --rm -p 8000:8000 -e APP_GREETING="Ahoy" ghcr.io/<you>/fastapi-hello:0.1.0
   curl localhost:8000/hello
   ```

4. Push to a registry

   - Log in (`docker login ghcr.io`), tag, push.
   - Pull from another machine or a teammate to prove it works.

5. Health & config validation
   - Add `APP_GREETING` env var support to your FastAPI route; confirm `curl` reflects runtime value.
   - Hit `/health` to ensure the container reports ready.

## Checkpoint

You can clearly articulate:

- Why Docker images are snapshots and not mutable VMs.
- How env vars and secrets differ.
- Why logs should go to stdout/stderr.
- What makes an app “stateless” and why that matters for scaling.

## Stretch Goals

- Publish the image to a private registry and pull using a read-only token.
- Experiment with multi-stage builds to reduce image size.
- Integrate Poetry or Pipenv instead of plain pip.
- Add simple unit tests and run them inside Docker.

## Resources

- 12 Factor App manifesto — https://12factor.net/
- Docker docs on best practices — https://docs.docker.com/develop/dev-best-practices/
- FastAPI tutorials — https://fastapi.tiangolo.com/tutorial/

## Deliverable

- Working container image pushed to a registry, with notes on the commands used.
- Short journal entry covering what tripped you up and how you solved it.

Onward, Little Wan—Master Lonn nods approvingly when your containers are tidy.
