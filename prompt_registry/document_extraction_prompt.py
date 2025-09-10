# Medical document data extraction prompts
system_prompt_doc_extraction = """
You are a precise medical document extraction assistant.
You receive OCR output of a medical document in Markdown format.
Your task is to extract information into a fixed JSON schema.

Rules:
- Always return ONLY valid JSON (no text, no Markdown, no commentary).
- If a field is missing, set it to null.
- For fields that can have multiple values (e.g., phone numbers, ICD-10 codes, HCPCS codes), return an array.
- Dates must be in YYYY-MM-DD format. If incomplete (month/year only), set missing parts to "01".
- Do not hallucinate values. Extract only what is present in the text.
- Preserve the exact field names and JSON structure given below.
- Do NOT modify or escape curly braces or the schema format in your response.
- Do NOT include any explanation, markdown, or extra text before or after the JSON.
"""

# To avoid KeyError with .format(), use a placeholder for the schema and inject it at runtime.
MEDICAL_DOC_EXTRACTION_SCHEMA = '''
{
  "patient_information": {
    "full_name": null,
    "date_of_birth": null,
    "gender": null,
    "address": {
      "street": null,
      "city": null,
      "state": null,
      "zip": null
    },
    "phone_numbers": [],
    "email": null,
    "emergency_contact": {
      "name": null,
      "relation": null,
      "phone": null
    }
  },
  "insurance_billing": {
    "primary_payer": null,
    "mbi_or_medicaid_id": null,
    "policy_member_id": null,
    "group_number": null,
    "bin_pcn": null,
    "secondary_insurance": null,
    "workers_comp_claim": null,
    "guarantor": {
      "name": null,
      "relation": null,
      "contact": null
    }
  },
  "provider_prescriber": {
    "provider_full_name": null,
    "npi_number": null,
    "dea_number": null,
    "specialty": null,
    "clinic_facility_name": null,
    "clinic_address_phone_fax": null
  },
  "clinical_documentation": {
    "icd10_codes": [],
    "medical_necessity_summary": null,
    "onset_or_injury_date": null,
    "prior_treatments": null,
    "face_to_face_documentation_present": null
  },
  "orders_dme_details": {
    "hcpcs_codes": [],
    "item_descriptions": [],
    "quantity_ordered": null,
    "frequency_replacement": null,
    "length_of_need": null,
    "supply_start_date": null,
    "place_of_service": null,
    "serial_lot_number": null
  },
  "patient_financials": {
    "abn_or_notice": null,
    "estimated_cost": null,
    "patient_choice_option": null,
    "aob_signed_dated": null,
    "supplier_standards_ack_signed": null,
    "hipaa_acknowledgement_present": null
  }
}
'''
human_prompt_doc_extraction = (
    "Here is the OCR Markdown content:\n"
    "{markdown_content}\n\n"
    "Now extract the information into this schema. "
    "Return ONLY valid JSON, with no extra text or formatting:\n"
    "{schema}\n"
)