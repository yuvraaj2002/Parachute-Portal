import fitz  # PyMuPDF

results = {
  "patient_information": {
    "full_name": { "value": "Kimberly Hofstede", "confidence": 0.95 },
    "date_of_birth": { "value": "1966-08-06", "confidence": 0.95 },
    "gender": { "value": "Female", "confidence": 0.9 },
    "height": { "value": "5'6\"", "confidence": 0.9 },
    "weight": { "value": "140 lbs", "confidence": 0.9 },
    "ssn": { "value": "123-45-6789", "confidence": 0.9 },
    "address": {
      "street": { "value": "123 Main St", "confidence": 0.9 },
      "city": { "value": "The Woodlands", "confidence": 0.95 },
      "state": { "value": "TX", "confidence": 0.95 },
      "zip": { "value": "77380", "confidence": 0.95 }
    },
    "phone_numbers": [
      { "value": "2812986742", "original_text": "(281) 298-6742", "confidence": 0.9 },
      { "value": "2814353667", "original_text": "(281) 435-3667", "confidence": 0.9 }
    ],
    "email": { "value": "kim.hofstede@example.com", "confidence": 0.9 },
    "emergency_contact": {
      "name": { "value": "John Hofstede", "confidence": 0.9 },
      "relation": { "value": "Husband", "confidence": 0.9 },
      "phone": { "value": "2815551122", "original_text": "(281) 555-1122", "confidence": 0.9 }
    },
    "copy_of_id_present": { "value": "Yes", "confidence": 0.85 }
  },

  "insurance_billing": {
    "primary_payer": { "value": "Medicare", "confidence": 0.95 },
    "mbi_or_medicaid_id": { "value": "1EG4TE5MK73", "confidence": 0.9 },
    "policy_member_id": { "value": "PM12345678", "confidence": 0.9 },
    "group_number": { "value": "GRP89012", "confidence": 0.85 },
    "bin_pcn": { "value": "BIN12345 / PCN67890", "confidence": 0.85 },
    "secondary_insurance": { "value": "Aetna", "confidence": 0.8 },
    "workers_comp_claim": { "value": "No", "confidence": 0.9 },
    "guarantor": {
      "name": { "value": "Kimberly Hofstede", "confidence": 0.9 },
      "relation": { "value": "Self", "confidence": 0.9 },
      "contact": { "value": "2812986742", "original_text": "(281) 298-6742", "confidence": 0.9 }
    }
  },

  "provider_prescriber": {
    "provider_full_name": { "value": "Dr. Sarah Lee", "confidence": 0.95 },
    "npi_number": { "value": "1234567890", "confidence": 0.95 },
    "dea_number": { "value": "AB1234567", "confidence": 0.85 },
    "specialty": { "value": "Pulmonology", "confidence": 0.9 },
    "clinic_facility_name": { "value": "Houston Medical Center", "confidence": 0.9 },
    "clinic_address": {
       "street": { "value": "200 Wellness Blvd", "confidence": 0.9 },
       "city": { "value": "Houston", "confidence": 0.9 },
       "state": { "value": "TX", "confidence": 0.9 },
       "zip": { "value": "77002", "confidence": 0.9 }
    },
    "clinic_phone": { "value": "7135559876", "original_text": "(713) 555-9876", "confidence": 0.9 },
    "clinic_fax": { "value": "7135551234", "original_text": "(713) 555-1234", "confidence": 0.9 },
    "signature_date_signed": { "value": "2025-09-20", "confidence": 0.9 },
    "signature_present": { "value": "Yes", "confidence": 0.9 },
    "pecos_enrollment_present": { "value": "Yes", "confidence": 0.85 }
  },

  "clinical_documentation": {
    "icd10_codes": [
      { "code": "J44.9", "description": "Chronic obstructive pulmonary disease, unspecified", "confidence": 0.9 },
      { "code": "G47.33", "description": "Obstructive sleep apnea", "confidence": 0.9 }
    ],
    "medical_necessity_summary": { "value": "Patient requires continuous oxygen therapy.", "confidence": 0.9 },
    "onset_or_injury_date": { "value": "2024-05-15", "confidence": 0.85 },
    "prior_treatments": { "value": "Inhalers, nebulizer therapy", "confidence": 0.85 },
    "face_to_face_documentation_present": { "value": "Yes", "confidence": 0.9 }
  },

  "orders_dme_details": {
    "hcpcs_codes": [
      { "code": "E1390", "confidence": 0.9 },
      { "code": "A7003", "confidence": 0.9 }
    ],
    "item_descriptions": [
      { "value": "Oxygen concentrator", "confidence": 0.9 },
      { "value": "Nebulizer tubing", "confidence": 0.9 }
    ],
    "quantity_ordered": { "value": "1 concentrator, 3 nebulizer sets", "confidence": 0.9 },
    "frequency_replacement": { "value": "Every 3 months", "confidence": 0.85 },
    "length_of_need": { "value": "12 months", "confidence": 0.9 },
    "supply_start_date": { "value": "2025-10-01", "confidence": 0.9 },
    "place_of_service": { "value": "Home", "confidence": 0.9 },
    "serial_lot_number": { "value": "SN123456789", "confidence": 0.9 }
  },

  "patient_financials": {
    "abn_or_notice_present": { "value": "Yes", "confidence": 0.9 },
    "estimated_cost": { "value": "1200.00", "currency": "USD", "confidence": 0.9 },
    "patient_choice_option": { "value": "Option 1 - Medicare", "confidence": 0.85 },
    "aob_signed_dated": { "value": "2025-09-22", "confidence": 0.9 },
    "supplier_standards_ack_signed": { "value": "Yes", "confidence": 0.9 },
    "hipaa_acknowledgement_present": { "value": "Yes", "confidence": 0.9 }
  },

  "delivery_proof": {
    "proof_of_delivery_signed": { "value": "Yes", "confidence": 0.9 },
    "pod_signed_date": { "value": "2025-09-25", "confidence": 0.9 },
    "pod_address": { "value": "123 Main St, The Woodlands, TX 77380", "confidence": 0.9 },
    "pod_item_list": { "value": "Oxygen concentrator, nebulizer tubing", "confidence": 0.9 },
    "courier_documentation_present": { "value": "Yes", "confidence": 0.9 },
    "tracking_number": { "value": "1Z999AA10123456784", "confidence": 0.95 }
  },

  "administrative_tracking": {
    "internal_case_id": { "value": "CASE-2025-00123", "confidence": 0.95 },
    "referral_source": { "value": "Dr. Sarah Lee", "confidence": 0.9 },
    "prior_authorization_number": { "value": "AUTH-456789", "confidence": 0.9 },
    "recertification_documentation_present": { "value": "Yes", "confidence": 0.9 },
    "replacement_vs_new_notes": { "value": "Replacement concentrator for broken device", "confidence": 0.85 }
  },

  "compliance_checklists": {
    "medicare_dme_file": {
       "patient_demographics_with_mbi": { "value": "1EG4TE5MK73", "confidence": 0.9 },
       "medicare_card_copy_present": { "value": "Yes", "confidence": 0.9 },
       "ordering_provider_info": { "value": "Dr. Sarah Lee, NPI 1234567890", "confidence": 0.9 },
       "dwo_signed_dated": { "value": "2025-09-20", "confidence": 0.9 },
       "face_to_face_note_present": { "value": "Yes", "confidence": 0.9 },
       "icd10_linked_to_hcpcs": { "value": "Yes", "confidence": 0.85 },
       "hcpcs_present": { "value": "Yes", "confidence": 0.9 },
       "abn_signed_dated": { "value": "2025-09-22", "confidence": 0.9 },
       "aob_signed_dated": { "value": "2025-09-22", "confidence": 0.9 },
       "supplier_standards_ack_signed": { "value": "Yes", "confidence": 0.9 },
       "pod_signed_date_present": { "value": "2025-09-25", "confidence": 0.9 },
       "serial_lot_number_logged": { "value": "SN123456789", "confidence": 0.9 },
       "prior_auth_approval_present": { "value": "Yes", "confidence": 0.9 }
    },
    "medicaid_dme_file": {
      "value": "N/A",
      "confidence": 0.0
    },
    "commercial_dme_file": {
      "value": "N/A",
      "confidence": 0.0
    },
    "workerscomp_dme_file": {
      "value": "N/A",
      "confidence": 0.0
    }
  },

  "meta": {
    "document_type_guess": { "value": "DME Intake Form", "confidence": 0.9 },
    "pages_checked": [1, 2],
    "extraction_confidence": 0.92,
    "notes": "Sample JSON populated with test values for pipeline validation"
  }
}

pdf_path = "/Users/yuvrajsingh/Documents/AI Development/Freelance/Parachute_Portal/docs/Generate_Pdfs/Purewick_Resupply_Agreement_OHC_Template.pdf"

def fill_purewick_resupply_agreement(pdf_path, extracted_data, output_path="filled_purewick.pdf"):
    try:
        doc = fitz.open(pdf_path)

        # Explicit mapping for ONLY 3 fields
        field_map = {
            "full name": extracted_data["patient_information"]["full_name"]["value"],
            "date of birth": extracted_data["patient_information"]["date_of_birth"]["value"],
            "insurance id": extracted_data["insurance_billing"]["mbi_or_medicaid_id"]["value"],
        }

        for page in doc:
            widgets = page.widgets()
            if not widgets:
                continue
            for w in widgets:
                if w.field_name in field_map:
                    value = field_map[w.field_name]
                    if value:
                        w.field_value = str(value)
                        w.update()

        doc.save(output_path)
        doc.close()
        print(f"PDF filled and saved as {output_path}")

    except Exception as e:
        print(f"Error filling PDF: {e}")


# Example usage
if __name__ == "__main__":
    fill_purewick_resupply_agreement(pdf_path, results)
