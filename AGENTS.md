# AGENTS.md

## Overview
This file provides guidance for AI coding agents to be productive in the FastFlow project. It highlights key conventions, build/test commands, and important components.

---

## Build and Run Instructions
- Refer to the [README.md](README.md) for detailed instructions.
- To start the project using Docker:
  ```bash
  docker compose up --build -d
  ```
- Backend initialization tasks:
  - `python manage.py migrate`
  - `python manage.py seed_fastflow`

---

## Backend Webhook Functionality
- The `webhook_test_view` function in [backend/restaurante/webhook_views.py](backend/restaurante/webhook_views.py#L206-L250) handles sending test webhooks.
- Endpoint: `/webhooks/test/`
- Key steps:
  1. Validates the webhook subscription.
  2. Creates a test event.
  3. Sends the event immediately.

---

## URL Configuration
- Webhook-related endpoints are defined in [backend/restaurante/urls.py](backend/restaurante/urls.py#L60-L80).
- Example endpoints:
  - `/webhooks/subscriptions/`
  - `/webhooks/subscriptions/<int:webhook_id>/`
  - `/webhooks/test/`

---

## Notes for AI Agents
- Always ensure the backend is initialized properly before testing webhook functionality.
- Use the provided Docker setup for consistent development environments.
- Link to existing documentation (e.g., `README.md`) instead of duplicating content.