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

#pdf_path = "/Users/yuvrajsingh/Documents/AI Development/Freelance/Parachute_Portal/docs/Generate_Pdfs/Purewick_Resupply_Agreement_OHC_Template.pdf"

def list_editable_fields(pdf_path):
    """
    Print all editable form field names from a PDF document.
    """
    try:
        doc = fitz.open(pdf_path)
        for page_num in range(len(doc)):
            page = doc[page_num]
            widgets = page.widgets()
            if widgets:
                for widget in widgets:
                    if widget.field_name:
                        print(widget.field_name)
        doc.close()
    except Exception as e:
        print(f"Error reading PDF: {str(e)}")

def _get_full_address(address_dict):
    """Helper method to create full address string from address dictionary"""
    if not isinstance(address_dict, dict):
        return ""
    
    address_parts = []
    components = ['street', 'city', 'state', 'zip']
    for component in components:
        if component in address_dict:
            value = address_dict[component]
            if isinstance(value, dict) and "value" in value:
                val = value["value"]
                if val is not None and str(val).strip():  # Only add non-empty values
                    address_parts.append(str(val))
            elif isinstance(value, str) and value.strip():  # Only add non-empty strings
                address_parts.append(value)
    
    return " ".join(address_parts) if address_parts else ""

def _convert_to_non_editable(input_path: str, output_path: str, dpi: int = 150) -> None:
    """
    Convert filled PDF to non-editable by rendering each page as an image.
    This completely removes all form fields and makes the PDF truly read-only.
    """
    try:
        # Open the filled PDF
        filled_doc = fitz.open(input_path)
        
        # Create a new empty PDF
        output_doc = fitz.open()
        
        # Convert each page to image and add to new PDF
        for page_num in range(len(filled_doc)):
            page = filled_doc[page_num]
            
            # Render page to high-quality image
            pix = page.get_pixmap(dpi=dpi)
            
            # Create new page with same dimensions
            new_page = output_doc.new_page(
                width=page.rect.width,
                height=page.rect.height
            )
            
            # Insert the rendered image
            new_page.insert_image(page.rect, pixmap=pix)
        
        # Save the non-editable PDF
        output_doc.save(output_path)
        output_doc.close()
        filled_doc.close()
        
        print(f"✅ Converted to non-editable image-based PDF")
        
    except Exception as e:
        print(f"⚠️ Error converting to non-editable: {e}")
        # If conversion fails, just copy the filled PDF
        import shutil
        shutil.copy(input_path, output_path)

def fill_patient_financial_responsibilty_template(pdf_path, extracted_data, output_path="filled_patient_financial_responsibilty_template.pdf"):
    """Standalone function to fill Patient Financial Responsibility Template"""
    try:
        doc = fitz.open(pdf_path)

        # Comprehensive field mapping for Patient Financial Responsibility Template
        field_map = {
            # Patient Information
            "full name": extracted_data.get("patient_information", {}).get("full_name", {}).get("value", ""),
            "date of birth": extracted_data.get("patient_information", {}).get("date_of_birth", {}).get("value", ""),
            "address": _get_full_address(extracted_data.get("patient_information", {}).get("address", {})),
            "phone": extracted_data.get("patient_information", {}).get("phone_numbers", [{}])[0].get("value", ""),
            
            # Insurance Information
            "primary insurance": extracted_data.get("insurance_billing", {}).get("primary_payer", {}).get("value", ""),
            "member id": extracted_data.get("insurance_billing", {}).get("policy_member_id", {}).get("value", ""),
            "group": extracted_data.get("insurance_billing", {}).get("group_number", {}).get("value", ""),
            "secondary insurance": extracted_data.get("insurance_billing", {}).get("secondary_insurance", {}).get("value", ""),
        }

        # Fill the form fields - using exact matching like CGM function
        filled_count = 0
        for page in doc:
            widgets = page.widgets()
            if not widgets:
                continue
            for w in widgets:
                if w.field_name in field_map:
                    value = field_map[w.field_name]
                    if value:
                        w.field_value = str(value)
                        try:
                            # Set font properties for better appearance
                            w.field_fontsize = 8  # Small font size
                            w.field_flags = w.field_flags | 0x00000002  # ReadOnly flag
                            w.field_display = 0  # Hide field display
                            w.field_text_color = (0, 0, 0)  # Black text
                            w.field_border_color = (0, 0, 0)  # Black border
                            w.field_border_width = 0.5  # Thin border
                        except:
                            pass
                        w.update()
                        filled_count += 1
                        print(f"✅ Filled '{w.field_name}' with '{value}' (font size: 8)")
                    else:
                        print(f"⚠️ No value for field '{w.field_name}'")
                else:
                    print(f"❌ No mapping for field: '{w.field_name}'")
        
        print(f"📊 Total fields filled: {filled_count}")

        # Save the filled PDF first
        temp_path = output_path.replace('.pdf', '_temp.pdf')
        doc.save(temp_path)
        doc.close()

        # Convert to non-editable by rendering to images
        _convert_to_non_editable(temp_path, output_path)

        # Clean up temp file
        import os
        try:
            os.unlink(temp_path)
        except:
            pass

        return output_path

    except Exception as e:
        print(f"Error filling Patient Financial Responsibility PDF: {e}")
        raise e

