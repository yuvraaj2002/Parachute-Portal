from openai import OpenAI
from config import settings
import os
import time
import inspect
from rich import print
import logging
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from prompt_registry.document_extraction_prompt import system_prompt_doc_extraction, human_prompt_doc_extraction, MEDICAL_DOC_SCHEMA

class LLMService:
    def __init__(self):
        self.openai_client = OpenAI(api_key=settings.openai_api_key)
        self.openai = ChatOpenAI(api_key=settings.openai_api_key, model="gpt-4o-mini", temperature=0.2,timeout=None, max_retries=2)
        self.logger = logging.getLogger(__name__)

    async def process_medical_document(self, markdown_content: str):
        """
        Processes a medical document and returns a structured JSON of the document.
        """
        try:
            messages = [
                SystemMessage(system_prompt_doc_extraction),
                HumanMessage(
                    human_prompt_doc_extraction.format(
                        markdown_content=markdown_content,
                        schema=MEDICAL_DOC_SCHEMA
                    )
                )
            ]
            response = self.openai.invoke(messages)
            response = response.content
            return response
        except Exception as e:
            self.logger.error(f"Error processing medical document: {str(e)}")
            import traceback
            self.logger.error(f"Full traceback: {traceback.format_exc()}")
            return None




import asyncio

if __name__ == "__main__":
    async def main():
        llm_service = LLMService()
        markdown_content = """
--- Page 1 ---

athena GC - MHW - Memorial Health and Wellness 11511 Katy Fwy, HOUSTON TX 77079-1908 09-05-2025 3:01 PM ET GC - MHW - Memorial Health and Wellness 11511 Katy Fwy, HOUSTON TX 77079-1908 613-300253563 00 1 of 2

CHIZER, Mary (Id #9204319, dob: 12/18/1965)

This fax may contain sensitive and confidential personal health information that is being sent for the sole use of the intended recipient. Unintended recipients are directed to securely destroy any materials received. You are hereby notified that the unauthorized disclosure or other unlawful use of this fax or any personal health information is prohibited. To the extent patient information contained in this fax is subject to 42 CFR Part 2, this regulation prohibits unauthorized disclosure of these records.

If you received this fax in error, please visit www.athenahealth.com/NotMyFax to notify the sender and confirm that the information will be destroyed. If you do not have internet access, please call 1-888-482-8436 to notify the sender and confirm that the information will be destroyed. Thank you for your attention and cooperation. [ID:1008738047-H-8042]

Durable Medical Equipment Order 08/21/2025

|  Prescriber | Supplier  |
| --- | --- |
|  VALLERY ADA, FNP Memorial Health and Wellness 11511 Katy Fwy Suite 605 HOUSTON, TX 77079-1908 Phone: (281) 741-4045 Fax: (713) 482-4525 | OPTIMISTIC HEALTHCARE 14520 MEMORIAL DR STE 22 HOUSTON, TX 77079 Phone: (800) 674-4440 Fax: (833) 623-3134  |

Patient Information

|  Patient Name | CHIZER, MARY  |
| --- | --- |
|  Sex - DOB - Age | F 12/18/1965 59yo  |
|  Address | 14333 MEMORIAL DR/APT 85 HOUSTON, TX 77079-6726  |
|  Phone | H: (281) 435-3667 M: (281) 435-3667  |
|  Primary Insurance | Cigna - TN - TX - AL - IL - OK - FL - PA - MS (Medicare Replacement/Advantage - HMO) ID: 64X9H2R28 Policy Holder: CHIZER, MARY C  |
|  Secondary Insurance | Medicaid-TX (Medicaid) ID: 505509163 Policy Holder: CHIZER, MARY  |

DME Order Information

|  Applicable Diagnoses | Obesity ICD-10: E66.2: Morbid (severe) obesity with alveolar hypoventilation  |
| --- | --- |
|  Supply | BARIATRIC WALKER  |
|  Quantity | 1  |
|  SIG | Use as directed.  |
|  Refills Allowed |   |
|  DAW? | N  |
|  Note to Supplier |   |

Electronically Signed by: VALLERY ADA, FNP, NP


--- Page 2 ---

athena
GC - MHW - Memorial Health and Wellness 11511 Katy Fwy, HOUSTON TX 77079-1908
09-05-2025 3:01 PM ET
613-300253563
00 2 of 2
CHIZER, Mary (Id #9204319, dob: 12/18/1965)

ValaryAda, FNP-BC

Date: 08/21/2025
Electronically ordered/documented by: VALLERY ADA, FNP NPI # 1194430579
Supervising Provider: VALLERY ADA, FNP
Supervising Provider DEA #: DEA # MA7979074

Prescription is void if more than one (1) prescription is written per blank.
"""
        result = await llm_service.process_medical_document(markdown_content)
        print(result)

    asyncio.run(main())
