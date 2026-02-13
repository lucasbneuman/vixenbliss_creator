"""
LoRA API Endpoints
Handles dataset generation and LoRA training
"""

import uuid
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, UploadFile, File, Form, Header
from sqlalchemy.orm import Session
from uuid import UUID

from app.database import get_db
from app.api.dependencies import get_user_id
from app.models.lora_model import LoRAModel
from app.schemas.lora import (
    DatasetGenerationRequest,
    DatasetGenerationResponse,
    LoRATrainingRequest,
    LoRATrainingResponse,
    LoRATrainingStatus,
    LoRAModelCreateRequest,
    LoRAModelResponse
)
from app.services.dataset_builder import dataset_builder_service
from app.services.storage import storage_service
from app.workers.tasks import train_lora_task


router = APIRouter(prefix="/api/v1/loras", tags=["loras"])


@router.get("/models", response_model=list[LoRAModelResponse])
def list_lora_models(
    user_id: UUID,
    include_inactive: bool = False,
    auth_user_id: UUID = Depends(get_user_id),
    db: Session = Depends(get_db)
):
    if user_id != auth_user_id:
        raise HTTPException(status_code=403, detail="user_id does not match authenticated user")

    query = db.query(LoRAModel).filter(LoRAModel.user_id == user_id)
    if not include_inactive:
        query = query.filter(LoRAModel.is_active.is_(True))
    return query.order_by(LoRAModel.created_at.desc()).all()


@router.post("/models", response_model=LoRAModelResponse)
def create_lora_model(
    request: LoRAModelCreateRequest,
    user_id: UUID,
    auth_user_id: UUID = Depends(get_user_id),
    db: Session = Depends(get_db)
):
    if user_id != auth_user_id:
        raise HTTPException(status_code=403, detail="user_id does not match authenticated user")

    lora_model = LoRAModel(
        user_id=user_id,
        name=request.name,
        description=request.description,
        base_model=request.base_model,
        lora_weights_url=request.lora_weights_url,
        preview_image_url=request.preview_image_url,
        tags=request.tags,
        meta_data=request.meta_data,
        is_active=True
    )
    db.add(lora_model)
    db.commit()
    db.refresh(lora_model)
    return lora_model


@router.post("/models/upload", response_model=LoRAModelResponse)
async def upload_lora_model(
    user_id: UUID = Form(...),
    name: str = Form(...),
    description: str | None = Form(None),
    base_model: str | None = Form(None),
    preview_image_url: str | None = Form(None),
    tags: str | None = Form(None),
    metadata_json: str | None = Form(None),
    lora_file: UploadFile = File(...),
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db)
):
    resolved_user_id = await get_user_id(authorization=authorization, q_user_id=str(user_id))
    if user_id != resolved_user_id:
        raise HTTPException(status_code=403, detail="user_id does not match authenticated user")

    if not lora_file.filename.lower().endswith(".safetensors"):
        raise HTTPException(status_code=400, detail="LoRA file must be .safetensors")

    try:
        file_content = await lora_file.read()
        file_ext = lora_file.filename.split(".")[-1]
        file_path = f"lora/{user_id}/{uuid.uuid4()}.{file_ext}"

        upload_result = storage_service.upload_file(
            file_content=file_content,
            file_path=file_path,
            content_type="application/octet-stream",
            metadata={"user_id": str(user_id), "name": name}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload LoRA file: {str(e)}")

    parsed_tags = [t.strip() for t in (tags or "").split(",") if t.strip()]
    parsed_metadata = {}
    if metadata_json:
        import json
        try:
            parsed_metadata = json.loads(metadata_json)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="metadata_json must be valid JSON")

    lora_model = LoRAModel(
        user_id=user_id,
        name=name,
        description=description,
        base_model=base_model,
        lora_weights_url=upload_result["r2_url"],
        preview_image_url=preview_image_url,
        tags=parsed_tags,
        meta_data=parsed_metadata,
        is_active=True
    )
    db.add(lora_model)
    db.commit()
    db.refresh(lora_model)
    return lora_model


