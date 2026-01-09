import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add the src directory to the path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app

client = TestClient(app)


class TestActivitiesEndpoint:
    """Tests for the /activities endpoint"""

    def test_get_activities_returns_all_activities(self):
        """Test that GET /activities returns all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        activities = response.json()
        assert isinstance(activities, dict)
        assert len(activities) > 0
        assert "Basketball" in activities
        assert "Soccer" in activities

    def test_activities_have_required_fields(self):
        """Test that each activity has required fields"""
        response = client.get("/activities")
        activities = response.json()
        
        for activity_name, activity_data in activities.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)


class TestSignupEndpoint:
    """Tests for the /activities/{activity_name}/signup endpoint"""

    def test_signup_successful(self):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Basketball/signup?email=student@test.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "student@test.edu" in data["message"]

    def test_signup_activity_not_found(self):
        """Test signup for non-existent activity"""
        response = client.post(
            "/activities/NonexistentActivity/signup?email=student@test.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_signup_duplicate_email(self):
        """Test that duplicate signup is rejected"""
        # Sign up the first time
        response1 = client.post(
            "/activities/Basketball/signup?email=duplicate@test.edu"
        )
        assert response1.status_code == 200
        
        # Try to sign up again
        response2 = client.post(
            "/activities/Basketball/signup?email=duplicate@test.edu"
        )
        assert response2.status_code == 400
        data = response2.json()
        assert "already signed up" in data["detail"]

    def test_signup_adds_participant(self):
        """Test that signup actually adds the participant"""
        email = "newtester@test.edu"
        client.post(f"/activities/Soccer/signup?email={email}")
        
        # Verify the participant was added
        response = client.get("/activities")
        activities = response.json()
        assert email in activities["Soccer"]["participants"]


class TestUnregisterEndpoint:
    """Tests for the /unregister/{participant_email} endpoint"""

    def test_unregister_successful(self):
        """Test successful unregistration"""
        email = "unregister@test.edu"
        
        # First sign up
        client.post(f"/activities/Art%20Club/signup?email={email}")
        
        # Then unregister
        response = client.delete(f"/unregister/{email}")
        assert response.status_code == 200
        data = response.json()
        assert email in data["message"]

    def test_unregister_participant_not_found(self):
        """Test unregistering non-existent participant"""
        response = client.delete("/unregister/nonexistent@test.edu")
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"]

    def test_unregister_removes_from_all_activities(self):
        """Test that unregister removes participant from all activities"""
        email = "multiactivity@test.edu"
        
        # Sign up for multiple activities
        client.post(f"/activities/Basketball/signup?email={email}")
        client.post(f"/activities/Soccer/signup?email={email}")
        
        # Unregister
        response = client.delete(f"/unregister/{email}")
        assert response.status_code == 200
        
        # Verify removed from both
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email not in activities["Basketball"]["participants"]
        assert email not in activities["Soccer"]["participants"]

    def test_unregister_removes_participant(self):
        """Test that unregister actually removes the participant"""
        email = "remove@test.edu"
        
        # Sign up
        client.post(f"/activities/Debate%20Team/signup?email={email}")
        
        # Unregister
        client.delete(f"/unregister/{email}")
        
        # Verify removal
        response = client.get("/activities")
        activities = response.json()
        assert email not in activities["Debate Team"]["participants"]


class TestRootEndpoint:
    """Tests for the root endpoint"""

    def test_root_redirect(self):
        """Test that root redirects to static index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]
