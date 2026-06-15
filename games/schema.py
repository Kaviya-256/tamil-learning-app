from pydantic import BaseModel

class GameRoundSchema(BaseModel):
    session_id: str
    round_no: int
    attempt_no: int
    is_correct: bool
    response_time_ms: int