def fill_patient_intake_form(pdf_path, extracted_data, output_path="filled_patient_intake_form.pdf"):
    """
    Fill the Patient Intake Form - Non Medicare Intake Form with extracted data.
    
    Maps the extracted data from the schema to the PDF form fields:
    - last name, first name -> full_name
    - address -> address (street)
    - city -> address (city)
    - zip -> address (zip)
    - phone -> phone_numbers
    - date of birth -> date_of_birth
    - SSN -> ssn
    - supply start date -> supply_start_date
    - emergency name -> emergency_contact (name)
    - emergency phone -> emergency_contact (phone)
    - provider name -> provider_full_name
    - npi number -> npi_number
    - prescriber address -> clinic_address
    - prescriber phone -> clinic_phone
    - icd10 codes -> icd10_codes
    - policy member id -> policy_member_id
    - guarantor name -> guarantor (name)
    - item description and services needed -> item_descriptions
    - administrative date received -> internal_case_id (or date)
    - full name -> full_name
    - admission date -> onset_or_injury_date
    - phone number -> phone_numbers
    - item descriptions and hcpcs codes -> item_descriptions and hcpcs_codes
    """
    try:
        doc = fitz.open(pdf_path)

        # Helper function to safely get nested values
        def safe_get(data, path, default=""):
            """Safely navigate nested dictionary structure"""
            try:
                keys = path.split('.')
                result = data
                for key in keys:
                    if isinstance(result, dict) and key in result:
                        result = result[key]
                        if isinstance(result, dict) and "value" in result:
                            result = result["value"]
                    else:
                        return default
                # Handle None values and empty strings
                if result is None:
                    return default
                # Don't convert dicts or lists to strings - return as-is
                if isinstance(result, (dict, list)):
                    return result
                return str(result) if result else default
            except:
                return default

        # Helper function to get first phone number
        def get_first_phone(phone_list):
            """Get the first phone number from the phone_numbers array"""
            try:
                if isinstance(phone_list, list) and len(phone_list) > 0:
                    phone = phone_list[0]
                    if isinstance(phone, dict):
                        return phone.get("value", phone.get("original_text", ""))
                return ""
            except:
                return ""

        # Helper function to get address components
        def get_address_component(address_dict, component):
            """Get specific address component"""
            try:
                if isinstance(address_dict, dict) and component in address_dict:
                    comp = address_dict[component]
                    if isinstance(comp, dict) and "value" in comp:
                        return comp["value"]
                    return str(comp) if comp else ""
                return ""
            except:
                return ""

        # Helper function to format ICD10 codes
        def format_icd10_codes(icd10_list):
            """Format ICD10 codes into a readable string"""
            try:
                if isinstance(icd10_list, list):
                    codes = []
                    for code_obj in icd10_list:
                        if isinstance(code_obj, dict) and "code" in code_obj:
                            code = code_obj["code"]
                            if code:
                                codes.append(code)
                    return ", ".join(codes) if codes else ""
                return ""
            except:
                return ""

        # Helper function to format HCPCS codes
        def format_hcpcs_codes(hcpcs_list):
            """Format HCPCS codes into a readable string"""
            try:
                if isinstance(hcpcs_list, list):
                    codes = []
                    for code_obj in hcpcs_list:
                        if isinstance(code_obj, dict) and "code" in code_obj:
                            code = code_obj["code"]
                            if code:
                                codes.append(code)
                    return ", ".join(codes) if codes else ""
                return ""
            except:
                return ""

        # Helper function to format item descriptions
        def format_item_descriptions(items_list):
            """Format item descriptions into a readable string"""
            try:
                if isinstance(items_list, list):
                    descriptions = []
                    for item in items_list:
                        if isinstance(item, dict) and "value" in item:
                            desc = item["value"]
                            if desc:
                                descriptions.append(desc)
                        elif isinstance(item, str) and item:
                            descriptions.append(item)
                    return "; ".join(descriptions) if descriptions else ""
                return ""
            except:
                return ""

        # Helper function to get full name components
        def get_name_components(full_name):
            """Split full name into first and last name"""
            try:
                if full_name:
                    parts = full_name.strip().split()
                    if len(parts) >= 2:
                        first_name = parts[0]
                        last_name = " ".join(parts[1:])
                        return first_name, last_name
                    elif len(parts) == 1:
                        return parts[0], ""
                return "", ""
            except:
                return "", ""

        # Get full name and split it
        full_name = safe_get(extracted_data, "patient_information.full_name")
        first_name, last_name = get_name_components(full_name)

        # Get address components
        address_dict = safe_get(extracted_data, "patient_information.address", {})
        street = get_address_component(address_dict, "street")
        city = get_address_component(address_dict, "city")
        zip_code = get_address_component(address_dict, "zip")

        # Get state from address
        state = get_address_component(address_dict, "state")

        # Comprehensive field mapping for Patient Intake Form
        field_map = {
            # Patient Information
            "last name": last_name,
            "first name": first_name,
            "address": street,
            "city": city,
            "zip": zip_code,
            "phone": get_first_phone(safe_get(extracted_data, "patient_information.phone_numbers", [])),
            "date of birth": safe_get(extracted_data, "patient_information.date_of_birth"),
            "SSN": safe_get(extracted_data, "patient_information.ssn"),
            "supply start date": safe_get(extracted_data, "orders_dme_details.supply_start_date"),
            
            # Emergency Contact
            "emergency name": safe_get(extracted_data, "patient_information.emergency_contact.name"),
            "emergency phone": safe_get(extracted_data, "patient_information.emergency_contact.phone"),
            
            # Provider Information
            "provider name": safe_get(extracted_data, "provider_prescriber.provider_full_name"),
            "npi number": safe_get(extracted_data, "provider_prescriber.npi_number"),
            "prescriber address": _get_full_address(safe_get(extracted_data, "provider_prescriber.clinic_address", {})),
            "prescriber phone": safe_get(extracted_data, "provider_prescriber.clinic_phone"),
            
            # Clinical Information
            "icd10 codes": format_icd10_codes(safe_get(extracted_data, "clinical_documentation.icd10_codes", [])),
            
            # Insurance Information
            "policy member id": safe_get(extracted_data, "insurance_billing.policy_member_id"),
            "guarantor name": safe_get(extracted_data, "insurance_billing.guarantor.name"),
            
            # DME Details
            "item description and services needed": format_item_descriptions(safe_get(extracted_data, "orders_dme_details.item_descriptions", [])),
            
            # Administrative
            "administrative date received": safe_get(extracted_data, "administrative_tracking.internal_case_id"),
            "full name": full_name,  # Duplicate field for full name
            "admission date": safe_get(extracted_data, "clinical_documentation.onset_or_injury_date"),
            "phone number": get_first_phone(safe_get(extracted_data, "patient_information.phone_numbers", [])),  # Duplicate phone field
            "item descriptions and hcpcs codes": f"{format_item_descriptions(safe_get(extracted_data, 'orders_dme_details.item_descriptions', []))} - {format_hcpcs_codes(safe_get(extracted_data, 'orders_dme_details.hcpcs_codes', []))}",
            
            # Special field mapping for state
            "Text-ca7ONFbtHI": state,
        }

        # Fill the form fields
        filled_count = 0
        for page in doc:
            widgets = page.widgets()
            if not widgets:
                continue
            for w in widgets:
                if w.field_name in field_map:
                    value = field_map[w.field_name]
                    if value:
                        # Set the field value
                        w.field_value = str(value)
                        
                        # Set font size to 9pt (readable and professional)
                        w.text_fontsize = 9
                        
                        # Update the widget to apply changes
                        w.update()
                        
                        filled_count += 1
                        print(f"✅ Filled '{w.field_name}' with '{value}'")
                    else:
                        print(f"⚠️ No value for field '{w.field_name}'")
                else:
                    print(f"❌ No mapping for field: '{w.field_name}'")
        
        print(f"📊 Total fields filled: {filled_count}")

        # Save the filled PDF
        doc.save(output_path)
        doc.close()

        return output_path

    except Exception as e:
        print(f"Error filling Patient Intake Form PDF: {e}")
        raise e

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
                        try:
                            # Set font properties for better appearance
                            w.field_fontsize = 8  # Small font size
                            w.field_text_color = (0, 0, 0)  # Black text
                        except:
                            pass
                        w.update()

        doc.save(output_path)
        doc.close()
        print(f"PDF filled and saved as {output_path}")

    except Exception as e:
        print(f"Error filling PDF: {e}")

