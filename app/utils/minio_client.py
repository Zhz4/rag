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

    async def upload_file_bytes(self, file_bytes: bytes, object_name: str) -> str:
        """上传文件字节流到MinIO

        Args:
            file_bytes: 文件字节流
            object_name: MinIO中的对象名称

        Returns:
            str: 文件的访问URL
        """
        try:
            from io import BytesIO

            file_stream = BytesIO(file_bytes)

            # 上传到 MinIO
            self.client.put_object(
                bucket_name=settings.MINIO_BUCKET_NAME,
                object_name=object_name,
                data=file_stream,
                length=len(file_bytes),
            )

            # 生成文件URL
            url = self.client.presigned_get_object(
                settings.MINIO_BUCKET_NAME, object_name
            )
            return url
        except S3Error as e:
            logger.error(f"Error uploading file to MinIO: {e}")
            raise

    async def download_file(self, object_name: str, local_path: str) -> str:
        """从MinIO下载文件到本地临时目录

        Args:
            object_name: MinIO中的对象名称
            local_path: 本地保存路径

        Returns:
            str: 下载文件的本地路径
        """
        try:
            self.client.fget_object(settings.MINIO_BUCKET_NAME, object_name, local_path)
            return local_path
        except S3Error as e:
            logger.error(f"Error downloading file from MinIO: {e}")
            raise
