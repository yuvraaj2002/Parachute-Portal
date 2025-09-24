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
MEDICAL_DOC_SCHEMA = """
GOAL:
From the OCR content, extract every field described in the Medical Extraction / Compliance checklist (patient demographics, insurance/billing, provider/prescriber, clinical documentation, DME/orders, financials, delivery/proof, administrative/tracking, and Medicare/Medicaid/Commercial/WorkersComp checklist items). Produce a single JSON object that exactly follows the schema below.

OUTPUT RULES (MUST FOLLOW EXACTLY):
1. Output ONLY valid JSON (no additional text). Keys must appear exactly as in the schema. Use `null` when a value is not present.
2. Dates MUST be normalized to ISO 8601 date only: YYYY-MM-DD. If you can only extract a partial date (month/year) use YYYY-MM-00. If no date, null.
3. Phone numbers: try to normalize to E.164 if country is clear (e.g., +1XXXXXXXXXX). If country unknown, return local cleaned digits only (e.g., 4155551212). Also provide original_text if available.
4. Names: Title Case (e.g., "John A. Smith"). IDs (NPI, DEA, MBI) return as extracted trimmed alphanumeric with uppercase where appropriate.
5. All lists (ICD10, HCPCS, phone_numbers, etc.) must be arrays. If none, return empty array [].
6. For every extracted field, include a `confidence` score (0.0-1.0) representing how confident you are that this field value is correct. If field not found, value=null and confidence=0.0.
7. If a field is present in multiple places (e.g., provider appears on page 1 and page 3), provide a single value and assign confidence reflecting overall certainty.
8. For checklist items (e.g., ABN signed & dated) return a boolean presence field with accompanying confidence.
9. Return `extraction_confidence` top-level (0.0-1.0) — your best estimate for completeness/accuracy of the extracted JSON.
10. If a value is ambiguous (multiple candidate values), include `candidates` for that field with each candidate's value, confidence, and a short `reason` for selection. Populate primary field with best choice.

SCHEMA (output JSON must match this structure; replace evidence arrays with confidence):

{
  "patient_information": {
    "full_name": { "value": null, "confidence": 0.0 },
    "date_of_birth": { "value": null, "confidence": 0.0 },
    "gender": { "value": null, "confidence": 0.0 },
    "address": {
      "street": { "value": null, "confidence": 0.0 },
      "city": { "value": null, "confidence": 0.0 },
      "state": { "value": null, "confidence": 0.0 },
      "zip": { "value": null, "confidence": 0.0 }
    },
    "phone_numbers": [ { "value": null, "original_text": null, "confidence": 0.0 } ],
    "email": { "value": null, "confidence": 0.0 },
    "emergency_contact": {
      "name": { "value": null, "confidence": 0.0 },
      "relation": { "value": null, "confidence": 0.0 },
      "phone": { "value": null, "original_text": null, "confidence": 0.0 }
    },
    "copy_of_id_present": { "value": null, "confidence": 0.0 }
  },

  "insurance_billing": {
    "primary_payer": { "value": null, "confidence": 0.0 },
    "mbi_or_medicaid_id": { "value": null, "confidence": 0.0 },
    "policy_member_id": { "value": null, "confidence": 0.0 },
    "group_number": { "value": null, "confidence": 0.0 },
    "bin_pcn": { "value": null, "confidence": 0.0 },
    "secondary_insurance": { "value": null, "confidence": 0.0 },
    "workers_comp_claim": { "value": null, "confidence": 0.0 },
    "guarantor": {
      "name": { "value": null, "confidence": 0.0 },
      "relation": { "value": null, "confidence": 0.0 },
      "contact": { "value": null, "original_text": null, "confidence": 0.0 }
    }
  },

  "provider_prescriber": {
    "provider_full_name": { "value": null, "confidence": 0.0 },
    "npi_number": { "value": null, "confidence": 0.0 },
    "dea_number": { "value": null, "confidence": 0.0 },
    "specialty": { "value": null, "confidence": 0.0 },
    "clinic_facility_name": { "value": null, "confidence": 0.0 },
    "clinic_address": {
       "street": { "value": null, "confidence": 0.0 },
       "city": { "value": null, "confidence": 0.0 },
       "state": { "value": null, "confidence": 0.0 },
       "zip": { "value": null, "confidence": 0.0 }
    },
    "clinic_phone": { "value": null, "original_text": null, "confidence": 0.0 },
    "clinic_fax": { "value": null, "original_text": null, "confidence": 0.0 },
    "signature_date_signed": { "value": null, "confidence": 0.0 },
    "signature_present": { "value": null, "confidence": 0.0 },
    "pecos_enrollment_present": { "value": null, "confidence": 0.0 }
  },

  "clinical_documentation": {
    "icd10_codes": [ { "code": null, "description": null, "confidence": 0.0 } ],
    "medical_necessity_summary": { "value": null, "confidence": 0.0 },
    "onset_or_injury_date": { "value": null, "confidence": 0.0 },
    "prior_treatments": { "value": null, "confidence": 0.0 },
    "face_to_face_documentation_present": { "value": null, "confidence": 0.0 }
  },

  "orders_dme_details": {
    "hcpcs_codes": [ { "code": null, "confidence": 0.0 } ],
    "item_descriptions": [ { "value": null, "confidence": 0.0 } ],
    "quantity_ordered": { "value": null, "confidence": 0.0 },
    "frequency_replacement": { "value": null, "confidence": 0.0 },
    "length_of_need": { "value": null, "confidence": 0.0 },
    "supply_start_date": { "value": null, "confidence": 0.0 },
    "place_of_service": { "value": null, "confidence": 0.0 },
    "serial_lot_number": { "value": null, "confidence": 0.0 }
  },

  "patient_financials": {
    "abn_or_notice_present": { "value": null, "confidence": 0.0 },
    "estimated_cost": { "value": null, "currency": "USD", "confidence": 0.0 },
    "patient_choice_option": { "value": null, "confidence": 0.0 },
    "aob_signed_dated": { "value": null, "confidence": 0.0 },
    "supplier_standards_ack_signed": { "value": null, "confidence": 0.0 },
    "hipaa_acknowledgement_present": { "value": null, "confidence": 0.0 }
  },

  "delivery_proof": {
    "proof_of_delivery_signed": { "value": null, "confidence": 0.0 },
    "pod_signed_date": { "value": null, "confidence": 0.0 },
    "pod_address": { "value": null, "confidence": 0.0 },
    "pod_item_list": { "value": null, "confidence": 0.0 },
    "courier_documentation_present": { "value": null, "confidence": 0.0 },
    "tracking_number": { "value": null, "confidence": 0.0 }
  },

  "administrative_tracking": {
    "internal_case_id": { "value": null, "confidence": 0.0 },
    "referral_source": { "value": null, "confidence": 0.0 },
    "prior_authorization_number": { "value": null, "confidence": 0.0 },
    "recertification_documentation_present": { "value": null, "confidence": 0.0 },
    "replacement_vs_new_notes": { "value": null, "confidence": 0.0 }
  },

  "compliance_checklists": {
    "medicare_dme_file": {
       "patient_demographics_with_mbi": { "value": null, "confidence": 0.0 },
       "medicare_card_copy_present": { "value": null, "confidence": 0.0 },
       "ordering_provider_info": { "value": null, "confidence": 0.0 },
       "dwo_signed_dated": { "value": null, "confidence": 0.0 },
       "face_to_face_note_present": { "value": null, "confidence": 0.0 },
       "icd10_linked_to_hcpcs": { "value": null, "confidence": 0.0 },
       "hcpcs_present": { "value": null, "confidence": 0.0 },
       "abn_signed_dated": { "value": null, "confidence": 0.0 },
       "aob_signed_dated": { "value": null, "confidence": 0.0 },
       "supplier_standards_ack_signed": { "value": null, "confidence": 0.0 },
       "pod_signed_date_present": { "value": null, "confidence": 0.0 },
       "serial_lot_number_logged": { "value": null, "confidence": 0.0 },
       "prior_auth_approval_present": { "value": null, "confidence": 0.0 }
    },
    "medicaid_dme_file": { /* same style booleans/confidence as needed */ },
    "commercial_dme_file": { /* same style booleans/confidence as needed */ },
    "workerscomp_dme_file": { /* same style booleans/confidence as needed */ }
  },

  "meta": {
    "document_type_guess": { "value": null, "confidence": 0.0 },
    "pages_checked": [1,2],
    "extraction_confidence": 0.0,
    "notes": null
  }
}

FINAL:
- Produce ONLY the JSON object (matching schema). Do not return any commentary.
- If no fields could be extracted at all, return the schema with all values null and confidence 0.0.

EXTRACTION GUIDELINES / TIPS:
- Use headings and neighboring text to decide scope (e.g., "Patient:", "DOB:", "Policy #", "NPI", "HCPCS", "ICD-10").
- Validate IDs (NPI=10 digits, ICD10 pattern, HCPCS pattern, MBI length ~11) but include value anyway if pattern fails; assign confidence appropriately.
- For signatures and checkboxes, assign confidence to reflect certainty of presence.
- For ambiguous or multiple candidates, populate `candidates` with value, confidence, and reason.
"""

human_prompt_doc_extraction = (
    "Here is the OCR Markdown content:\n"
    "{markdown_content}\n\n"
    "Now extract the information into this schema. "
    "Return ONLY valid JSON, with no extra text or formatting:\n"
    "{schema}\n"
)