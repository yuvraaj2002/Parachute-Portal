import fitz  # PyMuPDF
import json

# -------------------------
# Paths
# -------------------------
template_path = "/Users/yuvrajsingh/Documents/AI Development/Freelance/Parachute_Portal/docs/Generate_Pdfs/Non Medicare DME Intake Form_Template.pdf"
output_path = "/Users/yuvrajsingh/Documents/AI Development/Freelance/Parachute_Portal/docs/Generate_Pdfs/Filled_DME_Form.pdf"

# -------------------------
# Example extracted JSON schema with values
# -------------------------
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

# -------------------------
# Mapping PDF fields → JSON schema keys
# -------------------------
field_map = {
    # Patient Information
    "patient last name": "patient_information.full_name",  # Will extract last name from full name
    "patient first name": "patient_information.full_name",  # Will extract first name from full name
    "patient full name": "patient_information.full_name",
    "patient address": "patient_information.address",  # Will create full address string
    "patient address city": "patient_information.address.city",
    "patient address state": "patient_information.address.state",
    "patient address zip": "patient_information.address.zip",
    "patient phone number": "patient_information.phone_numbers[0].value",
    "patient date of birth": "patient_information.date_of_birth",
    "patient email": "patient_information.email",
    "emergency contact name": "patient_information.emergency_contact.name",
    "emergency phone": "patient_information.emergency_contact.phone",
    "patient height": "patient_information.height",
    "patient weight": "patient_information.weight",
    "SSN": "patient_information.ssn",

    # Provider / Prescriber
    "provider_full_name": "provider_prescriber.provider_full_name",
    "provider_prescriber.provider_full_name": "provider_prescriber.provider_full_name",
    "npi_number": "provider_prescriber.npi_number",
    "provider_prescriber.npi_number": "provider_prescriber.npi_number",
    "clinic_address": "provider_prescriber.clinic_address.street",
    "clinic_phone": "provider_prescriber.clinic_phone",
    "provider_prescriber.clinic_phone": "provider_prescriber.clinic_phone",

    # Clinical Documentation
    "icd10_codes": "clinical_documentation.icd10_codes[0].code",
    "clinical_documentation.icd10_codes": "clinical_documentation.icd10_codes[0].code",

    # Insurance / Billing
    "insurance primary payer": "insurance_billing.primary_payer",
    "insurance policy id": "insurance_billing.policy_member_id",
    "insurance group number": "insurance_billing.group_number",
    "insurance secondary payer": "insurance_billing.secondary_insurance",

    # Orders / Equipment
    "Equ pment  Serv ces Needed": "orders_dme_details.item_descriptions[0].value",
    "item descriptions": "orders_dme_details.item_descriptions[0].value",

    # Additional fields that might be in the PDF
    "Source": "administrative_tracking.referral_source",
    "Admission Date": "orders_dme_details.supply_start_date",
    
    # Insurance fields that might have different names
    "1": "insurance_billing.primary_payer",
    "2": "insurance_billing.secondary_insurance",
    "cy": "insurance_billing.group_number",
    "cy_2": "insurance_billing.group_number",
    "Address_3": "provider_prescriber.clinic_address.street",
    "Address_4": "provider_prescriber.clinic_address.street",
    "Phone_4": "provider_prescriber.clinic_phone",
    "Phone_5": "provider_prescriber.clinic_phone",
    "nsured": "insurance_billing.policy_member_id",
    "nsured_2": "insurance_billing.policy_member_id",
    "rth_2": "patient_information.date_of_birth",
    "rth_3": "patient_information.date_of_birth"
}

# -------------------------
# Helper: fetch nested value from dict using dot path
# -------------------------
def get_value_from_schema(data, path):
    try:
        parts = path.replace("]", "").split(".")
        val = data
        for part in parts:
            if "[" in part:  # handle list like icd10_codes[0]
                field, idx = part.split("[")
                val = val[field][int(idx)]
            else:
                val = val[part]
        if isinstance(val, dict) and "value" in val:
            return val["value"]
        if isinstance(val, dict) and "code" in val:
            return val["code"]
        return val
    except Exception:
        return None

# -------------------------
# Special handlers for name extraction
# -------------------------
def get_first_name(full_name):
    """Extract first name from full name"""
    if isinstance(full_name, dict) and "value" in full_name:
        full_name = full_name["value"]
    if isinstance(full_name, str):
        name_parts = full_name.split()
        return name_parts[0] if name_parts else ""
    return ""

