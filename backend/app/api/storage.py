from fastapi import APIRouter, HTTPException, UploadFile, File, Query
from typing import Optional
from pydantic import BaseModel

from app.services.storage import storage_service

router = APIRouter(prefix="/storage", tags=["storage"])

class PresignedUrlRequest(BaseModel):
    file_path: str
    expiration: int = 3600
    download_as: Optional[str] = None

class PresignedUrlResponse(BaseModel):
    presigned_url: str
    expires_in: int

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    folder: str = Query("uploads", description="Upload folder path")
):
    """
    Upload file to R2 storage
    """
    try:
        # Read file content
        file_content = await file.read()

        # Generate file path
        file_path = f"{folder}/{file.filename}"

        # Upload to storage
        result = storage_service.upload_file(
            file_content=file_content,
            file_path=file_path,
            content_type=file.content_type or 'application/octet-stream'
        )

        return {
            "success": True,
            "file_path": file_path,
            "url": result['r2_url'],
            "backup_url": result.get('s3_url')
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/presigned-url", response_model=PresignedUrlResponse)
async def generate_presigned_url(request: PresignedUrlRequest):
    """
    Generate presigned URL for secure file access
    """
    try:
        presigned_url = storage_service.generate_presigned_url(
            file_path=request.file_path,
            expiration=request.expiration,
            download_as=request.download_as
        )

        return PresignedUrlResponse(
            presigned_url=presigned_url,
            expires_in=request.expiration
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/delete")
async def delete_file(
    file_path: str = Query(..., description="File path in storage"),
    delete_backup: bool = Query(True, description="Also delete from S3 backup")
):
    """
    Delete file from storage
    """
    try:
        success = storage_service.delete_file(
            file_path=file_path,
            delete_backup=delete_backup
        )

        if success:
            return {"success": True, "message": "File deleted"}
        else:
            raise HTTPException(status_code=500, detail="Deletion failed")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/list")
async def list_files(
    prefix: str = Query("", description="Filter by prefix"),
    max_keys: int = Query(100, description="Maximum number of files", le=1000)
):
    """
    List files in storage
    """
    try:
        files = storage_service.list_files(prefix=prefix, max_keys=max_keys)

        return {
            "success": True,
            "count": len(files),
            "files": [
                {
                    "key": f.get('Key'),
                    "size": f.get('Size'),
                    "last_modified": f.get('LastModified').isoformat() if f.get('LastModified') else None
                }
                for f in files
            ]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metadata")
async def get_file_metadata(
    file_path: str = Query(..., description="File path in storage")
):
    """
    Get file metadata
    """
    try:
        metadata = storage_service.get_file_metadata(file_path=file_path)

        if metadata:
            return {"success": True, **metadata}
        else:
            raise HTTPException(status_code=404, detail="File not found")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
