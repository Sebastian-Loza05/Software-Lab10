from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from poke_images.services import image_service

router = APIRouter()


@router.get("/images/{name}", tags=["images"])
async def get_image(name: str) -> FileResponse:
    path = image_service.find_image(name)
    if path is None:
        raise HTTPException(status_code=404, detail=f"No image for '{name}'")
    return FileResponse(path, media_type="image/jpeg", filename=path.name)
