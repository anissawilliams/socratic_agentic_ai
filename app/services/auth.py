from app.db.participants import get_participant_by_email


def request_access(email: str):
    email = email.strip().lower()

    print(f"AUTH EMAIL: {email}")

    participant = get_participant_by_email(email)

    print(f"PARTICIPANT: {participant}")

    if not participant:
        raise ValueError("Participant not found")

    return participant