# from fastapi import APIRouter, Request, HTTPException
# import requests
# from app.config import POWERBI_API

# router = APIRouter()

# @router.get("/workspaces")
# def get_workspaces(request: Request):
#     access_token = request.session.get("access_token")

#     if not access_token:
#         raise HTTPException(status_code=401, detail="Not logged in")

#     headers = {
#         "Authorization": f"Bearer {access_token}"
#     }

#     # 1. Get all workspaces
#     ws_resp = requests.get(f"{POWERBI_API}/groups", headers=headers)

#     if ws_resp.status_code != 200:
#         raise HTTPException(status_code=ws_resp.status_code, detail=ws_resp.text)

#     workspaces = ws_resp.json().get("value", [])

#     # 2. For each workspace, get reports + datasets
#     for ws in workspaces:
#         workspace_id = ws["id"]

#         reports_resp = requests.get(
#             f"{POWERBI_API}/groups/{workspace_id}/reports",
#             headers=headers
#         )

#         datasets_resp = requests.get(
#             f"{POWERBI_API}/groups/{workspace_id}/datasets",
#             headers=headers
#         )

#         ws["reports"] = (
#             reports_resp.json().get("value", [])
#             if reports_resp.status_code == 200
#             else []
#         )

#         ws["datasets"] = (
#             datasets_resp.json().get("value", [])
#             if datasets_resp.status_code == 200
#             else []
#         )

#     return {
#         "count": len(workspaces),
#         "workspaces": workspaces
#     }

from fastapi import APIRouter, HTTPException, Body
import requests
import os
import msal
from app.config import POWERBI_API, TENANT_ID, CLIENT_ID, CLIENT_SECRET

router = APIRouter()

# ==========================================================
# SERVICE PRINCIPAL CONFIG
# ==========================================================

AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
SCOPE = ["https://analysis.windows.net/powerbi/api/.default"]

SP_OBJECT_ID = os.getenv("SP_OBJECT_ID")  # MUST be Enterprise App Object ID


# ==========================================================
# GET SERVICE PRINCIPAL ACCESS TOKEN
# ==========================================================

def get_sp_access_token():
    app = msal.ConfidentialClientApplication(
        CLIENT_ID,
        authority=AUTHORITY,
        client_credential=CLIENT_SECRET
    )

    result = app.acquire_token_for_client(scopes=SCOPE)

    if "access_token" not in result:
        raise HTTPException(
            status_code=400,
            detail=f"Token acquisition failed: {result}"
        )

    return result["access_token"]


# ==========================================================
# GET WORKSPACES (SP BASED)
# ==========================================================

@router.get("/workspaces")
def get_workspaces():

    access_token = get_sp_access_token()

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    ws_resp = requests.get(f"{POWERBI_API}/groups", headers=headers)

    if ws_resp.status_code != 200:
        raise HTTPException(status_code=ws_resp.status_code, detail=ws_resp.text)

    workspaces = ws_resp.json().get("value", [])

    for ws in workspaces:
        workspace_id = ws["id"]

        reports_resp = requests.get(
            f"{POWERBI_API}/groups/{workspace_id}/reports",
            headers=headers
        )

        datasets_resp = requests.get(
            f"{POWERBI_API}/groups/{workspace_id}/datasets",
            headers=headers
        )

        ws["reports"] = (
            reports_resp.json().get("value", [])
            if reports_resp.status_code == 200
            else []
        )

        ws["datasets"] = (
            datasets_resp.json().get("value", [])
            if datasets_resp.status_code == 200
            else []
        )

    return {
        "count": len(workspaces),
        "workspaces": workspaces
    }


# ==========================================================
# CREATE WORKSPACE (SP BASED)
# ==========================================================

@router.post("/workspaces")
def create_workspace(payload: dict = Body(...)):

    workspace_name = payload.get("workspace_name")

    if not workspace_name:
        raise HTTPException(status_code=400, detail="workspace_name is required")

    access_token = get_sp_access_token()

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    response = requests.post(
        f"{POWERBI_API}/groups?workspaceV2=true",
        headers=headers,
        json={"name": workspace_name},
        timeout=30
    )

    if response.status_code not in (200, 201):
        raise HTTPException(status_code=response.status_code, detail=response.text)

    data = response.json()

    return {
        "message": "Workspace created successfully",
        "workspaceId": data["id"],
        "workspaceName": data["name"]
    }


# ==========================================================
# ADD SERVICE PRINCIPAL TO WORKSPACE
# ==========================================================

@router.post("/workspaces/add-sp")
def add_service_principal_to_workspace(payload: dict = Body(...)):

    workspace_id = payload.get("workspace_id")

    if not workspace_id:
        raise HTTPException(status_code=400, detail="workspace_id is required")

    if not SP_OBJECT_ID:
        raise HTTPException(status_code=500, detail="SP_OBJECT_ID not configured")

    access_token = get_sp_access_token()

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    users_url = f"{POWERBI_API}/groups/{workspace_id}/users"

    add_payload = {
        "identifier": SP_OBJECT_ID,
        "principalType": "App",
        "groupUserAccessRight": "Admin"
    }

    resp = requests.post(users_url, headers=headers, json=add_payload)

    if resp.status_code in (200, 201, 204):
        return {
            "status": "success",
            "message": "Service Principal added to workspace"
        }

    raise HTTPException(
        status_code=resp.status_code,
        detail=resp.text
    )