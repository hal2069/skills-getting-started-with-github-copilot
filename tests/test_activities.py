"""
Tests for High School Management System API

This test suite covers all endpoints:
- GET /activities
- POST /activities/{activity_name}/signup
- DELETE /activities/{activity_name}/unregister
"""

import pytest
from copy import deepcopy
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture
def reset_activities():
    """Reset activities to initial state before and after each test"""
    # Store original state
    original_activities = deepcopy(activities)
    
    # Reset before test
    activities.clear()
    activities.update(original_activities)
    
    yield
    
    # Reset after test
    activities.clear()
    activities.update(original_activities)


class TestGetActivities:
    """Tests for GET /activities endpoint"""
    
    def test_get_activities_returns_all_activities(self, client, reset_activities):
        """Test that GET /activities returns all activities"""
        response = client.get("/activities")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 9
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data
    
    def test_get_activities_response_structure(self, client, reset_activities):
        """Test that activities have correct structure"""
        response = client.get("/activities")
        data = response.json()
        
        activity = data["Chess Club"]
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity
        assert isinstance(activity["participants"], list)
    
    def test_get_activities_contains_participants(self, client, reset_activities):
        """Test that participants are included in activities"""
        response = client.get("/activities")
        data = response.json()
        
        chess_club = data["Chess Club"]
        assert "michael@mergington.edu" in chess_club["participants"]
        assert "daniel@mergington.edu" in chess_club["participants"]


class TestSignup:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_successful(self, client, reset_activities):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Basketball Team/signup?email=test@mergington.edu"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "Signed up" in data["message"]
        assert "test@mergington.edu" in data["message"]
    
    def test_signup_adds_participant(self, client, reset_activities):
        """Test that signup adds participant to activity"""
        client.post("/activities/Basketball Team/signup?email=test@mergington.edu")
        
        response = client.get("/activities")
        data = response.json()
        assert "test@mergington.edu" in data["Basketball Team"]["participants"]
    
    def test_signup_duplicate_email_returns_error(self, client, reset_activities):
        """Test that duplicate signup returns 400 error"""
        # First signup
        client.post("/activities/Chess Club/signup?email=new@mergington.edu")
        
        # Duplicate signup
        response = client.post(
            "/activities/Chess Club/signup?email=new@mergington.edu"
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]
    
    def test_signup_invalid_activity_returns_404(self, client, reset_activities):
        """Test that signup for non-existent activity returns 404"""
        response = client.post(
            "/activities/Nonexistent Club/signup?email=test@mergington.edu"
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]
    
    def test_signup_multiple_students_same_activity(self, client, reset_activities):
        """Test multiple students can sign up for same activity"""
        client.post("/activities/Soccer Club/signup?email=student1@mergington.edu")
        client.post("/activities/Soccer Club/signup?email=student2@mergington.edu")
        
        response = client.get("/activities")
        data = response.json()
        participants = data["Soccer Club"]["participants"]
        
        assert "student1@mergington.edu" in participants
        assert "student2@mergington.edu" in participants
        assert len(participants) == 2
    
    def test_signup_same_student_different_activities(self, client, reset_activities):
        """Test same student can sign up for multiple activities"""
        email = "student@mergington.edu"
        
        response1 = client.post(f"/activities/Drama Club/signup?email={email}")
        response2 = client.post(f"/activities/Art Club/signup?email={email}")
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        data = client.get("/activities").json()
        assert email in data["Drama Club"]["participants"]
        assert email in data["Art Club"]["participants"]


class TestUnregister:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint"""
    
    def test_unregister_successful(self, client, reset_activities):
        """Test successful unregistration from activity"""
        # First sign up
        client.post("/activities/Chess Club/signup?email=test@mergington.edu")
        
        # Then unregister
        response = client.delete(
            "/activities/Chess Club/unregister?email=test@mergington.edu"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered" in data["message"]
    
    def test_unregister_removes_participant(self, client, reset_activities):
        """Test that unregister removes participant from activity"""
        email = "test@mergington.edu"
        
        # Sign up
        client.post(f"/activities/Programming Class/signup?email={email}")
        
        # Verify signup
        data = client.get("/activities").json()
        assert email in data["Programming Class"]["participants"]
        
        # Unregister
        client.delete(f"/activities/Programming Class/unregister?email={email}")
        
        # Verify removal
        data = client.get("/activities").json()
        assert email not in data["Programming Class"]["participants"]
    
    def test_unregister_nonexistent_participant_returns_400(self, client, reset_activities):
        """Test that unregistering non-existent participant returns 400"""
        response = client.delete(
            "/activities/Gym Class/unregister?email=nonexistent@mergington.edu"
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "not signed up" in data["detail"]
    
    def test_unregister_invalid_activity_returns_404(self, client, reset_activities):
        """Test that unregister for non-existent activity returns 404"""
        response = client.delete(
            "/activities/Nonexistent Club/unregister?email=test@mergington.edu"
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]
    
    def test_unregister_existing_participant(self, client, reset_activities):
        """Test unregistering a participant who was already in the activity"""
        response = client.delete(
            "/activities/Chess Club/unregister?email=michael@mergington.edu"
        )
        
        assert response.status_code == 200
        
        data = client.get("/activities").json()
        chess_club_participants = data["Chess Club"]["participants"]
        assert "michael@mergington.edu" not in chess_club_participants
        assert "daniel@mergington.edu" in chess_club_participants


class TestIntegration:
    """Integration tests combining multiple operations"""
    
    def test_signup_then_unregister_cycle(self, client, reset_activities):
        """Test complete cycle of signup and unregister"""
        email = "integration@mergington.edu"
        activity = "Math Club"
        
        # Initial state
        data = client.get("/activities").json()
        initial_count = len(data[activity]["participants"])
        
        # Sign up
        response1 = client.post(f"/activities/{activity}/signup?email={email}")
        assert response1.status_code == 200
        
        data = client.get("/activities").json()
        assert len(data[activity]["participants"]) == initial_count + 1
        assert email in data[activity]["participants"]
        
        # Unregister
        response2 = client.delete(f"/activities/{activity}/unregister?email={email}")
        assert response2.status_code == 200
        
        data = client.get("/activities").json()
        assert len(data[activity]["participants"]) == initial_count
        assert email not in data[activity]["participants"]
    
    def test_multiple_signups_and_unregisters(self, client, reset_activities):
        """Test multiple signup and unregister operations"""
        activity = "Robotics Club"
        emails = ["user1@mergington.edu", "user2@mergington.edu", "user3@mergington.edu"]
        
        # Sign up multiple students
        for email in emails:
            response = client.post(f"/activities/{activity}/signup?email={email}")
            assert response.status_code == 200
        
        data = client.get("/activities").json()
        assert len(data[activity]["participants"]) == 3
        
        # Unregister middle student
        response = client.delete(
            f"/activities/{activity}/unregister?email={emails[1]}"
        )
        assert response.status_code == 200
        
        data = client.get("/activities").json()
        assert len(data[activity]["participants"]) == 2
        assert emails[0] in data[activity]["participants"]
        assert emails[1] not in data[activity]["participants"]
        assert emails[2] in data[activity]["participants"]
