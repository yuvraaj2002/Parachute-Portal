from pydantic import BaseModel
from typing import List

class GenerateDocumentRequest(BaseModel):
    group_id : str
    template_ids: List[int] 