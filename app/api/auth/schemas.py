from pydantic import BaseModel


class ParticipantResponse(BaseModel):
    id: str
    email: str
    condition: str | None = None
    study_status: str | None = None