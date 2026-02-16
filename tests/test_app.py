import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app

client = TestClient(app)


class TestActivitiesEndpoint:
    """Tests for the GET /activities endpoint"""

    def test_get_activities_returns_200(self):
        """Test that activities endpoint returns status 200"""
        response = client.get("/activities")
        assert response.status_code == 200

    def test_get_activities_returns_dict(self):
        """Test that activities endpoint returns a dictionary"""
        response = client.get("/activities")
        assert isinstance(response.json(), dict)

    def test_get_activities_contains_expected_activities(self):
        """Test that activities list contains expected activities"""
        response = client.get("/activities")
        activities = response.json()
        expected_activities = ["Chess Club", "Programming Class", "Gym Class"]
        for activity in expected_activities:
            assert activity in activities

    def test_activity_has_required_fields(self):
        """Test that each activity has the required fields"""
        response = client.get("/activities")
        activities = response.json()
        required_fields = ["description", "schedule", "max_participants", "participants"]
        
        for activity_name, activity_data in activities.items():
            for field in required_fields:
                assert field in activity_data, f"Activity {activity_name} missing {field}"


class TestSignupEndpoint:
    """Tests for the POST /activities/{activity_name}/signup endpoint"""

    def test_signup_new_student(self):
        """Test signing up a new student for an activity"""
        response = client.post(
            "/activities/Chess%20Club/signup?email=test@mergington.edu"
        )
        assert response.status_code == 200
        assert "signed up" in response.json()["message"].lower()

    def test_signup_nonexistent_activity(self):
        """Test signing up for a non-existent activity"""
        response = client.post(
            "/activities/Nonexistent%20Activity/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_signup_duplicate_student(self):
        """Test that duplicate signups are rejected"""
        email = "duplicate@mergington.edu"
        # First signup
        client.post(f"/activities/Chess%20Club/signup?email={email}")
        # Try to sign up again
        response = client.post(f"/activities/Chess%20Club/signup?email={email}")
        assert response.status_code == 400
        assert "already" in response.json()["detail"].lower()

    def test_signup_updates_participant_count(self):
        """Test that signing up adds the student to participants"""
        email = "newstudent@mergington.edu"
        response = client.post(
            f"/activities/Programming%20Class/signup?email={email}"
        )
        assert response.status_code == 200
        
        # Verify the student is in participants
        activities = client.get("/activities").json()
        assert email in activities["Programming Class"]["participants"]


class TestUnregisterEndpoint:
    """Tests for the POST /activities/{activity_name}/unregister endpoint"""

    def test_unregister_existing_student(self):
        """Test unregistering an existing student"""
        email = "michael@mergington.edu"
        response = client.post(
            f"/activities/Chess%20Club/unregister?email={email}"
        )
        assert response.status_code == 200
        assert "unregistered" in response.json()["message"].lower()

    def test_unregister_nonexistent_activity(self):
        """Test unregistering from a non-existent activity"""
        response = client.post(
            "/activities/Nonexistent%20Activity/unregister?email=test@mergington.edu"
        )
        assert response.status_code == 404

    def test_unregister_student_not_signed_up(self):
        """Test unregistering a student who is not signed up"""
        response = client.post(
            "/activities/Basketball/unregister?email=notregistered@mergington.edu"
        )
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"].lower()

    def test_unregister_removes_participant(self):
        """Test that unregistering removes the student from participants"""
        email = "james@mergington.edu"
        # Verify student is signed up initially
        activities = client.get("/activities").json()
        assert email in activities["Tennis Club"]["participants"]
        
        # Unregister
        response = client.post(
            f"/activities/Tennis%20Club/unregister?email={email}"
        )
        assert response.status_code == 200
        
        # Verify student is no longer in participants
        activities = client.get("/activities").json()
        assert email not in activities["Tennis Club"]["participants"]


class TestRootEndpoint:
    """Tests for the GET / endpoint"""

    def test_root_redirects_to_static(self):
        """Test that root endpoint redirects to static files"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"
