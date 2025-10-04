import os
import base64
import pypandoc
import fitz  # PyMuPDF
import tempfile
import logging
from datetime import datetime
from mistralai import Mistral
from config import settings
from services.aws_service import file_handler
from models.database_models import GeneratedDocument

logger = logging.getLogger(__name__)

class PdfProcessor:
    def __init__(self):
        # You can set the API key via argument or environment variable
        self.api_key = settings.mistral_api_key
        if not self.api_key:
            raise ValueError("Please set the mistral_api_key environment variable or provide an API key.")
        self.client = Mistral(api_key=self.api_key)

    def extract_text_from_pdf(self, pdf_path):
        """
        Extracts text from a local PDF using Mistral OCR.
        Returns the OCR response (including markdown text).
        """
        # Read and Base64-encode the PDF
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()
        base64_pdf = base64.b64encode(pdf_bytes).decode("utf-8")

        # Call OCR on the Base64-encoded PDF
        ocr_response = self.client.ocr.process(
            model="mistral-ocr-latest",
            document={
                "type": "document_url",
                "document_url": f"data:application/pdf;base64,{base64_pdf}"
            },
            include_image_base64=False  # Set to True if you need embedded images
        )

        return ocr_response

    
    def fill_purewick_resupply_agreement(self, pdf_path, extracted_data, output_path="filled_purewick.pdf"):
        try:
            doc = fitz.open(pdf_path)

            field_map = {
                "full name": extracted_data.get("patient_information", {}).get("full_name", {}).get("value", ""),
                "date of birth": extracted_data.get("patient_information", {}).get("date_of_birth", {}).get("value", ""),
                "insurance id": extracted_data.get("insurance_billing", {}).get("mbi_or_medicaid_id", {}).get("value", ""),
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
                                w.field_flags = w.field_flags | 0x00000002  # ReadOnly flag
                                w.field_display = 0  # Hide field display
                            except:
                                pass
                            w.update()

            temp_path = output_path.replace('.pdf', '_temp.pdf')
            doc.save(temp_path)
            doc.close()

            self._convert_to_non_editable(temp_path, output_path)

            import os
            try:
                os.unlink(temp_path)
            except:
                pass

            return output_path

        except Exception as e:
            raise e

    def fill_patient_financial_responsibilty_template(self, pdf_path, extracted_data, output_path="filled_patient_financial_responsibilty_template.pdf"):
        try:
            doc = fitz.open(pdf_path)

            # Comprehensive field mapping for Patient Financial Responsibility Template
            field_map = {
                # Patient Information
                "full name": extracted_data.get("patient_information", {}).get("full_name", {}).get("value", ""),
                "date of birth": extracted_data.get("patient_information", {}).get("date_of_birth", {}).get("value", ""),
                "address": self._get_full_address(extracted_data.get("patient_information", {}).get("address", {})),
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
                                w.field_flags = w.field_flags | 0x00000002  # ReadOnly flag
                                w.field_display = 0  # Hide field display
                            except:
                                pass
                            w.update()
                            filled_count += 1

            # Save the filled PDF first
            temp_path = output_path.replace('.pdf', '_temp.pdf')
            doc.save(temp_path)
            doc.close()
            
            # Convert to non-editable by rendering to images
            self._convert_to_non_editable(temp_path, output_path)
            
            # Clean up temp file
            import os
            try:
                os.unlink(temp_path)
            except:
                pass
            
            return output_path

        except Exception as e:
            raise e

    def fill_cgm_resupply_agreement_form(self, pdf_path, extracted_data, output_path="filled_cgm_resupply_agreement.pdf"):
        try:
            doc = fitz.open(pdf_path)

            field_map = {
                "full name": extracted_data.get("patient_information", {}).get("full_name", {}).get("value", ""),
                "date of birth": extracted_data.get("patient_information", {}).get("date_of_birth", {}).get("value", ""),
                "insurance id": extracted_data.get("insurance_billing", {}).get("mbi_or_medicaid_id", {}).get("value", ""),
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
                                w.field_flags = w.field_flags | 0x00000002  # ReadOnly flag
                                w.field_display = 0  # Hide field display
                            except:
                                pass
                            w.update()

            temp_path = output_path.replace('.pdf', '_temp.pdf')
            doc.save(temp_path)
            doc.close()

            self._convert_to_non_editable(temp_path, output_path)

            import os
            try:
                os.unlink(temp_path)
            except:
                pass

            return output_path

        except Exception as e:
            raise e

    def fill_non_medicare_dme_intake_form(self, pdf_path, extracted_data, output_path="filled_non_medicare_dme_intake_form.pdf"):
        try:
            doc = fitz.open(pdf_path)

            field_map = {
                # Patient Information
                "full name": extracted_data.get("patient_information", {}).get("full_name", {}).get("value", ""),
                "patient name": extracted_data.get("patient_information", {}).get("full_name", {}).get("value", ""),
                "name": extracted_data.get("patient_information", {}).get("full_name", {}).get("value", ""),
                "date of birth": extracted_data.get("patient_information", {}).get("date_of_birth", {}).get("value", ""),
                "dob": extracted_data.get("patient_information", {}).get("date_of_birth", {}).get("value", ""),
                "birth date": extracted_data.get("patient_information", {}).get("date_of_birth", {}).get("value", ""),
                "phone": extracted_data.get("patient_information", {}).get("phone_numbers", [{}])[0].get("value", ""),
                "phone number": extracted_data.get("patient_information", {}).get("phone_numbers", [{}])[0].get("value", ""),
                "email": extracted_data.get("patient_information", {}).get("email", {}).get("value", ""),
                "address": self._get_full_address(extracted_data.get("patient_information", {}).get("address", {})),
                
                # Insurance Information
                "insurance id": extracted_data.get("insurance_billing", {}).get("mbi_or_medicaid_id", {}).get("value", ""),
                "insurance number": extracted_data.get("insurance_billing", {}).get("mbi_or_medicaid_id", {}).get("value", ""),
                "policy number": extracted_data.get("insurance_billing", {}).get("policy_member_id", {}).get("value", ""),
                "group number": extracted_data.get("insurance_billing", {}).get("group_number", {}).get("value", ""),
                "primary payer": extracted_data.get("insurance_billing", {}).get("primary_payer", {}).get("value", ""),
                
                # Provider Information
                "provider name": extracted_data.get("provider_prescriber", {}).get("provider_full_name", {}).get("value", ""),
                "doctor name": extracted_data.get("provider_prescriber", {}).get("provider_full_name", {}).get("value", ""),
                "npi": extracted_data.get("provider_prescriber", {}).get("npi_number", {}).get("value", ""),
                "clinic phone": extracted_data.get("provider_prescriber", {}).get("clinic_phone", {}).get("value", ""),
                
                # Clinical Information
                "icd10": extracted_data.get("clinical_documentation", {}).get("icd10_codes", [{}])[0].get("code", ""),
                "diagnosis": extracted_data.get("clinical_documentation", {}).get("icd10_codes", [{}])[0].get("code", ""),
                "hcpcs": extracted_data.get("orders_dme_details", {}).get("hcpcs_codes", [{}])[0].get("code", ""),
                "equipment": extracted_data.get("orders_dme_details", {}).get("item_descriptions", [{}])[0].get("value", ""),
            }

            # Fill the form fields
            filled_count = 0
            for page in doc:
                widgets = page.widgets()
                if not widgets:
                    continue
                for w in widgets:
                     if w.field_name and w.field_name.lower() in field_map:
                         value = field_map[w.field_name.lower()]
                         if value:
                             w.field_value = str(value)
                             
                             # Try to hide field borders/placeholders
                             try:
                                 # Set field flags to hide borders
                                 w.field_flags = w.field_flags | 0x00000002  # ReadOnly flag
                                 # Try to set appearance to hide borders
                                 w.field_display = 0  # Hide field display
                             except:
                                 pass
                             
                             w.update()
                             filled_count += 1
                             print(f"✅ Filled '{w.field_name}' with '{value}'")

            # Save the filled PDF first
            print(f"💾 Saving filled PDF...")
            temp_path = output_path.replace('.pdf', '_temp.pdf')
            doc.save(temp_path)
            doc.close()
            
            # Convert to non-editable by rendering to images
            print(f"🔒 Converting to non-editable format...")
            self._convert_to_non_editable(temp_path, output_path)
            
            # Clean up temp file
            import os
            try:
                os.unlink(temp_path)
            except:
                pass
            
            print(f"✅ PDF filled and made non-editable! Filled {filled_count} fields.")
            return output_path

        except Exception as e:
            print(f"Error filling generic PDF: {e}")
            raise e

    def fill_comprehensive_pdf_template(self, pdf_path, extracted_data, output_path="filled_comprehensive.pdf"):
        """
        Fill any PDF template with comprehensive field mapping based on pdf_form_filler.py logic.
        This function handles extensive field mapping for DME intake forms and other medical documents.
        
        Args:
            pdf_path: Path to the PDF template
            extracted_data: Dictionary containing extracted patient data
            output_path: Path where the filled PDF will be saved
        
        Returns:
            str: Path to the filled PDF file
        """
        try:
            doc = fitz.open(pdf_path)

            # Comprehensive field mapping based on pdf_form_filler.py
            field_map = {
                # Patient Information
                "patient last name": "patient_information.full_name",  # Will extract last name
                "patient first name": "patient_information.full_name",  # Will extract first name
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
            
            print(f"🔍 Comprehensive field mapping for PDF template:")
            
            # First, let's see what fields are available in the PDF
            all_fields = []
            for page in doc:
                widgets = page.widgets()
                if widgets:
                    for w in widgets:
                        if w.field_name:
                            all_fields.append(w.field_name)
            
            print(f"📋 Available fields in PDF: {all_fields}")
            print(f"📋 Field mapping keys: {list(field_map.keys())}")
            
            # Fill the form fields
            filled_count = 0
            for page in doc:
                widgets = page.widgets()
                if not widgets:
                    continue
                for w in widgets:
                    if w.field_name and w.field_name in field_map:
                        schema_path = field_map[w.field_name]
                        value = self._get_value_from_schema(extracted_data, schema_path)
                        
                        # Special handling for name extraction
                        if w.field_name == "patient first name" and value:
                            value = self._get_first_name(value)
                        elif w.field_name == "patient last name" and value:
                            value = self._get_last_name(value)
                        elif w.field_name == "patient address" and value:
                            value = self._get_full_address(value)
                        
                        if value:
                            w.field_value = str(value)
                            
                            # Try to hide field borders/placeholders
                            try:
                                # Set field flags to hide borders
                                w.field_flags = w.field_flags | 0x00000002  # ReadOnly flag
                                # Try to set appearance to hide borders
                                w.field_display = 0  # Hide field display
                            except:
                                pass
                            
                            w.update()
                            filled_count += 1
                            print(f"✅ Filled '{w.field_name}' with '{value}'")
                    elif w.field_name:
                        print(f"❌ No mapping found for field: '{w.field_name}'")

            # Save the filled PDF first
            print(f"💾 Saving filled PDF...")
            temp_path = output_path.replace('.pdf', '_temp.pdf')
            doc.save(temp_path)
            doc.close()
            
            # Convert to non-editable by rendering to images
            print(f"🔒 Converting to non-editable format...")
            self._convert_to_non_editable(temp_path, output_path)
            
            # Clean up temp file
            import os
            try:
                os.unlink(temp_path)
            except:
                pass
            
            print(f"✅ PDF filled and made non-editable! Filled {filled_count} fields.")
            return output_path

        except Exception as e:
            print(f"Error filling comprehensive PDF: {e}")
            raise e
    
    def _get_value_from_schema(self, data, path):
        """Helper: fetch nested value from dict using dot path"""
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

    def _get_first_name(self, full_name):
        """Extract first name from full name"""
        if isinstance(full_name, dict) and "value" in full_name:
            full_name = full_name["value"]
        if isinstance(full_name, str):
            name_parts = full_name.split()
            return name_parts[0] if name_parts else ""
        return ""

    def _get_last_name(self, full_name):
        """Extract last name from full name"""
        if isinstance(full_name, dict) and "value" in full_name:
            full_name = full_name["value"]
        if isinstance(full_name, str):
            name_parts = full_name.split()
            return name_parts[-1] if name_parts else ""
        return ""

    def _get_full_address(self, address_dict):
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
                    if val:  # Only add non-empty values
                        address_parts.append(val)
                elif isinstance(value, str) and value:  # Only add non-empty strings
                    address_parts.append(value)
        
        return " ".join(address_parts) if address_parts else ""

    def _convert_to_non_editable(self, input_path: str, output_path: str, dpi: int = 150) -> None:
        """
        Convert filled PDF to non-editable by rendering each page as an image.
        This completely removes all form fields and makes the PDF truly read-only.
        
        Args:
            input_path: Path to the filled PDF
            output_path: Path where the non-editable PDF will be saved
            dpi: Resolution for rendering (150 is good quality, default)
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

    def fill_pdf_templates(self, json_result, group_id, templates, db_session):
        """
        Fill PDF templates with extracted data using PyMuPDF (fitz).
        
        Args:
            json_result: Dictionary containing extracted patient data
            group_id: Unique identifier for the document group
            templates: List of template objects from database
            db_session: Database session for creating GeneratedDocument entries
        
        Returns:
            List of dictionaries containing S3 information for generated documents
        """
        try:
            # Generate PDFs for requested templates
            generated_documents = []            
            for temp in templates:
                try:
                    logger.info(f"Processing template: {temp.name}")
                    logger.info(f"Template S3 path: {temp.s3_path}")
                    
                    # Download PDF template from S3 using the dedicated function
                    temp_pdf_path = file_handler.download_pdf_template_from_s3(temp.s3_path)
                    logger.info(f"Downloaded template PDF from S3 to: {temp_pdf_path}")
                    
                    # Create output path for filled PDF
                    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as output_file:
                        output_pdf_path = output_file.name
                    
                    # Function mapping
                    logger.info(f"Template name: '{temp.name}' - checking for template type")
                    try:
                        if "purewick" in temp.name.lower():
                            logger.info("Using Purewick resupply agreement filling function")
                            filled_pdf_path = self.fill_purewick_resupply_agreement(
                                temp_pdf_path, 
                                json_result, 
                                output_pdf_path
                            )
                        elif "non medicare" in temp.name.lower():
                            logger.info("Using Non Medicare DME intake form filling function")
                            filled_pdf_path = self.fill_non_medicare_dme_intake_form(
                                temp_pdf_path, 
                                json_result, 
                                output_pdf_path
                            )
                        elif "cgm resupply" in temp.name.lower():
                            logger.info("Using CGM resupply agreement filling function")
                            filled_pdf_path = self.fill_cgm_resupply_agreement_form(
                                temp_pdf_path, 
                                json_result, 
                                output_pdf_path
                            )
                        elif any(x in temp.name for x in ["Payment Authorization Form", "Patient Service Agreement", "Ongoing Rental Agreement", "Patient Handout", "Patient Notes", "Equipment Warranty Information", "Medicare Capped Rental"]):
                            # Return the PDF as it is from the s3 bucket
                            filled_pdf_path = temp_pdf_path

                        elif "patient financial responsibility" in temp.name.lower():
                            logger.info("Using Patient Financial Responsibility filling function")
                            filled_pdf_path = self.fill_patient_financial_responsibilty_template(
                                temp_pdf_path, 
                                json_result, 
                                output_pdf_path
                            )
                        else:
                            logger.info("Using comprehensive PDF filling function")
                            # Use the comprehensive filling function for all other templates
                            filled_pdf_path = self.fill_comprehensive_pdf_template(
                                temp_pdf_path, 
                                json_result, 
                                output_pdf_path
                            )
                        logger.info(f"Successfully filled PDF: {filled_pdf_path}")
                    except Exception as e:
                        logger.error(f"Error filling PDF template {temp.name}: {e}")
                        continue
                    
                    # Upload filled PDF to S3 and create database entry
                    try:
                        # Upload to S3
                        upload_result = file_handler.upload_generated_pdf_to_s3(
                            filled_pdf_path, group_id, temp.name
                        )
                        
                        # Create database entry if db_session is provided
                        if db_session:
                            generated_doc = GeneratedDocument(
                                document_group_id=group_id,
                                document_type=f"filled_{temp.name.lower().replace(' ', '_')}",
                                s3_path=upload_result["s3_key"],
                                created_at=datetime.now(),
                                updated_at=datetime.now()
                            )
                            db_session.add(generated_doc)
                            db_session.commit()
                            db_session.refresh(generated_doc)
                            
                            logger.info(f"Created database entry for generated document: {generated_doc.id}")
                        
                        logger.info(f"Successfully uploaded filled PDF to S3: {upload_result['s3_url']}")
                        
                        # Add to results with S3 information
                        generated_documents.append({
                            "template_name": temp.name,
                            "s3_key": upload_result["s3_key"],
                            "s3_url": upload_result["s3_url"],
                            "file_id": upload_result["file_id"]
                        })
                        
                    except Exception as e:
                        logger.error(f"Error uploading filled PDF to S3 or creating database entry: {e}")
                        # Continue with other PDFs even if one fails
                        
                except Exception as e:
                    logger.error(f"Error processing template {temp.name}: {e}")
                    # Continue with other templates even if one fails
                    continue
                    
                finally:
                    # Clean up temporary files
                    try:
                        if temp_pdf_path and os.path.exists(temp_pdf_path):
                            os.unlink(temp_pdf_path)
                        if 'output_pdf_path' in locals() and output_pdf_path and os.path.exists(output_pdf_path):
                            os.unlink(output_pdf_path)
                    except Exception as e:
                        logger.warning(f"Could not delete temporary files: {e}")
            
            return generated_documents
            
        except Exception as e:
            logger.error(f"Error filling PDF templates: {e}")
            raise e

if __name__ == "__main__":
    PDF_PATH = "/content/dbd994f3-32d4-4d88-b991-22075124f480.pdf"  # Replace with your actual PDF file path
    extractor = PdfProcessor()
    try:
        response = extractor.extract_text_from_pdf(PDF_PATH)
        print("OCR extraction successful!\n")
        for page in response.pages:
            print(f"--- Page {page.index + 1} ---\n")
            print(page.markdown)
            print("\n")
    except Exception as e:
        print(f"Error during OCR processing: {e}")
