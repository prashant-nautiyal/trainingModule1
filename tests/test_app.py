import pytest


class TestRootEndpoint:
    """Tests for the root endpoint."""

    def test_get_root_redirects_to_static(self, client):
        """Verify that GET / redirects to /static/index.html."""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivitiesEndpoint:
    """Tests for the GET /activities endpoint."""

    def test_get_activities_returns_all(self, client):
        """Verify GET /activities returns all activities with correct structure."""
        response = client.get("/activities")
        assert response.status_code == 200

        activities = response.json()
        assert isinstance(activities, dict)
        assert len(activities) == 10  # We have 10 activities in our fixture

        # Check that each activity has the required fields
        for activity_name, activity_data in activities.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)

    def test_get_activities_includes_chess_club(self, client):
        """Verify Chess Club is in the activities list with correct data."""
        response = client.get("/activities")
        activities = response.json()

        assert "Chess Club" in activities
        chess = activities["Chess Club"]
        assert chess["max_participants"] == 12
        assert "michael@mergington.edu" in chess["participants"]
        assert "daniel@mergington.edu" in chess["participants"]

    def test_get_activities_includes_empty_activity(self, client):
        """Verify activities with no participants return empty list."""
        response = client.get("/activities")
        activities = response.json()

        assert "Basketball Team" in activities
        basketball = activities["Basketball Team"]
        assert basketball["participants"] == []


class TestSignupEndpoint:
    """Tests for the POST /activities/{activity_name}/signup endpoint."""

    def test_signup_for_activity_success(self, client):
        """Verify successful signup adds participant and returns success message."""
        new_email = "alex@mergington.edu"
        activity_name = "Basketball Team"

        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": new_email}
        )

        assert response.status_code == 200
        assert response.json()["message"] == f"Signed up {new_email} for {activity_name}"

        # Verify participant was added
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert new_email in activities[activity_name]["participants"]

    def test_signup_for_activity_duplicate_email(self, client):
        """Verify signup fails (400) when student already signed up."""
        email = "michael@mergington.edu"  # Already in Chess Club
        activity_name = "Chess Club"

        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]

    def test_signup_for_activity_not_found(self, client):
        """Verify signup fails (404) when activity doesn't exist."""
        response = client.post(
            "/activities/NonExistent Club/signup",
            params={"email": "test@mergington.edu"}
        )

        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_signup_multiple_different_activities(self, client):
        """Verify same student can sign up for multiple activities."""
        email = "newstudent@mergington.edu"

        # Sign up for Basketball Team
        response1 = client.post(
            "/activities/Basketball Team/signup",
            params={"email": email}
        )
        assert response1.status_code == 200

        # Sign up for Soccer Club
        response2 = client.post(
            "/activities/Soccer Club/signup",
            params={"email": email}
        )
        assert response2.status_code == 200

        # Verify both signups succeeded
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email in activities["Basketball Team"]["participants"]
        assert email in activities["Soccer Club"]["participants"]


class TestRemoveParticipantEndpoint:
    """Tests for the DELETE /activities/{activity_name}/participants endpoint."""

    def test_remove_participant_success(self, client):
        """Verify successful removal of participant."""
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # This email is in Chess Club

        response = client.delete(
            f"/activities/{activity_name}/participants",
            params={"email": email}
        )

        assert response.status_code == 200
        assert response.json()["message"] == f"Removed {email} from {activity_name}"

        # Verify participant was removed
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email not in activities[activity_name]["participants"]

    def test_remove_participant_activity_not_found(self, client):
        """Verify delete fails (404) when activity doesn't exist."""
        response = client.delete(
            "/activities/NonExistent Activity/participants",
            params={"email": "test@mergington.edu"}
        )

        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_remove_participant_not_in_activity(self, client):
        """Verify delete fails (404) when participant not in activity."""
        activity_name = "Chess Club"
        email = "notinchess@mergington.edu"

        response = client.delete(
            f"/activities/{activity_name}/participants",
            params={"email": email}
        )

        assert response.status_code == 404
        assert "Participant not found" in response.json()["detail"]

    def test_remove_participant_then_re_signup(self, client):
        """Verify student can sign up again after being removed."""
        activity_name = "Basketball Team"
        email = "student@mergington.edu"

        # Sign up
        response1 = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        assert response1.status_code == 200

        # Remove
        response2 = client.delete(
            f"/activities/{activity_name}/participants",
            params={"email": email}
        )
        assert response2.status_code == 200

        # Sign up again
        response3 = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        assert response3.status_code == 200

        # Verify re-signup succeeded
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email in activities[activity_name]["participants"]
