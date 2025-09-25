from openai import OpenAI
from config import settings
import os
import time
import inspect
from rich import print
import json
import logging
import traceback
import asyncio
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
            self.logger.error(f"Full traceback: {traceback.format_exc()}")
            return None

    def merge_json_responses(self, json_responses: list):
        """
        Merges multiple JSON responses from document processing.
        Rules:
        - null values are common, keep them
        - If field has unique value, use it
        - If field has multiple values, use the one with maximum confidence
        - Boolean fields: true > false > null (based on confidence)
        - Lists: merge unique items, keep highest confidence for duplicates
        """
        try:
            
            if not json_responses:
                return None
            
            # Parse all JSON responses
            parsed_responses = []
            for response in json_responses:
                try:
                    if isinstance(response, str):
                        parsed = json.loads(response)
                    else:
                        parsed = response
                    parsed_responses.append(parsed)
                except json.JSONDecodeError as e:
                    self.logger.warning(f"Failed to parse JSON response: {e}")
                    continue
            
            if not parsed_responses:
                return None
            
            # Start with the first response as base
            merged = parsed_responses[0].copy()
            
            # Helper function to merge nested objects
            def merge_nested_objects(base_obj, new_obj, path=""):
                if not isinstance(base_obj, dict) or not isinstance(new_obj, dict):
                    return base_obj
                
                for key, value in new_obj.items():
                    current_path = f"{path}.{key}" if path else key
                    
                    if key not in base_obj:
                        base_obj[key] = value
                    elif isinstance(value, dict) and isinstance(base_obj[key], dict):
                        # Recursively merge nested objects
                        merge_nested_objects(base_obj[key], value, current_path)
                    elif isinstance(value, list) and isinstance(base_obj[key], list):
                        # Merge lists - combine unique items
                        base_obj[key] = self._merge_lists(base_obj[key], value, current_path)
                    elif isinstance(value, dict) and "value" in value and "confidence" in value:
                        # This is a confidence-based field (including booleans)
                        base_obj[key] = self._merge_confidence_field(base_obj[key], value, current_path)
                    else:
                        # For other types, keep the existing value
                        pass
                
                return base_obj
            
            # Merge all responses
            for response in parsed_responses[1:]:
                merged = merge_nested_objects(merged, response)
            
            return json.dumps(merged, indent=2)
            
        except Exception as e:
            self.logger.error(f"Error merging JSON responses: {str(e)}")
            self.logger.error(f"Full traceback: {traceback.format_exc()}")
            return None

    def _merge_confidence_field(self, base_field, new_field, path):
        """Merge confidence-based fields, keeping the one with highest confidence.
        Special handling for boolean fields: true > false > null (based on confidence)"""
        try:
            # Handle null values
            if base_field is None or base_field.get("value") is None:
                return new_field
            if new_field is None or new_field.get("value") is None:
                return base_field
            
            base_value = base_field.get("value")
            new_value = new_field.get("value")
            base_confidence = base_field.get("confidence", 0.0)
            new_confidence = new_field.get("confidence", 0.0)
            
            # Special handling for boolean fields
            if isinstance(base_value, bool) and isinstance(new_value, bool):
                # Boolean logic: true > false > null (based on confidence)
                if base_value == new_value:
                    # Same boolean value, use higher confidence
                    if new_confidence > base_confidence:
                        self.logger.debug(f"Replacing {path} boolean with higher confidence: {new_confidence} > {base_confidence}")
                        return new_field
                    else:
                        return base_field
                else:
                    # Different boolean values
                    if base_value is True and new_value is False:
                        # true > false, but check confidence threshold
                        if new_confidence > base_confidence + 0.1:  # Need significantly higher confidence to override true with false
                            self.logger.debug(f"Replacing {path} true with false due to much higher confidence: {new_confidence} > {base_confidence + 0.1}")
                            return new_field
                        else:
                            return base_field
                    elif base_value is False and new_value is True:
                        # true > false, use true if confidence is reasonable
                        if new_confidence > base_confidence - 0.1:  # Allow slightly lower confidence for true
                            self.logger.debug(f"Replacing {path} false with true: {new_confidence} > {base_confidence - 0.1}")
                            return new_field
                        else:
                            return base_field
            
            # For non-boolean fields, use simple confidence comparison
            if new_confidence > base_confidence:
                self.logger.debug(f"Replacing {path} with higher confidence value: {new_confidence} > {base_confidence}")
                return new_field
            else:
                return base_field
                
        except Exception as e:
            self.logger.warning(f"Error merging confidence field at {path}: {e}")
            return base_field

    def _merge_lists(self, base_list, new_list, path=""):
        """Merge two lists, keeping unique items and handling confidence-based merging"""
        try:
            if not base_list:
                return new_list
            if not new_list:
                return base_list
            
            # Handle empty lists
            if len(base_list) == 0:
                return new_list
            if len(new_list) == 0:
                return base_list
            
            # For simple lists (like pages_checked), combine and deduplicate
            if isinstance(base_list[0], (str, int, float)) and isinstance(new_list[0], (str, int, float)):
                combined = list(set(base_list + new_list))
                return combined
            
            # For complex lists (like ICD10 codes, HCPCS codes, phone numbers), merge by confidence
            if isinstance(base_list[0], dict) and isinstance(new_list[0], dict):
                return self._merge_complex_lists(base_list, new_list, path)
            
            # For mixed or unknown types, concatenate
            return base_list + new_list
            
        except Exception as e:
            self.logger.warning(f"Error merging lists at {path}: {e}")
            return base_list

    def _merge_complex_lists(self, base_list, new_list, path=""):
        """Merge complex lists (like ICD10 codes, HCPCS codes, phone numbers) based on confidence"""
        try:
            merged = base_list.copy()
            
            for new_item in new_list:
                if not isinstance(new_item, dict):
                    merged.append(new_item)
                    continue
                
                # Check if similar item exists in base list
                found_match = False
                for i, base_item in enumerate(merged):
                    if not isinstance(base_item, dict):
                        continue
                    
                    # Different matching strategies based on the field type
                    is_match = False
                    
                    # For ICD10 codes: match by code
                    if "code" in new_item and "code" in base_item:
                        is_match = base_item.get("code") == new_item.get("code")
                    
                    # For phone numbers: match by value
                    elif "value" in new_item and "value" in base_item:
                        is_match = base_item.get("value") == new_item.get("value")
                    
                    # For item descriptions: match by value
                    elif "value" in new_item and "value" in base_item:
                        is_match = base_item.get("value") == new_item.get("value")
                    
                    if is_match:
                        # Same item, compare confidence
                        base_confidence = base_item.get("confidence", 0.0)
                        new_confidence = new_item.get("confidence", 0.0)
                        
                        if new_confidence > base_confidence:
                            self.logger.debug(f"Replacing item in {path} with higher confidence: {new_confidence} > {base_confidence}")
                            merged[i] = new_item
                        found_match = True
                        break
                
                if not found_match:
                    # Add new unique item
                    merged.append(new_item)
            
            return merged
            
        except Exception as e:
            self.logger.warning(f"Error merging complex lists at {path}: {e}")
            return base_list




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
