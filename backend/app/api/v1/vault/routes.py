import os
import secrets
import uuid
from pathlib import Path
from typing import Optional

from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse

from ....core.config import get_settings
from ....core.response_handler import StandardResponse
from ....core.security import get_current_user
from ....models.documents import User, VaultCategory, VaultEntry, VaultNominee
from ....services.notification import send_email
from .schemas import NomineeCreate, NomineeResponse, VaultCategoryEnum, VaultEntryCreate, VaultEntryResponse

router = APIRouter()
settings = get_settings()

UPLOAD_DIR = Path("uploads/vault")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png", ".doc", ".docx"}


def entry_to_response(e: VaultEntry) -> VaultEntryResponse:
    return VaultEntryResponse(
        id=str(e.id),
        category=e.category,
        title=e.title,
        details=e.details,
        notes=e.notes,
        nominee_visible=e.nominee_visible,
        files=e.files or [],
        created_at=e.created_at.isoformat(),
        updated_at=e.updated_at.isoformat(),
    )


def nominee_to_response(n: VaultNominee) -> NomineeResponse:
    return NomineeResponse(
        id=str(n.id),
        nominee_email=n.nominee_email,
        nominee_name=n.nominee_name,
        relation=n.relation,
        accepted=n.accepted,
        created_at=n.created_at.isoformat(),
    )


# --- Vault Entries ---


@router.get("/entries", summary="Get vault entries")
async def get_entries(
    category: Optional[VaultCategoryEnum] = Query(None),
    current_user: dict = Depends(get_current_user),
) -> StandardResponse:
    query = {"user_id": PydanticObjectId(current_user["_id"])}
    if category:
        query["category"] = category.value
    entries = await VaultEntry.find(query).sort("-created_at").to_list()
    return StandardResponse.ok([entry_to_response(e) for e in entries])


@router.post("/entries", summary="Create vault entry")
async def create_entry(data: VaultEntryCreate, current_user: dict = Depends(get_current_user)) -> StandardResponse:
    entry = VaultEntry(
        user_id=PydanticObjectId(current_user["_id"]),
        category=VaultCategory(data.category),
        title=data.title,
        details=data.details,
        notes=data.notes,
        nominee_visible=data.nominee_visible,
    )
    await entry.insert()
    return StandardResponse.ok(entry_to_response(entry), "Entry created")


@router.put("/entries/{entry_id}", summary="Update vault entry")
async def update_entry(
    entry_id: str, data: VaultEntryCreate, current_user: dict = Depends(get_current_user)
) -> StandardResponse:
    if not PydanticObjectId.is_valid(entry_id):
        raise HTTPException(status_code=400, detail="Invalid ID")
    entry = await VaultEntry.find_one(
        {"_id": PydanticObjectId(entry_id), "user_id": PydanticObjectId(current_user["_id"])}
    )
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    entry.category = VaultCategory(data.category)
    entry.title = data.title
    entry.details = data.details
    entry.notes = data.notes
    entry.nominee_visible = data.nominee_visible
    await entry.save()
    return StandardResponse.ok(entry_to_response(entry), "Entry updated")


@router.delete("/entries/{entry_id}", summary="Delete vault entry")
async def delete_entry(entry_id: str, current_user: dict = Depends(get_current_user)) -> StandardResponse:
    if not PydanticObjectId.is_valid(entry_id):
        raise HTTPException(status_code=400, detail="Invalid ID")
    entry = await VaultEntry.find_one(
        {"_id": PydanticObjectId(entry_id), "user_id": PydanticObjectId(current_user["_id"])}
    )
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    await entry.delete()
    return StandardResponse.ok(message="Entry deleted")


# --- Nominees ---


@router.get("/nominees", summary="Get nominees")
async def get_nominees(current_user: dict = Depends(get_current_user)) -> StandardResponse:
    nominees = await VaultNominee.find({"user_id": PydanticObjectId(current_user["_id"])}).to_list()
    return StandardResponse.ok([nominee_to_response(n) for n in nominees])


@router.post("/nominees", summary="Add nominee")
async def add_nominee(data: NomineeCreate, current_user: dict = Depends(get_current_user)) -> StandardResponse:
    existing = await VaultNominee.find_one(
        {"user_id": PydanticObjectId(current_user["_id"]), "nominee_email": data.nominee_email}
    )
    if existing:
        raise HTTPException(status_code=400, detail="Nominee already exists")
    
    invite_token = secrets.token_urlsafe(32)
    nominee = VaultNominee(
        user_id=PydanticObjectId(current_user["_id"]),
        nominee_email=data.nominee_email,
        nominee_name=data.nominee_name,
        relation=data.relation,
        invite_token=invite_token,
    )
    await nominee.insert()
    
    # Send invite email
    owner_name = current_user.get("name") or current_user.get("email", "Someone")
    accept_url = f"{settings.frontend_url}/vault/shared?token={invite_token}"
    html = f"""
    <h2>🔐 Family Vault Invitation</h2>
    <p><strong>{owner_name}</strong> has added you as a nominee to their Family Vault on StockPilot.</p>
    <p>As a nominee, you'll be able to view their important financial documents including bank accounts, insurance policies, investments, and more.</p>
    <p><a href="{accept_url}" style="display:inline-block;padding:12px 24px;background:#6366f1;color:white;text-decoration:none;border-radius:8px;">Accept Invitation</a></p>
    <p style="color:#666;font-size:12px;">If you don't have a StockPilot account, you'll need to create one with this email address ({data.nominee_email}) to access the vault.</p>
    """
    await send_email(data.nominee_email, f"{owner_name} added you as a Vault Nominee - StockPilot", html)
    
    return StandardResponse.ok(nominee_to_response(nominee), "Nominee added and invite sent")


