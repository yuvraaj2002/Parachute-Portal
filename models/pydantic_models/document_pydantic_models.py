from pydantic import BaseModel

class SignatureRequestInput(BaseModel):
    document_id: str 