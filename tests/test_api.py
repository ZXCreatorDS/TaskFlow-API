def create_user(client, email="user@example.com", display_name="User", role="operator"):
    response = client.post(
        "/v1/users",
        json={"email": email, "display_name": display_name, "role": role},
    )
    assert response.status_code == 201, response.text
    return response.json()


def create_project(client, name="TaskFlow"):
    response = client.post(
        "/v1/projects",
        json={"name": name, "description": "Test project"},
    )
    assert response.status_code == 201, response.text
    return response.json()


def create_label(client, name="backend", color="#2563eb"):
    response = client.post("/v1/labels", json={"name": name, "color": color})
    assert response.status_code == 201, response.text
    return response.json()


def create_task(client, project_id, assignee_id=None, label_id=None, **overrides):
    payload = {
        "project_id": project_id,
        "assignee_id": assignee_id,
        "label_id": label_id,
        "title": "Build API",
    }
    payload.update(overrides)
    response = client.post("/v1/tasks", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def create_comment(client, task_id, author_id, body="In progress"):
    response = client.post(
        "/v1/comments",
        json={"task_id": task_id, "author_id": author_id, "body": body},
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_user_crud_and_conflicts(client):
    user = create_user(client)
    assert user["role"] == "operator"
    assert user["created_at"]

    assert len(client.get("/v1/users").json()) == 1
    assert client.get(f"/v1/users/{user['id']}").status_code == 200

    response = client.patch(
        f"/v1/users/{user['id']}",
        json={"display_name": "Updated"},
    )
    assert response.status_code == 200
    assert response.json()["display_name"] == "Updated"

    duplicate = client.post(
        "/v1/users",
        json={"email": "user@example.com", "display_name": "Duplicate"},
    )
    assert duplicate.status_code == 409

    assert (
        client.post(
            "/v1/users",
            json={"email": "bad-email", "display_name": "Bad"},
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/v1/users",
            json={
                "email": "other@example.com",
                "display_name": "Bad role",
                "role": "superadmin",
            },
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/v1/users",
            json={
                "id": 99,
                "email": "id@example.com",
                "display_name": "Service field",
            },
        ).status_code
        == 422
    )

    assert client.delete(f"/v1/users/{user['id']}").status_code == 204
    assert client.get(f"/v1/users/{user['id']}").status_code == 404


def test_project_label_task_comment_flow(client):
    user = create_user(client)
    project = create_project(client)
    label = create_label(client)

    task = create_task(
        client,
        project["id"],
        assignee_id=user["id"],
        label_id=label["id"],
        priority="high",
    )
    assert task["status"] == "open"
    assert task["priority"] == "high"

    comment = create_comment(client, task["id"], user["id"])
    assert comment["body"] == "In progress"

    tasks = client.get(f"/v1/tasks?project_id={project['id']}&status=open").json()
    assert len(tasks) == 1
    assert tasks[0]["id"] == task["id"]

    comments = client.get(f"/v1/comments?task_id={task['id']}").json()
    assert len(comments) == 1

    response = client.patch(
        f"/v1/tasks/{task['id']}",
        json={"status": "done"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "done"

    response = client.patch(
        f"/v1/comments/{comment['id']}",
        json={"body": "Done"},
    )
    assert response.status_code == 200
    assert response.json()["body"] == "Done"

    assert (
        client.post(
            "/v1/labels",
            json={"name": "backend", "color": "#000000"},
        ).status_code
        == 409
    )
    assert (
        client.post(
            "/v1/labels",
            json={"name": "bad-color", "color": "blue"},
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/v1/tasks",
            json={"project_id": project["id"], "title": "Bad", "status": "closed"},
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/v1/tasks",
            json={"project_id": 999, "title": "Missing project"},
        ).status_code
        == 409
    )
    assert (
        client.post(
            "/v1/comments",
            json={
                "task_id": task["id"],
                "author_id": user["id"],
                "body": "   ",
            },
        ).status_code
        == 422
    )


def test_project_delete_cascades_tasks_and_comments(client):
    user = create_user(client)
    project = create_project(client)
    task = create_task(client, project["id"], assignee_id=user["id"])
    create_comment(client, task["id"], user["id"])

    assert client.delete(f"/v1/projects/{project['id']}").status_code == 204
    assert client.get(f"/v1/tasks/{task['id']}").status_code == 404
    assert client.get(f"/v1/comments?task_id={task['id']}").json() == []


def test_assignee_and_label_delete_set_null(client):
    author = create_user(client, email="author@example.com")
    assignee = create_user(client, email="assignee@example.com")
    project = create_project(client)
    label = create_label(client)
    task = create_task(
        client,
        project["id"],
        assignee_id=assignee["id"],
        label_id=label["id"],
    )

    assert client.delete(f"/v1/labels/{label['id']}").status_code == 204
    updated = client.get(f"/v1/tasks/{task['id']}").json()
    assert updated["label_id"] is None

    assert client.delete(f"/v1/users/{assignee['id']}").status_code == 204
    updated = client.get(f"/v1/tasks/{task['id']}").json()
    assert updated["assignee_id"] is None
    assert author["id"] != assignee["id"]


def test_user_with_comments_cannot_be_deleted(client):
    user = create_user(client)
    project = create_project(client)
    task = create_task(client, project["id"])
    create_comment(client, task["id"], user["id"])

    assert client.delete(f"/v1/users/{user['id']}").status_code == 409
    assert client.get(f"/v1/users/{user['id']}").status_code == 200
    assert len(client.get(f"/v1/comments?task_id={task['id']}").json()) == 1


def test_404_and_query_validation(client):
    assert client.get("/v1/users/999").status_code == 404
    assert client.delete("/v1/projects/999").status_code == 404
    assert client.patch("/v1/tasks/999", json={"title": "x"}).status_code == 404
    assert client.get("/v1/tasks?status=closed").status_code == 422
    assert client.patch("/v1/tasks/1", json={"status": None}).status_code == 422


def test_docs_and_openapi(client):
    assert client.get("/docs").status_code == 200
    assert client.get("/openapi.json").status_code == 200
