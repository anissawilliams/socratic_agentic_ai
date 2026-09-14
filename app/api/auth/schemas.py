from pydantic import BaseModel, Field

class ParticipanCodeRequest(BaseModel):
    code: str = Field(min_length=8, max_length=64)

class ParticipantResponse(BaseModel):
    id: str
    email: str
    condition: str | None = None