def fill_patient_authorization_form(pdf_path, extracted_data, output_path="filled_patient_authorization_form.pdf"):
    """
    Fill the Patient Authorization Form with extracted data.
    
    Maps the extracted data from the schema to the PDF form fields:
    - full name -> patient_information.full_name
    - address -> patient_information.address (full address string)
    - City -> patient_information.address.city
    - State -> patient_information.address.state
    - ZIP Code -> patient_information.address.zip
    - Phone Number -> patient_information.phone_numbers[0]
    - Email Address -> patient_information.email
    """
    try:
        doc = fitz.open(pdf_path)

        # Helper function to safely get nested values
        def safe_get(data, path, default=""):
            """Safely navigate nested dictionary structure"""
            try:
                keys = path.split('.')
                result = data
                for key in keys:
                    if isinstance(result, dict) and key in result:
                        result = result[key]
                        if isinstance(result, dict) and "value" in result:
                            result = result["value"]
                    else:
                        return default
                # Handle None values and empty strings
                if result is None:
                    return default
                # Don't convert dicts or lists to strings - return as-is
                if isinstance(result, (dict, list)):
                    return result
                return str(result) if result else default
            except:
                return default

        # Helper function to get first phone number
        def get_first_phone(phone_list):
            """Get the first phone number from the phone_numbers array"""
            try:
                if isinstance(phone_list, list) and len(phone_list) > 0:
                    phone = phone_list[0]
                    if isinstance(phone, dict):
                        value = phone.get("value") or phone.get("original_text", "")
                        return str(value) if value else ""
                return ""
            except:
                return ""

        # Helper function to get address components
        def get_address_component(address_dict, component):
            """Get specific address component"""
            try:
                if isinstance(address_dict, dict) and component in address_dict:
                    comp = address_dict[component]
                    if isinstance(comp, dict) and "value" in comp:
                        value = comp["value"]
                        return str(value) if value is not None else ""
                    return str(comp) if comp is not None else ""
                return ""
            except:
                return ""

        # Get address components
        address_dict = safe_get(extracted_data, "patient_information.address", {})
        city = get_address_component(address_dict, "city")
        state = get_address_component(address_dict, "state")
        zip_code = get_address_component(address_dict, "zip")

        # Comprehensive field mapping for Patient Authorization Form
        field_map = {
            # Patient Information
            "full name": safe_get(extracted_data, "patient_information.full_name"),
            "address": _get_full_address(safe_get(extracted_data, "patient_information.address", {})),
            "City": city,
            "State": state,
            "ZIP Code": zip_code,
            "Phone Number": get_first_phone(safe_get(extracted_data, "patient_information.phone_numbers", [])),
            "Email Address": safe_get(extracted_data, "patient_information.email"),
        }

        filled_count = 0
        for page in doc:
            widgets = page.widgets()
            if not widgets:
                continue
            for w in widgets:
                if w.field_name in field_map:
                    value = field_map[w.field_name]
                    if value:
                        w.field_value = str(value)
                        try:
                            # Set font properties for better appearance
                            w.text_fontsize = 10  # Font size
                            w.field_text_color = (0, 0, 0)  # Black text
                        except:
                            pass
                        w.update()
                        filled_count += 1
                        print(f"✅ Filled '{w.field_name}' with '{value}'")
                    else:
                        print(f"⚠️ No value for field '{w.field_name}'")
                else:
                    print(f"❌ No mapping for field: '{w.field_name}'")

        print(f"📊 Total fields filled: {filled_count}")

        doc.save(output_path)
        doc.close()
        print(f"✅ PDF filled and saved as {output_path}. Filled {filled_count} fields.")

    except Exception as e:
        print(f"Error filling Patient Authorization Form PDF: {e}")
        raise e

