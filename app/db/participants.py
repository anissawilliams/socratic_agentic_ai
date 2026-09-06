from app.services.supabase import get_supabase_client


def get_participant_by_email(email: str):
    supabase = get_supabase_client()

    response = (
        supabase
        .table("study_participant")
        .select("id, email, condition")
        .eq("email", email)
        .limit(1)
        .execute()
    )

    if not response.data:
        return None

    return response.data[0]