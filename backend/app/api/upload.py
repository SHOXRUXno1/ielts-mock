from fastapi import APIRouter, Depends, UploadFile

from app.api.deps import get_current_admin
from app.services.storage import save_audio, save_image

router = APIRouter(
    prefix="/admin/upload",
    tags=["Upload"],
    dependencies=[Depends(get_current_admin)],
)


@router.post("/audio")
async def upload_audio_file(file: UploadFile):
    contents = await file.read()
    url, _local = save_audio(contents, content_type=file.content_type or "audio/webm")
    return {"url": url}


@router.post("/image")
async def upload_image_file(file: UploadFile):
    contents = await file.read()
    url, _local = save_image(contents, content_type=file.content_type or "image/png")
    return {"url": url}
