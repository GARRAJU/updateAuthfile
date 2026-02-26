from fastapi import APIRouter, Request, HTTPException
import jwt

router = APIRouter()

@router.get("/me")
def get_me(request: Request):
    id_token = request.session.get("id_token")

    if not id_token:
        raise HTTPException(status_code=401, detail="Not logged in")

    decoded = jwt.decode(id_token, options={"verify_signature": False})

    return {
        "name": decoded.get("name"),
        "email": decoded.get("preferred_username") or decoded.get("email"),
        "oid": decoded.get("oid"),
        "tenant_id": decoded.get("tid")
    }
