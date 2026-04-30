"""
FastAPI endpoint tests for the activities management system.
"""

import pytest


class TestGetActivities:
    """Tests for GET /activities endpoint"""

    def test_get_all_activities(self, client):
        """Test successfully retrieving all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) > 0
        
        # Verify all required activity fields exist
        for activity_name, activity_data in data.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)

    def test_activities_have_participants(self, client):
        """Test that initial activities have participant data"""
        response = client.get("/activities")
        data = response.json()
        
        # Verify Chess Club has initial participants
        assert "Chess Club" in data
        chess_club = data["Chess Club"]
        assert len(chess_club["participants"]) >= 0
        assert chess_club["max_participants"] == 12

    def test_activities_response_structure(self, client):
        """Test that activities response has correct structure"""
        response = client.get("/activities")
        data = response.json()
        
        # Get first activity for testing
        first_activity = next(iter(data.values()))
        
        # Verify data types
        assert isinstance(first_activity["description"], str)
        assert isinstance(first_activity["schedule"], str)
        assert isinstance(first_activity["max_participants"], int)
        assert isinstance(first_activity["participants"], list)
        
        # Verify all participants are strings (emails)
        for participant in first_activity["participants"]:
            assert isinstance(participant, str)


class TestRootRedirect:
    """Tests for GET / endpoint"""

    def test_root_redirects_to_static_html(self, client):
        """Test that root path redirects to static index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]

    def test_root_redirect_followed(self, client):
        """Test that following root redirect works"""
        response = client.get("/", follow_redirects=True)
        assert response.status_code == 200


