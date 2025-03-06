from sqlalchemy.orm import Session
from app.utils.mysql_client import MySQLClient
from app.db.models.chat import files
from fastapi import HTTPException
from fastapi import UploadFile
from pathlib import Path
from fastapi import File
import shutil
from app.utils.minio_client import MinioClient


class Files:
    def __init__(self, db: Session):
        self.db = db
        self.minio = MinioClient()

    def create_file(self, file: files):
        try:
            self.db.add(file)
            self.db.commit()
            self.db.refresh(file)
            return file
        except Exception as e:
            self.db.rollback()
            raise e

    async def uploadfile(self, upload_files: list[UploadFile] = File(...)):
        """上传文档"""
        try:
            results = []
            for file in upload_files:
                # 读取文件内容
                content = await file.read()

                # 直接上传到MinIO
                file_url = await self.minio.upload_file_bytes(
                    file_bytes=content, object_name=file.filename
                )

                # 保存文件信息到数据库
                file_info = files(
                    file_name=file.filename,
                    file_path=file_url,
                )
                self.create_file(file_info)

                results.append(file.filename)

            return {
                "message": "文件上传成功",
                "uploaded_files": results,
                "total_files": len(results),
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")

    async def files_study(self):
        """设置文件为已学习状态"""
        try:
            # 更新所有未学习文件的状态
            unprocessed_files = self.db.query(files).filter(
                files.is_study == False, files.is_deleted == False
            )

            for file in unprocessed_files:
                file.is_study = True

            self.db.commit()
            return {"message": "文件学习状态更新成功"}
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"文件学习失败: {str(e)}")
