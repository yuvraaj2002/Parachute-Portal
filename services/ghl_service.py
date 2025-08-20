import httpx
import requests
import logging
from rich import print
from config import settings

logger = logging.getLogger(__name__)

class GHLService:
    def __init__(self):
        self.api_key = settings.ghl_api_key
        self.base_url = "https://rest.gohighlevel.com/v1"
        self.private_token = settings.private_token
        self.location_id = settings.location_id
        self.send_sms_url = "https://services.leadconnectorhq.com/conversations/messages"
        self.headers = {
            "Authorization": f"Bearer {self.private_token}",
            "Content-Type": "application/json",
            "Version": "2021-07-28"
        }
    

    async def find_contact_by_phone(self, phone_number: str):
        """
        Find a contact in GHL by phone number.
        Returns the contact ID if found, None otherwise.
        """
        if not self.api_key:
            logger.error("GHL_API_KEY environment variable not set. Cannot find contact.")
            return None

        url = f"{self.base_url}/contacts/lookup"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        params = {"phone": phone_number}

        try:
            response = requests.get(url, params=params, headers=headers)
            response.raise_for_status()
            
            contacts = response.json().get("contacts", [])
            for contact in contacts:
                contact_phone = contact.get('phone')
                if contact_phone == phone_number:
                    contact_id = contact.get('id', '')
                    logger.info(f"Found existing contact {contact_id} for phone {phone_number}")
                    return contact_id
            
            logger.info(f"No existing contact found for phone {phone_number}")
            return None
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 422:
                # Phone number is invalid - this is expected for some numbers
                logger.warning(f"Phone number {phone_number} is invalid according to GHL API. Status: {e.response.status_code}, Response: {e.response.text}")
            else:
                logger.error(f"Failed to find contact by phone {phone_number}. Status: {e.response.status_code}, Response: {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"An unexpected error occurred while finding contact: {str(e)}")
            return None

    async def send_sms(self, contact_id, message):
        payload = {
            "locationId": self.location_id,
            "contactId": contact_id,
            "message": message,
            "type": "SMS"
        }
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(self.send_sms_url, headers=self.headers, json=payload)
            resp.raise_for_status()
            logger.info("SMS sent and logged in Conversations!")
            logger.debug("Response: %s", resp.json())
            return True
        except httpx.HTTPStatusError as e:
            logger.error("Error sending SMS: %s %s", e.response.status_code, e.response.text)
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending SMS: {str(e)}")
            return False
    
# Create a singleton instance
ghl_service = GHLService() 

if __name__ == "__main__":
    import asyncio
    
    async def main():

        # Testing sending the SMS
        contact_id = await ghl_service.find_contact_by_phone("+916239305919")
        await ghl_service.send_sms(contact_id, "Hello, this is a test SMS from the GHL service!")
    
    asyncio.run(main())