class TestSignupEndpoint:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_successful_signup(self, client):
        """Test successfully signing up a new student"""
        response = client.post(
            "/activities/Chess Club/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]
        assert "Chess Club" in data["message"]

    def test_signup_adds_participant(self, client):
        """Test that signup actually adds participant to activity"""
        # Get initial participants count
        response1 = client.get("/activities")
        initial_count = len(response1.json()["Chess Club"]["participants"])
        
        # Sign up new student
        client.post(
            "/activities/Chess Club/signup?email=student@mergington.edu"
        )
        
        # Verify participant was added
        response2 = client.get("/activities")
        new_count = len(response2.json()["Chess Club"]["participants"])
        assert new_count == initial_count + 1
        assert "student@mergington.edu" in response2.json()["Chess Club"]["participants"]

    def test_signup_nonexistent_activity(self, client):
        """Test signup fails for non-existent activity"""
        response = client.post(
            "/activities/Nonexistent Activity/signup?email=student@mergington.edu"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_signup_duplicate_email(self, client):
        """Test signup fails when email already registered"""
        # Sign up first time
        response1 = client.post(
            "/activities/Chess Club/signup?email=duplicate@mergington.edu"
        )
        assert response1.status_code == 200
        
        # Try to sign up again
        response2 = client.post(
            "/activities/Chess Club/signup?email=duplicate@mergington.edu"
        )
        assert response2.status_code == 400
        assert "already signed up" in response2.json()["detail"]

    def test_signup_multiple_students(self, client):
        """Test multiple students can sign up for same activity"""
        emails = [
            "student1@mergington.edu",
            "student2@mergington.edu",
            "student3@mergington.edu",
        ]
        
        for email in emails:
            response = client.post(
                f"/activities/Tennis Club/signup?email={email}"
            )
            assert response.status_code == 200
        
        # Verify all students are registered
        response = client.get("/activities")
        participants = response.json()["Tennis Club"]["participants"]
        for email in emails:
            assert email in participants

    def test_signup_preserves_existing_participants(self, client):
        """Test that signup preserves original participants"""
        response1 = client.get("/activities")
        original_participants = response1.json()["Chess Club"]["participants"].copy()
        
        # Sign up new student
        client.post(
            "/activities/Chess Club/signup?email=newstudent@mergington.edu"
        )
        
        # Verify original participants are still there
        response2 = client.get("/activities")
        new_participants = response2.json()["Chess Club"]["participants"]
        for participant in original_participants:
            assert participant in new_participants


class TestUnregisterEndpoint:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint"""

    def test_successful_unregister(self, client):
        """Test successfully unregistering a student"""
        # Get an existing participant
        response1 = client.get("/activities")
        chess_participants = response1.json()["Chess Club"]["participants"]
        email_to_remove = chess_participants[0]
        
        # Unregister
        response2 = client.delete(
            f"/activities/Chess Club/unregister?email={email_to_remove}"
        )
        assert response2.status_code == 200
        data = response2.json()
        assert "message" in data
        assert email_to_remove in data["message"]

    def test_unregister_removes_participant(self, client):
        """Test that unregister actually removes participant"""
        # Get initial participants
        response1 = client.get("/activities")
        initial_participants = response1.json()["Chess Club"]["participants"].copy()
        email_to_remove = initial_participants[0]
        
        # Unregister
        client.delete(
            f"/activities/Chess Club/unregister?email={email_to_remove}"
        )
        
        # Verify participant was removed
        response2 = client.get("/activities")
        new_participants = response2.json()["Chess Club"]["participants"]
        assert email_to_remove not in new_participants
        assert len(new_participants) == len(initial_participants) - 1

    def test_unregister_nonexistent_activity(self, client):
        """Test unregister fails for non-existent activity"""
        response = client.delete(
            "/activities/Nonexistent Activity/unregister?email=student@mergington.edu"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_unregister_student_not_registered(self, client):
        """Test unregister fails when student not in activity"""
        response = client.delete(
            "/activities/Chess Club/unregister?email=notregistered@mergington.edu"
        )
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"]

    def test_unregister_preserves_other_participants(self, client):
        """Test that unregistering one student doesn't affect others"""
        # Get participants
        response1 = client.get("/activities")
        original_participants = response1.json()["Tennis Club"]["participants"].copy()
        
        if len(original_participants) > 0:
            email_to_remove = original_participants[0]
            others = original_participants[1:]
            
            # Unregister
            client.delete(
                f"/activities/Tennis Club/unregister?email={email_to_remove}"
            )
            
            # Verify others are still there
            response2 = client.get("/activities")
            remaining = response2.json()["Tennis Club"]["participants"]
            for participant in others:
                assert participant in remaining


class TestSignupUnregisterFlow:
    """Integration tests for signup and unregister flows"""

    def test_signup_then_unregister(self, client):
        """Test complete signup then unregister flow"""
        email = "teststudent@mergington.edu"
        activity = "Drama Club"
        
        # Sign up
        response1 = client.post(
            f"/activities/{activity}/signup?email={email}"
        )
        assert response1.status_code == 200
        
        # Verify signup
        response2 = client.get("/activities")
        assert email in response2.json()[activity]["participants"]
        
        # Unregister
        response3 = client.delete(
            f"/activities/{activity}/unregister?email={email}"
        )
        assert response3.status_code == 200
        
        # Verify unregistered
        response4 = client.get("/activities")
        assert email not in response4.json()[activity]["participants"]

    def test_signup_unregister_signup_again(self, client):
        """Test signup, unregister, then signup again"""
        email = "teststudent2@mergington.edu"
        activity = "Art Studio"
        
        # First signup
        client.post(f"/activities/{activity}/signup?email={email}")
        response1 = client.get("/activities")
        assert email in response1.json()[activity]["participants"]
        
        # Unregister
        client.delete(f"/activities/{activity}/unregister?email={email}")
        response2 = client.get("/activities")
        assert email not in response2.json()[activity]["participants"]
        
        # Sign up again - should succeed
        response3 = client.post(
            f"/activities/{activity}/signup?email={email}"
        )
        assert response3.status_code == 200
        
        response4 = client.get("/activities")
        assert email in response4.json()[activity]["participants"]

    def test_availability_decreases_on_signup(self, client):
        """Test that availability decreases when signing up"""
        activity = "Science Club"
        email = "student@mergington.edu"
        
        response1 = client.get("/activities")
        initial_max = response1.json()[activity]["max_participants"]
        initial_participants = len(response1.json()[activity]["participants"])
        initial_spots = initial_max - initial_participants
        
        # Sign up
        client.post(f"/activities/{activity}/signup?email={email}")
        
        response2 = client.get("/activities")
        new_participants = len(response2.json()[activity]["participants"])
        new_spots = initial_max - new_participants
        
        assert new_spots == initial_spots - 1

    def test_availability_increases_on_unregister(self, client):
        """Test that availability increases when unregistering"""
        activity = "Programming Class"
        
        # Get initial state
        response1 = client.get("/activities")
        initial_max = response1.json()[activity]["max_participants"]
        initial_participants = len(response1.json()[activity]["participants"])
        initial_spots = initial_max - initial_participants
        
        # Unregister someone
        email = response1.json()[activity]["participants"][0]
        client.delete(f"/activities/{activity}/unregister?email={email}")
        
        # Check new availability
        response2 = client.get("/activities")
        new_participants = len(response2.json()[activity]["participants"])
        new_spots = initial_max - new_participants
        
        assert new_spots == initial_spots + 1
