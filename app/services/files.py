from sqlalchemy.orm import Session
from app.utils.mysql_client import MySQLClient
from app.db.models.chat import files
from fastapi import HTTPException
from fastapi import UploadFile
from pathlib import Path
from fastapi import File

class Files:
    def __init__(self, db: Session):
        self.db = db

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
            # 确保 books 目录存在
            books_dir = Path("books")
            books_dir.mkdir(exist_ok=True)
            
            for file in upload_files:
                # 构建文件保存路径
                file_path = books_dir / file.filename

                # 写入文件
                content = await file.read()
                with open(file_path, "wb") as f:
                    f.write(content)

                # 直接保存文件信息到数据库
                file_info = files(
                    file_local_path=str(file_path),
                    # TODO: 改成文件的url
                    file_path=str(file_path),
                )
                self.create_file(file_info)

            return {
                "message": "文件上传成功",
                "uploaded_files": [file.filename for file in upload_files],
                "total_files": len(upload_files),
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")