def get_last_name(full_name):
    """Extract last name from full name"""
    if isinstance(full_name, dict) and "value" in full_name:
        full_name = full_name["value"]
    if isinstance(full_name, str):
        name_parts = full_name.split()
        return name_parts[-1] if name_parts else ""
    return ""

def get_full_address(address_dict):
    """Extract complete address string from address dictionary"""
    if not isinstance(address_dict, dict):
        return ""
    
    address_parts = []
    
    # Extract values from address components
    components = ['street', 'city', 'state', 'zip']
    for component in components:
        if component in address_dict:
            value = address_dict[component]
            if isinstance(value, dict) and "value" in value:
                address_parts.append(value["value"])
            elif isinstance(value, str):
                address_parts.append(value)
    
    # Join all parts with spaces
    return " ".join(address_parts) if address_parts else ""

def set_widget_font_size(widget, font_size=12):
    """Try multiple methods to set consistent font size for a widget"""
    methods_tried = []
    
    try:
        # Method 1: Direct font size setting
        widget.field_fontsize = font_size
        methods_tried.append("field_fontsize")
    except:
        pass
    
    try:
        # Method 2: Set font family
        widget.field_font = "helv"
        methods_tried.append("field_font")
    except:
        pass
    
    try:
        # Method 3: Try to modify the appearance dictionary
        if hasattr(widget, 'field_display') and widget.field_display:
            # Try to set font size in display properties
            methods_tried.append("field_display")
    except:
        pass
    
    try:
        # Method 4: Set text properties
        if hasattr(widget, 'field_text_maxlen'):
            widget.field_text_maxlen = len(str(widget.field_value)) + 20
            methods_tried.append("text_maxlen")
    except:
        pass
    
    try:
        # Method 5: Force field flags
        if hasattr(widget, 'field_flags'):
            widget.field_flags = widget.field_flags | 0x00000002
            methods_tried.append("field_flags")
    except:
        pass
    
    return methods_tried

# -------------------------
# Fill PDF fields using PyMuPDF
# -------------------------
print("📄 Loading PDF template...")

# Open the PDF
doc = fitz.open(template_path)
print(f"📄 PDF loaded with {len(doc)} pages")

# Get form fields
form_fields = {}
for page_num in range(len(doc)):
    page = doc[page_num]
    widgets = page.widgets()
    for widget in widgets:
        if widget.field_name:
            form_fields[widget.field_name] = widget.field_value
            print(f"   Field: '{widget.field_name}' = '{widget.field_value}'")

print(f"🔍 Found {len(form_fields)} form fields")

# Fill the form fields
filled_count = 0
for field_name, schema_path in field_map.items():
    value = get_value_from_schema(results, schema_path)
    
    # Special handling for name extraction
    if field_name == "patient first name" and value:
        value = get_first_name(value)
    elif field_name == "patient last name" and value:
        value = get_last_name(value)
    elif field_name == "patient address" and value:
        value = get_full_address(value)
    
    if value:
        # Find and fill the field
        for page_num in range(len(doc)):
            page = doc[page_num]
            widgets = page.widgets()
            for widget in widgets:
                if widget.field_name == field_name:
                    widget.field_value = str(value)
                    
                    # Set font size and appearance for better readability
                    methods_used = set_widget_font_size(widget, 12)
                    widget.update()
                    
                    if methods_used:
                        print(f"✅ Filled '{field_name}' with '{value}' (font: 12pt, methods: {', '.join(methods_used)})")
                    else:
                        print(f"✅ Filled '{field_name}' with '{value}' (default font)")
                    
                    filled_count += 1
                    break

print(f"\n📊 Filled {filled_count} fields")

# -------------------------
# Save filled PDF
# -------------------------
print(f"💾 Saving filled PDF to: {output_path}")
doc.save(output_path)
doc.close()

print("✅ PDF saved successfully!")

# -------------------------
# Verify the filled PDF
# -------------------------
print("\n🔍 Verifying filled PDF...")
doc_filled = fitz.open(output_path)

filled_count_verify = 0
for page_num in range(len(doc_filled)):
    page = doc_filled[page_num]
    widgets = page.widgets()
    for widget in widgets:
        if widget.field_name and widget.field_value and widget.field_value != '':
            filled_count_verify += 1
            print(f"✅ '{widget.field_name}' = '{widget.field_value}'")

print(f"\n📊 Verified: {filled_count_verify} fields have values")
doc_filled.close()
