import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


client = TestClient(app)


@pytest.fixture(autouse=True)
def restore_participants():
    participant_snapshots = {
        name: activity["participants"][:]
        for name, activity in activities.items()
    }
    yield
    for name, participants in participant_snapshots.items():
        activities[name]["participants"][:] = participants


def test_root_redirects_to_frontend():
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_activity_data():
    response = client.get("/activities")

    assert response.status_code == 200
    assert "Chess Club" in response.json()
    assert response.json()["Chess Club"]["participants"] == activities["Chess Club"]["participants"]


def test_signup_adds_participant():
    email = "new-student@mergington.edu"

    response = client.post("/activities/Soccer Team/signup", params={"email": email})

    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for Soccer Team"}
    assert email in activities["Soccer Team"]["participants"]


def test_signup_rejects_duplicate_participant():
    email = "new-student@mergington.edu"
    client.post("/activities/Soccer Team/signup", params={"email": email})

    response = client.post("/activities/Soccer Team/signup", params={"email": email})

    assert response.status_code == 400
    assert response.json()["detail"] == "Student is already signed up"


def test_signup_rejects_unknown_activity():
    response = client.post("/activities/Unknown%20Club/signup", params={"email": "student@mergington.edu"})

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_removes_participant():
    email = "new-student@mergington.edu"
    client.post("/activities/Soccer Team/signup", params={"email": email})

    response = client.delete("/activities/Soccer Team/signup", params={"email": email})

    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from Soccer Team"}
    assert email not in activities["Soccer Team"]["participants"]


def test_unregister_rejects_missing_participant():
    response = client.delete(
        "/activities/Soccer Team/signup",
        params={"email": "not-signed-up@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up"


def test_unregister_rejects_unknown_activity():
    response = client.delete(
        "/activities/Unknown%20Club/signup",
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"