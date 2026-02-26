# from fastapi import APIRouter, HTTPException, Request
# from fastapi.responses import RedirectResponse
# import msal
# from app.config import CLIENT_ID, CLIENT_SECRET, TENANT_ID, REDIRECT_URI, POWERBI_SCOPE

# router = APIRouter()

# msal_app = msal.ConfidentialClientApplication(
#     CLIENT_ID,
#     authority=f"https://login.microsoftonline.com/{TENANT_ID}",
#     client_credential=CLIENT_SECRET
# )

# @router.get("/login")
# def login(request: Request):
#     request.session.clear()
#     auth_url = msal_app.get_authorization_request_url(
#         scopes=POWERBI_SCOPE,
#         redirect_uri=REDIRECT_URI
#     )
#     return RedirectResponse(auth_url)

# @router.get("/auth/callback")
# def auth_callback(request: Request, code: str):
#     token = msal_app.acquire_token_by_authorization_code(
#         code=code,
#         scopes=POWERBI_SCOPE,
#         redirect_uri=REDIRECT_URI
#     )

#     if "access_token" not in token:
#         raise HTTPException(status_code=400, detail=token)

#     # Store token in session
#     request.session["access_token"] = token["access_token"]
#     request.session["id_token"] = token.get("id_token")

#     print("TOKEN RESPONSE:", token.keys())
#     print("ID TOKEN:", token.get("id_token"))

#     # Redirect to frontend success page
#     return RedirectResponse(
#         "https://id-preview--1115fb10-6ea8-4052-8d1b-31238016c02e.lovable.app/powerbi-auth-success"
#     )
#     # return {"message": "Login successful"}
#     # return RedirectResponse("http://localhost:8000/me")



from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
import msal
from datetime import datetime, timedelta
from app.config import CLIENT_ID, CLIENT_SECRET, TENANT_ID, REDIRECT_URI, POWERBI_SCOPE
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

msal_app = msal.ConfidentialClientApplication(
    CLIENT_ID,
    authority=f"https://login.microsoftonline.com/{TENANT_ID}",
    client_credential=CLIENT_SECRET
)

@router.get("/login")
def login(request: Request):
    """Initiate OAuth login flow"""
    request.session.clear()
    auth_url = msal_app.get_authorization_request_url(
        scopes=POWERBI_SCOPE,
        redirect_uri=REDIRECT_URI,
        prompt="select_account"
    )
    return RedirectResponse(auth_url)

@router.get("/auth/callback")
def auth_callback(request: Request, code: str):
    """Handle OAuth callback and store tokens"""
    token = msal_app.acquire_token_by_authorization_code(
        code=code,
        scopes=POWERBI_SCOPE,
        redirect_uri=REDIRECT_URI
    )

    if "access_token" not in token:
        logger.error(f"Token acquisition failed: {token}")
        raise HTTPException(status_code=400, detail="Failed to acquire token")

    # Store tokens in session
    request.session["access_token"] = token["access_token"]
    request.session["refresh_token"] = token.get("refresh_token")
    request.session["user"] = token.get("id_token_claims")
    
    # Store expiry time
    if "expires_in" in token:
        expires_at = datetime.now() + timedelta(seconds=token["expires_in"])
        request.session["token_expires_at"] = expires_at.isoformat()

    logger.info(f"User authenticated: {token.get('id_token_claims', {}).get('preferred_username')}")

    return RedirectResponse(
        "https://id-preview--1115fb10-6ea8-4052-8d1b-31238016c02e.lovable.app/powerbi-auth-success"
    )

@router.get("/auth/token")
def get_token(request: Request):
    """Get access token with automatic refresh"""
    access_token = request.session.get("access_token")
    token_expires_at = request.session.get("token_expires_at")
    user = request.session.get("user")
    
    if not access_token:
        raise HTTPException(
            status_code=401, 
            detail="Not authenticated. Please login.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Check if token needs refresh (within 10 minutes of expiry)
    is_expired = False
    if token_expires_at:
        expires_at = datetime.fromisoformat(token_expires_at)
        is_expired = datetime.now() >= (expires_at - timedelta(minutes=10))
    
    # Refresh if needed
    if is_expired:
        refresh_token = request.session.get("refresh_token")
        if not refresh_token:
            raise HTTPException(status_code=401, detail="Session expired, please login again")
        
        try:
            new_token = msal_app.acquire_token_by_refresh_token(
                refresh_token=refresh_token,
                scopes=POWERBI_SCOPE
            )
            
            if "access_token" not in new_token:
                raise HTTPException(status_code=401, detail="Token refresh failed")
            
            # Update session
            access_token = new_token["access_token"]
            request.session["access_token"] = access_token
            
            if "refresh_token" in new_token:
                request.session["refresh_token"] = new_token["refresh_token"]
            
            if "expires_in" in new_token:
                expires_at = datetime.now() + timedelta(seconds=new_token["expires_in"])
                request.session["token_expires_at"] = expires_at.isoformat()
                
        except Exception as e:
            logger.error(f"Token refresh failed: {str(e)}")
            raise HTTPException(status_code=401, detail="Token refresh failed, please login again")
    
    # Calculate remaining time
    expires_in = None
    if token_expires_at:
        expires_at = datetime.fromisoformat(token_expires_at)
        expires_in = int((expires_at - datetime.now()).total_seconds())
    
    return {
        "access_token": access_token,
        "expires_in": expires_in,
        "user": {
            "name": user.get("name") if user else None,
            "email": user.get("preferred_username") if user else None,
            "oid": user.get("oid") if user else None,
        } if user else None
    }

@router.get("/auth/me")
def me(request: Request):
    """Get current user info"""
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    return {
        "name": user.get("name"),
        "email": user.get("preferred_username"),
        "oid": user.get("oid"),
        "tenant": user.get("tid"),
    }

@router.post("/auth/logout")
def logout(request: Request):
    """Clear session"""
    request.session.clear()
    return {"message": "Logged out successfully"}


