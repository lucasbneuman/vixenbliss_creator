"""
LoRA API Endpoints
Handles dataset generation and LoRA training
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from uuid import UUID

from app.database import get_db
from app.schemas.lora import (
    DatasetGenerationRequest,
    DatasetGenerationResponse,
    LoRATrainingRequest,
    LoRATrainingResponse,
    LoRATrainingStatus
)
from app.services.dataset_builder import dataset_builder_service
from app.workers.tasks import train_lora_task


router = APIRouter(prefix="/api/v1/loras", tags=["loras"])


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
