import os
import base64
from mistralai import Mistral
from config import settings

class MistralPDFExtractor:
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

if __name__ == "__main__":
    PDF_PATH = "/content/dbd994f3-32d4-4d88-b991-22075124f480.pdf"  # Replace with your actual PDF file path
    extractor = MistralPDFExtractor()
    try:
        response = extractor.extract_text_from_pdf(PDF_PATH)
        print("OCR extraction successful!\n")
        for page in response.pages:
            print(f"--- Page {page.index + 1} ---\n")
            print(page.markdown)
            print("\n")
    except Exception as e:
        print(f"Error during OCR processing: {e}")