@router.delete("/models/{lora_model_id}")
def delete_lora_model(
    lora_model_id: UUID,
    user_id: UUID,
    auth_user_id: UUID = Depends(get_user_id),
    db: Session = Depends(get_db)
):
    if user_id != auth_user_id:
        raise HTTPException(status_code=403, detail="user_id does not match authenticated user")

    lora_model = db.query(LoRAModel).filter(
        LoRAModel.id == lora_model_id,
        LoRAModel.user_id == user_id
    ).first()
    if not lora_model:
        raise HTTPException(status_code=404, detail="LoRA model not found")

    lora_model.is_active = False
    db.commit()
    return {"success": True, "lora_model_id": str(lora_model_id)}


@router.post("/dataset/generate", response_model=DatasetGenerationResponse)
async def generate_dataset(
    request: DatasetGenerationRequest,
    db: Session = Depends(get_db)
):
    """
    Generate training dataset for LoRA fine-tuning

    Creates 50 variations of the avatar with different:
    - Camera angles
    - Lighting conditions
    - Facial expressions
    - Poses

    Validates consistency using CLIP embeddings.
    Returns ZIP archive ready for training.
    """
    try:
        result = await dataset_builder_service.generate_dataset(db, request)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Dataset generation failed: {str(e)}"
        )


@router.post("/training/start", response_model=LoRATrainingResponse)
async def start_lora_training(
    request: LoRATrainingRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Start LoRA training job (async via Celery)

    Training is performed on Google Colab Pro with A100 GPU using Kohya_ss.
    Typical training time: 20-30 minutes.

    Returns training job ID for status tracking.
    """
    try:
        # Queue training task in Celery
        task = train_lora_task.delay(
            avatar_id=str(request.avatar_id),
            dataset_batch_id=request.dataset_batch_id,
            training_steps=request.training_steps,
            learning_rate=request.learning_rate,
            lora_rank=request.lora_rank,
            use_auto_captions=request.use_auto_captions
        )

        return LoRATrainingResponse(
            success=True,
            avatar_id=request.avatar_id,
            training_job_id=task.id,
            estimated_time_minutes=25,
            cost_estimate_usd=2.50,  # Google Colab Pro cost
            status="queued",
            weights_url=None
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to queue training job: {str(e)}"
        )


@router.get("/training/status/{training_job_id}", response_model=LoRATrainingStatus)
def get_training_status(training_job_id: str):
    """Get status of LoRA training job"""
    from app.workers.celery_app import celery_app

    task_result = celery_app.AsyncResult(training_job_id)

    if task_result.state == "PENDING":
        status_response = LoRATrainingStatus(
            training_job_id=training_job_id,
            status="queued",
            progress_percentage=0.0,
            current_step=0,
            total_steps=0,
            estimated_time_remaining_minutes=None,
            loss=None,
            weights_url=None,
            error_message=None
        )
    elif task_result.state == "STARTED":
        info = task_result.info or {}
        status_response = LoRATrainingStatus(
            training_job_id=training_job_id,
            status="running",
            progress_percentage=info.get("progress", 0.0),
            current_step=info.get("current_step", 0),
            total_steps=info.get("total_steps", 0),
            estimated_time_remaining_minutes=info.get("eta_minutes"),
            loss=info.get("loss"),
            weights_url=None,
            error_message=None
        )
    elif task_result.state == "SUCCESS":
        result = task_result.result or {}
        status_response = LoRATrainingStatus(
            training_job_id=training_job_id,
            status="completed",
            progress_percentage=100.0,
            current_step=result.get("total_steps", 0),
            total_steps=result.get("total_steps", 0),
            estimated_time_remaining_minutes=0,
            loss=result.get("final_loss"),
            weights_url=result.get("weights_url"),
            error_message=None
        )
    elif task_result.state == "FAILURE":
        status_response = LoRATrainingStatus(
            training_job_id=training_job_id,
            status="failed",
            progress_percentage=0.0,
            current_step=0,
            total_steps=0,
            estimated_time_remaining_minutes=None,
            loss=None,
            weights_url=None,
            error_message=str(task_result.info)
        )
    else:
        status_response = LoRATrainingStatus(
            training_job_id=training_job_id,
            status=task_result.state.lower(),
            progress_percentage=0.0,
            current_step=0,
            total_steps=0,
            estimated_time_remaining_minutes=None,
            loss=None,
            weights_url=None,
            error_message=None
        )

    return status_response
