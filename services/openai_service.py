from config import settings
import os
import time
import inspect
from rich import print
import logging
from prompt_registry import *
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

class LLMService:
    def __init__(self):
        self.chat_openai = ChatOpenAI(api_key=settings.openai_api_key, model="gpt-4o", temperature=0.8,timeout=None, max_retries=2)
        self.logger = logging.getLogger(__name__)

    async def chatbot_response(self, messages):
        """
        Streams the response from the LLM as an async generator of text chunks.
        """
        try:
            self.logger.info("🔄 [LLM] Starting OpenAI API request...")
            
            # Use invoke instead of stream for better async compatibility
            response = await self.chat_openai.ainvoke(messages)
            
            if response and response.content:
                self.logger.info(f"✅ [LLM] Response received ({len(response.content)} chars)")
                # Yield the complete response as a single chunk
                yield response.content
            else:
                self.logger.warning("⚠️ [LLM] Empty response from OpenAI")
                yield "I'm sorry, I couldn't generate a response at the moment. Please try again."
                
        except Exception as e:
            self.logger.error(f"❌ [LLM] Error in chatbot_response: {str(e)}")
            import traceback
            self.logger.error(f"📋 [LLM] Full traceback: {traceback.format_exc()}")
            yield f"I'm experiencing technical difficulties. Please try again in a moment."


    async def get_chat_summary(self, checkin_context: str):
        """
        Generates a summary of the chat session using LangChain and GPT-4o-mini.
        """
        try:
            messages = [
                SystemMessage(summary_prompt.format(checkin_context=checkin_context)),
                HumanMessage("Please provide a summary of the chat session.")
            ]
            response = await self.chat_openai.ainvoke(messages)
            return response.content
        except Exception as e:
            self.logger.error(f"Error generating chat summary: {str(e)}")
            import traceback
            self.logger.error(f"Full traceback: {traceback.format_exc()}")
            return None
        
    # def get_response_with_retry(self, messages, keys_to_check):
    #     retries = 3
    #     for attempt in range(retries):
    #         try:
    #             response = self.chat_openai.invoke(messages)
    #             response = response.content

    #             # Only check for missing keys, allow values to be None or null
    #             missing_keys = [key for key in keys_to_check if key not in response]
    #             if not missing_keys:
    #                 return response
    #             else:
    #                 raise ValueError(f"Missing keys in response: {missing_keys}")
    #         except Exception as e:
    #             self.logger.error(f"Error retrieving response: {e}. Attempt {attempt + 1} of {retries}.")
    #     return {}

    # async def generate_transcription_summary(self, transcription: str):
    #     """
    #     Generates a summary of the transcription using LangChain and GPT-4o-mini.
    #     """
    #     try:
    #         summary_prompt = """
    #         You are an expert at analyzing call transcriptions and creating concise, professional summaries.
            
    #         Please analyze the following call transcription and provide a comprehensive summary that includes:
            
    #         1. Call Purpose: What was the main objective of this call?
    #         2. Key Points Discussed: What were the main topics or points covered?
    #         3. Outcome: What was the result or conclusion of the call?
    #         4. Action Items: Are there any follow-up actions needed?
    #         5. Sentiment: What was the overall tone and sentiment of the conversation?
            
    #         Transcription:
    #         {transcription}
            
    #         IMPORTANT: Please provide your analysis in plain text format without any markdown symbols (no ###, **, '', etc.). Use proper numbering (1, 2, 3, etc.) and clear section breaks with line spacing. Make it easy to read and well-structured but without any markdown formatting.
    #         """
            
    #         messages = [
    #             SystemMessage(summary_prompt.format(transcription=transcription)),
    #             HumanMessage("Please provide a comprehensive summary of this call transcription.")
    #         ]
            
    #         # Use the existing retry mechanism
    #         summary = self.get_response_with_retry(messages, [])
            
    #         if summary:
    #             self.logger.info(f"Successfully generated summary for transcription of length {len(transcription)}")
    #             return summary
    #         else:
    #             self.logger.error("Failed to generate summary - empty response")
    #             return None
                
    #     except Exception as e:
    #         self.logger.error(f"Error generating transcription summary: {str(e)}")
    #         import traceback
    #         self.logger.error(f"Full traceback: {traceback.format_exc()}")
    #         return None



