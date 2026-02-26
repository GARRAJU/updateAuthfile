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

# from fastapi import APIRouter, Request, HTTPException, Body
# import requests
# from app.config import POWERBI_API
 
# router = APIRouter()
 
# # -------------------------------------------
# # GET WORKSPACES (your existing code)
# # -------------------------------------------
# @router.get("/workspaces")
# def get_workspaces(request: Request):
#     access_token = request.session.get("access_token")
 
#     if not access_token:
#         raise HTTPException(status_code=401, detail="Not logged in")
 
#     headers = {
#         "Authorization": f"Bearer {access_token}"
#     }
 
#     ws_resp = requests.get(f"{POWERBI_API}/groups", headers=headers)
#     if ws_resp.status_code != 200:
#         raise HTTPException(status_code=ws_resp.status_code, detail=ws_resp.text)
 
#     workspaces = ws_resp.json().get("value", [])
 
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
 
 
# # -------------------------------------------
# # CREATE NEW WORKSPACE
# # -------------------------------------------
# @router.post("/workspaces")
# def create_workspace(request: Request, payload: dict = Body(...)):
#     """
#     Create a new Power BI workspace using the access token in session
#     Expected payload: { "workspace_name": "My New Workspace" }
#     """
#     access_token = request.session.get("access_token")
 
#     if not access_token:
#         raise HTTPException(status_code=401, detail="Not logged in")
 
#     workspace_name = payload.get("workspace_name")
#     if not workspace_name:
#         raise HTTPException(status_code=400, detail="workspace_name is required")
 
#     headers = {
#         "Authorization": f"Bearer {access_token}",
#         "Content-Type": "application/json"
#     }
 
#     response = requests.post(
#         f"{POWERBI_API}/groups?workspaceV2=true",
#         headers=headers,
#         json={"name": workspace_name},
#         timeout=30
#     )
 
#     if response.status_code not in (200, 201):
#         raise HTTPException(status_code=response.status_code, detail=response.text)
 
#     data = response.json()
 
#     return {
#         "message": "Workspace created successfully",
#         "workspaceId": data["id"],
#         "workspaceName": data["name"]
#     }
 

 from fastapi import APIRouter, Request, HTTPException, Body
import requests  # For HTTP calls to Power BI API
from app.config import POWERBI_API
 
router = APIRouter()
 
# -------------------------------------------
# GET WORKSPACES
# -------------------------------------------
@router.get("/workspaces")
def get_workspaces(request: Request):  # ← Make sure 'request: Request' is here
    """
    Get all Power BI workspaces with their reports and datasets
    Uses access token from session (set during auth callback)
    """
    # Get access token from session
    access_token = request.session.get("access_token")
 
    if not access_token:
        raise HTTPException(
            status_code=401, 
            detail="Not authenticated. Please login first."
        )
 
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
 
    # Get all workspaces
    try:
        ws_resp = requests.get(
            f"{POWERBI_API}/groups", 
            headers=headers,
            timeout=30
        )
        ws_resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to fetch workspaces: {str(e)}"
        )
 
    workspaces = ws_resp.json().get("value", [])
 
    # Get reports and datasets for each workspace
    for ws in workspaces:
        workspace_id = ws["id"]
 
        # Get reports
        try:
            reports_resp = requests.get(
                f"{POWERBI_API}/groups/{workspace_id}/reports",
                headers=headers,
                timeout=30
            )
            ws["reports"] = (
                reports_resp.json().get("value", [])
                if reports_resp.status_code == 200
                else []
            )
        except Exception:
            ws["reports"] = []
 
        # Get datasets
        try:
            datasets_resp = requests.get(
                f"{POWERBI_API}/groups/{workspace_id}/datasets",
                headers=headers,
                timeout=30
            )
            ws["datasets"] = (
                datasets_resp.json().get("value", [])
                if datasets_resp.status_code == 200
                else []
            )
        except Exception:
            ws["datasets"] = []
 
    return {
        "count": len(workspaces),
        "workspaces": workspaces
    }
 
 
# -------------------------------------------
# CREATE NEW WORKSPACE
# -------------------------------------------
@router.post("/workspaces")
def create_workspace(request: Request, payload: dict = Body(...)):
    """
    Create a new Power BI workspace
    Expected payload: { "workspace_name": "My New Workspace" }
    """
    # Get access token from session
    access_token = request.session.get("access_token")
 
    if not access_token:
        raise HTTPException(
            status_code=401, 
            detail="Not authenticated. Please login first."
        )
 
    workspace_name = payload.get("workspace_name")
    if not workspace_name:
        raise HTTPException(
            status_code=400, 
            detail="workspace_name is required in request body"
        )
 
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
 
    try:
        response = requests.post(
            f"{POWERBI_API}/groups?workspaceV2=true",
            headers=headers,
            json={"name": workspace_name},
            timeout=30
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=response.status_code if hasattr(response, 'status_code') else 500,
            detail=f"Failed to create workspace: {str(e)}"
        )
 
    data = response.json()
 
    return {
        "message": "Workspace created successfully",
        "workspaceId": data.get("id"),
        "workspaceName": data.get("name")
    }