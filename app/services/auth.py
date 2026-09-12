from app.db.participants import get_participant_by_email


def request_access(email: str):
    email = email.strip().lower()

    participant = get_participant_by_email(email)

    if not participant:
        raise ValueError("Participant not found")

    return participant