@router.delete("/nominees/{nominee_id}", summary="Remove nominee")
async def remove_nominee(nominee_id: str, current_user: dict = Depends(get_current_user)) -> StandardResponse:
    if not PydanticObjectId.is_valid(nominee_id):
        raise HTTPException(status_code=400, detail="Invalid ID")
    nominee = await VaultNominee.find_one(
        {"_id": PydanticObjectId(nominee_id), "user_id": PydanticObjectId(current_user["_id"])}
    )
    if not nominee:
        raise HTTPException(status_code=404, detail="Nominee not found")
    await nominee.delete()
    return StandardResponse.ok(message="Nominee removed")


# --- Nominee Access (view vault as nominee) ---


@router.get("/shared/{owner_email}", summary="View vault as nominee")
async def view_shared_vault(owner_email: str, current_user: dict = Depends(get_current_user)) -> StandardResponse:
    owner = await User.find_one({"email": owner_email})
    if not owner:
        raise HTTPException(status_code=404, detail="User not found")
    nominee = await VaultNominee.find_one(
        {"user_id": owner.id, "nominee_email": current_user["email"], "accepted": True}
    )
    if not nominee:
        raise HTTPException(status_code=403, detail="Not authorized to view this vault")
    entries = await VaultEntry.find({"user_id": owner.id, "nominee_visible": True}).sort("-created_at").to_list()
    return StandardResponse.ok(
        {"owner_name": owner.name or owner.email, "entries": [entry_to_response(e) for e in entries]}
    )


@router.get("/shared", summary="List vaults shared with me")
async def list_shared_vaults(current_user: dict = Depends(get_current_user)) -> StandardResponse:
    nominations = await VaultNominee.find({"nominee_email": current_user["email"], "accepted": True}).to_list()
    result = []
    for nom in nominations:
        owner = await User.get(nom.user_id)
        if owner:
            result.append(
                {"owner_email": owner.email, "owner_name": owner.name or owner.email, "relation": nom.relation}
            )
    return StandardResponse.ok(result)


@router.post("/accept-invite", summary="Accept nominee invite")
async def accept_invite(token: str = Query(...), current_user: dict = Depends(get_current_user)) -> StandardResponse:
    nominee = await VaultNominee.find_one({"invite_token": token, "nominee_email": current_user["email"]})
    if not nominee:
        raise HTTPException(status_code=404, detail="Invalid or expired invite")
    if nominee.accepted:
        return StandardResponse.ok(message="Already accepted")
    from datetime import datetime, timezone

    nominee.accepted = True
    nominee.accepted_at = datetime.now(timezone.utc)
    nominee.invite_token = None
    await nominee.save()
    return StandardResponse.ok(message="Invite accepted")



# --- File Upload/Download ---


@router.post("/entries/{entry_id}/upload", summary="Upload file to vault entry")
async def upload_file(
    entry_id: str, file: UploadFile = File(...), current_user: dict = Depends(get_current_user)
) -> StandardResponse:
    if not PydanticObjectId.is_valid(entry_id):
        raise HTTPException(status_code=400, detail="Invalid ID")
    entry = await VaultEntry.find_one(
        {"_id": PydanticObjectId(entry_id), "user_id": PydanticObjectId(current_user["_id"])}
    )
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")

    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"File type not allowed. Allowed: {', '.join(ALLOWED_EXTENSIONS)}")

    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = UPLOAD_DIR / filename
    with open(filepath, "wb") as f:
        f.write(await file.read())

    entry.files = entry.files or []
    entry.files.append(filename)
    await entry.save()
    return StandardResponse.ok({"filename": filename}, "File uploaded")


@router.get("/files/{filename}", summary="Download vault file")
async def download_file(filename: str, current_user: dict = Depends(get_current_user)):
    filepath = UPLOAD_DIR / filename
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="File not found")

    # Verify user owns an entry with this file
    entry = await VaultEntry.find_one(
        {"user_id": PydanticObjectId(current_user["_id"]), "files": filename}
    )
    if not entry:
        # Check if user is a nominee with access
        nominations = await VaultNominee.find({"nominee_email": current_user["email"], "accepted": True}).to_list()
        owner_ids = [n.user_id for n in nominations]
        entry = await VaultEntry.find_one({"user_id": {"$in": owner_ids}, "files": filename, "nominee_visible": True})
        if not entry:
            raise HTTPException(status_code=403, detail="Not authorized")

    return FileResponse(filepath, filename=filename)


@router.delete("/entries/{entry_id}/files/{filename}", summary="Delete file from vault entry")
async def delete_file(
    entry_id: str, filename: str, current_user: dict = Depends(get_current_user)
) -> StandardResponse:
    if not PydanticObjectId.is_valid(entry_id):
        raise HTTPException(status_code=400, detail="Invalid ID")
    entry = await VaultEntry.find_one(
        {"_id": PydanticObjectId(entry_id), "user_id": PydanticObjectId(current_user["_id"])}
    )
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    if filename not in (entry.files or []):
        raise HTTPException(status_code=404, detail="File not found in entry")

    filepath = UPLOAD_DIR / filename
    if filepath.exists():
        os.remove(filepath)

    entry.files.remove(filename)
    await entry.save()
    return StandardResponse.ok(message="File deleted")