def fill_patient_service_agreement(pdf_path, extracted_data, output_path="filled_patient_service_agreement.pdf"):
    try:
        doc = fitz.open(pdf_path)

        # Helper function to get insurance ID with fallback
        def get_insurance_id():
            """Get insurance ID - try mbi_or_medicaid_id first, fallback to policy_member_id"""
            try:
                mbi = extracted_data.get("insurance_billing", {}).get("mbi_or_medicaid_id", {})
                if isinstance(mbi, dict):
                    mbi_value = mbi.get("value")
                    if mbi_value:
                        return str(mbi_value)
                
                # Fallback to policy_member_id
                policy = extracted_data.get("insurance_billing", {}).get("policy_member_id", {})
                if isinstance(policy, dict):
                    policy_value = policy.get("value")
                    if policy_value:
                        return str(policy_value)
                
                return ""
            except:
                return ""

        # Helper function to get first name
        def get_first_name():
            """Extract first name from full name"""
            try:
                full_name = extracted_data.get("patient_information", {}).get("full_name", {}).get("value", "")
                if full_name:
                    return full_name.split()[0]
                return ""
            except:
                return ""

        # Field mapping with fallback logic
        field_map = {
            "full name": extracted_data.get("patient_information", {}).get("full_name", {}).get("value", ""),
            "first name": get_first_name(),
            "insurance id": get_insurance_id()
        }

        filled_count = 0
        for page in doc:
            widgets = page.widgets()
            if not widgets:
                continue
            for w in widgets:
                if w.field_name in field_map:
                    value = field_map[w.field_name]
                    if value:
                        w.field_value = str(value)
                        try:
                            # Set font properties for better appearance
                            w.text_fontsize = 8  # Small font size
                            w.field_text_color = (0, 0, 0)  # Black text
                        except:
                            pass
                        w.update()
                        filled_count += 1
                        print(f"✅ Filled '{w.field_name}' with '{value}'")

        doc.save(output_path)
        doc.close()
        print(f"✅ PDF filled and saved as {output_path}. Filled {filled_count} fields.")

    except Exception as e:
        print(f"Error filling PDF: {e}")
        raise e


# Example usage
if __name__ == "__main__":
    # Example 1: List all editable fields in a PDF
    pdf_path = "/Users/yuvrajsingh/Documents/AI Development/Freelance/Parachute_Portal/docs/Generate_Pdfs/Non medicare/Patient Service Agreement.pdf"
    #fields = list_editable_fields(pdf_path)
    fill_patient_service_agreement(pdf_path, results)
    
    #fill_patient_intake_form(pdf_path, results)
    #fill_patient_financial_responsibilty_template(pdf_path, results)
