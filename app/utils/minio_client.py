from minio import Minio
from minio.error import S3Error
from app.config.index import settings
from app.logging.logging import logger
import os
from typing import List


class MinioClient:
    def __init__(self):
        self.client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE,
        )
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self):
        """确保存储桶存在"""
        try:
            if not self.client.bucket_exists(settings.MINIO_BUCKET_NAME):
                self.client.make_bucket(settings.MINIO_BUCKET_NAME)
                logger.info(f"Bucket {settings.MINIO_BUCKET_NAME} created successfully")
        except S3Error as e:
            logger.error(f"Error checking/creating bucket: {e}")
            raise

    async def upload_file(self, file_path: str, object_name: str = None) -> str:
        """上传文件到MinIO

        Args:
            file_path: 本地文件路径
            object_name: MinIO中的对象名称，如果为None则使用文件名

        Returns:
            str: 文件的访问URL
        """
        try:
            if not object_name:
                object_name = os.path.basename(file_path)

            self.client.fput_object(settings.MINIO_BUCKET_NAME, object_name, file_path)

            # 生成文件URL
            url = self.client.presigned_get_object(
                settings.MINIO_BUCKET_NAME, object_name
            )
            return url
        except S3Error as e:
            logger.error(f"Error uploading file to MinIO: {e}")
            raise

    async def delete_file(self, object_name: str):
        """从MinIO删除文件"""
        try:
            self.client.remove_object(settings.MINIO_BUCKET_NAME, object_name)
        except S3Error as e:
            logger.error(f"Error deleting file from MinIO: {e}")
            raise

    async def list_files(self) -> List[str]:
        """列出所有文件"""
        try:
            objects = self.client.list_objects(settings.MINIO_BUCKET_NAME)
            return [obj.object_name for obj in objects]
        except S3Error as e:
            logger.error(f"Error listing files from MinIO: {e}")
            raise
