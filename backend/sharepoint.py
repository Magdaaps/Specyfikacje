import os
import logging
from office365.runtime.auth.client_credential import ClientCredential
from office365.sharepoint.client_context import ClientContext
from dotenv import load_dotenv

logger = logging.getLogger("generator-api.sharepoint")

load_dotenv()

SHAREPOINT_SITE_URL = os.getenv("SHAREPOINT_SITE_URL")
SHAREPOINT_CLIENT_ID = os.getenv("SHAREPOINT_CLIENT_ID")
SHAREPOINT_CLIENT_SECRET = os.getenv("SHAREPOINT_CLIENT_SECRET")

def get_sharepoint_context():
    if not all([SHAREPOINT_SITE_URL, SHAREPOINT_CLIENT_ID, SHAREPOINT_CLIENT_SECRET]):
        return None
    
    try:
        ctx = ClientContext(SHAREPOINT_SITE_URL).with_credentials(
            ClientCredential(SHAREPOINT_CLIENT_ID, SHAREPOINT_CLIENT_SECRET)
        )
        return ctx
    except Exception as e:
        logger.error(f"SharePoint connection error: {e}")
        return None

def upload_to_sharepoint(file_content, target_folder, filename):
    ctx = get_sharepoint_context()
    if not ctx:
        # Mocking for demo if no credentials
        logger.warning(f"MOCK MODE: Uploading {filename} to SharePoint folder {target_folder}")
        return True
    
    try:
        target_dir = ctx.web.get_folder_by_server_relative_url(target_folder)
        target_dir.upload_file(filename, file_content).execute_query()
        return True
    except Exception as e:
        logger.error(f"Upload error: {e}")
        return False

def download_logistics_from_sharepoint(relative_url):
    ctx = get_sharepoint_context()
    if not ctx:
        logger.warning("MOCK MODE: Downloading logistics file from SharePoint")
        return None
    
    try:
        response = ctx.web.get_file_by_server_relative_url(relative_url).download().execute_query()
        return response.content
    except Exception as e:
        logger.error(f"Download error: {e}")
        return None
