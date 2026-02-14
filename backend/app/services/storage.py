import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
from datetime import datetime, timedelta
from typing import Optional
import os
import logging

logger = logging.getLogger(__name__)

class StorageService:
    """
    Cloudflare R2 Storage Service with presigned URLs
    """

    def __init__(self):
        # Cloudflare R2 Configuration
        self.r2_client = None
        self.r2_bucket = None

        if os.getenv('R2_ENDPOINT_URL'):
            self.r2_client = boto3.client(
                's3',
                endpoint_url=os.getenv('R2_ENDPOINT_URL'),
                aws_access_key_id=os.getenv('R2_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('R2_SECRET_ACCESS_KEY'),
                config=Config(signature_version='s3v4'),
                region_name='auto'
            )
            self.r2_bucket = os.getenv('R2_BUCKET_NAME')

        # AWS S3 Backup Configuration (optional)
        self.s3_client = None
        if os.getenv('AWS_ACCESS_KEY_ID'):
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                region_name=os.getenv('AWS_REGION', 'us-east-1')
            )
            self.s3_bucket = os.getenv('S3_BUCKET_NAME')

    def upload_file(
        self,
        file_content: bytes,
        file_path: str,
        content_type: str = 'application/octet-stream',
        metadata: Optional[dict] = None
    ) -> dict:
        """
        Upload file to R2 and optionally to S3 backup

        Args:
            file_content: File content as bytes
            file_path: Path in bucket (e.g., 'avatars/uuid/image.jpg')
            content_type: MIME type
            metadata: Additional metadata

        Returns:
            dict with r2_url, s3_url (if backup enabled)
        """
        if not self.r2_client:
            raise ValueError("R2 storage is not configured. Please set R2_ENDPOINT_URL and related environment variables.")

        try:
            # Upload to R2 (primary)
            extra_args = {
                'ContentType': content_type,
            }
            if metadata:
                extra_args['Metadata'] = metadata

            self.r2_client.put_object(
                Bucket=self.r2_bucket,
                Key=file_path,
                Body=file_content,
                **extra_args
            )

            public_base = os.getenv('R2_PUBLIC_URL')
            if public_base:
                r2_url = f"{public_base.rstrip('/')}/{file_path}"
            else:
                # Fallback for local/dev setups without CDN URL configured.
                r2_url = self.r2_client.generate_presigned_url(
                    'get_object',
                    Params={
                        'Bucket': self.r2_bucket,
                        'Key': file_path
                    },
                    ExpiresIn=3600
                )
            logger.info(f"Uploaded to R2: {file_path}")

            result = {"r2_url": r2_url}

            # Backup to S3 (if configured)
            if self.s3_client:
                try:
                    self.s3_client.put_object(
                        Bucket=self.s3_bucket,
                        Key=file_path,
                        Body=file_content,
                        **extra_args
                    )
                    result["s3_url"] = f"https://{self.s3_bucket}.s3.amazonaws.com/{file_path}"
                    logger.info(f"Backed up to S3: {file_path}")
                except ClientError as e:
                    logger.warning(f"S3 backup failed: {str(e)}")

            return result

        except ClientError as e:
            logger.error(f"Upload failed: {str(e)}")
            raise

    async def upload_file_async(
        self,
        file_data: bytes,
        file_key: str,
        content_type: str = "application/octet-stream",
        metadata: Optional[dict] = None
    ) -> str:
        """
        Async wrapper used by services that run in async contexts.
        """
        result = self.upload_file(
            file_content=file_data,
            file_path=file_key,
            content_type=content_type,
            metadata=metadata
        )
        return result["r2_url"]


    def _normalize_mime_and_ext(self, content_type: str) -> tuple[str, str]:
        if not content_type:
            return 'application/octet-stream', 'bin'

        if '/' in content_type:
            mime = content_type
        elif content_type == 'image':
            mime = 'image/jpeg'
        elif content_type == 'video':
            mime = 'video/mp4'
        elif content_type == 'audio':
            mime = 'audio/mpeg'
        else:
            mime = 'application/octet-stream'

        mime_to_ext = {
            'image/jpeg': 'jpg',
            'image/png': 'png',
            'image/webp': 'webp',
            'video/mp4': 'mp4',
            'video/webm': 'webm',
            'video/quicktime': 'mov',
            'audio/mpeg': 'mp3',
            'audio/wav': 'wav'
        }
        return mime, mime_to_ext.get(mime, 'bin')

    async def upload_content_piece(
        self,
        avatar_id,
        content_data: bytes,
        content_type: str = 'image',
        tier: str = 'capa1'
    ) -> str:
        import uuid as uuid_pkg

        mime, ext = self._normalize_mime_and_ext(content_type)
        file_path = f"content/{avatar_id}/{uuid_pkg.uuid4()}.{ext}"

        result = self.upload_file(
            file_content=content_data,
            file_path=file_path,
            content_type=mime,
            metadata={
                'avatar_id': str(avatar_id),
                'tier': tier
            }
        )

        return result['r2_url']

    def generate_presigned_url(
        self,
        file_path: str,
        expiration: int = 3600,
        download_as: Optional[str] = None
    ) -> str:
        """
        Generate presigned URL for secure access

        Args:
            file_path: Path in bucket
            expiration: URL expiration time in seconds (default 1 hour)
            download_as: Force download with this filename

        Returns:
            Presigned URL
        """
        try:
            params = {
                'Bucket': self.r2_bucket,
                'Key': file_path
            }

            if download_as:
                params['ResponseContentDisposition'] = f'attachment; filename="{download_as}"'

            presigned_url = self.r2_client.generate_presigned_url(
                'get_object',
                Params=params,
                ExpiresIn=expiration
            )

            return presigned_url

        except ClientError as e:
            logger.error(f"Presigned URL generation failed: {str(e)}")
            raise

    def delete_file(self, file_path: str, delete_backup: bool = True) -> bool:
        """
        Delete file from R2 and optionally from S3 backup

        Args:
            file_path: Path in bucket
            delete_backup: Also delete from S3 backup

        Returns:
            Success status
        """
        try:
            # Delete from R2
            self.r2_client.delete_object(
                Bucket=self.r2_bucket,
                Key=file_path
            )
            logger.info(f"Deleted from R2: {file_path}")

            # Delete from S3 backup
            if delete_backup and self.s3_client:
                try:
                    self.s3_client.delete_object(
                        Bucket=self.s3_bucket,
                        Key=file_path
                    )
                    logger.info(f"Deleted from S3: {file_path}")
                except ClientError as e:
                    logger.warning(f"S3 deletion failed: {str(e)}")

            return True

        except ClientError as e:
            logger.error(f"Deletion failed: {str(e)}")
            return False

    def list_files(self, prefix: str = '', max_keys: int = 1000) -> list:
        """
        List files in bucket with optional prefix

        Args:
            prefix: Filter by prefix (e.g., 'avatars/uuid/')
            max_keys: Maximum number of keys to return

        Returns:
            List of file objects
        """
        try:
            response = self.r2_client.list_objects_v2(
                Bucket=self.r2_bucket,
                Prefix=prefix,
                MaxKeys=max_keys
            )

            return response.get('Contents', [])

        except ClientError as e:
            logger.error(f"List files failed: {str(e)}")
            return []

    def get_file_metadata(self, file_path: str) -> Optional[dict]:
        """
        Get file metadata from R2

        Args:
            file_path: Path in bucket

        Returns:
            File metadata
        """
        try:
            response = self.r2_client.head_object(
                Bucket=self.r2_bucket,
                Key=file_path
            )

            return {
                'size': response['ContentLength'],
                'content_type': response['ContentType'],
                'last_modified': response['LastModified'],
                'metadata': response.get('Metadata', {})
            }

        except ClientError as e:
            logger.error(f"Get metadata failed: {str(e)}")
            return None

    def upload_content_batch(
        self,
        content_files: list[dict],
        avatar_id: str
    ) -> list[dict]:
        """
        Upload batch of content files to R2

        Args:
            content_files: List of dicts with 'file_content', 'file_name', 'content_type', 'metadata'
            avatar_id: Avatar ID for organizing files

        Returns:
            List of upload results with URLs
        """
        results = []

        for idx, file_info in enumerate(content_files):
            try:
                file_content = file_info['file_content']
                file_name = file_info.get('file_name', f'content_{idx}.jpg')
                content_type = file_info.get('content_type', 'image/jpeg')
                metadata = file_info.get('metadata', {})

                # Generate file path
                file_path = f"content/{avatar_id}/{file_name}"

                # Add batch metadata
                metadata['batch_upload'] = 'true'
                metadata['batch_index'] = str(idx)
                metadata['avatar_id'] = avatar_id

                # Upload file
                upload_result = self.upload_file(
                    file_content=file_content,
                    file_path=file_path,
                    content_type=content_type,
                    metadata=metadata
                )

                results.append({
                    'success': True,
                    'file_name': file_name,
                    'file_path': file_path,
                    'r2_url': upload_result['r2_url'],
                    's3_url': upload_result.get('s3_url'),
                    'index': idx
                })

            except Exception as e:
                logger.error(f"Batch upload failed for file {idx}: {str(e)}")
                results.append({
                    'success': False,
                    'file_name': file_info.get('file_name', f'content_{idx}.jpg'),
                    'error': str(e),
                    'index': idx
                })

        return results

    def get_cdn_url(self, file_path: str) -> str:
        """
        Get CDN URL for a file (public R2 URL)

        Args:
            file_path: Path in bucket

        Returns:
            Public CDN URL
        """
        # Cloudflare R2 public URL
        public_url = f"{os.getenv('R2_PUBLIC_URL')}/{file_path}"

        return public_url

    def get_cdn_urls_batch(self, file_paths: list[str]) -> list[str]:
        """
        Get CDN URLs for batch of files

        Args:
            file_paths: List of file paths in bucket

        Returns:
            List of public CDN URLs
        """
        return [self.get_cdn_url(path) for path in file_paths]

    def download_file(self, file_path: str) -> Optional[bytes]:
        """
        Download file content from R2

        Args:
            file_path: Path in bucket

        Returns:
            File content as bytes
        """
        try:
            response = self.r2_client.get_object(
                Bucket=self.r2_bucket,
                Key=file_path
            )

            return response['Body'].read()

        except ClientError as e:
            logger.error(f"Download failed: {str(e)}")
            return None

    def copy_file(self, source_path: str, destination_path: str) -> bool:
        """
        Copy file within R2 bucket

        Args:
            source_path: Source file path
            destination_path: Destination file path

        Returns:
            Success status
        """
        try:
            self.r2_client.copy_object(
                Bucket=self.r2_bucket,
                CopySource={'Bucket': self.r2_bucket, 'Key': source_path},
                Key=destination_path
            )

            logger.info(f"Copied {source_path} to {destination_path}")
            return True

        except ClientError as e:
            logger.error(f"Copy failed: {str(e)}")
            return False

# Singleton instance
storage_service = StorageService()
