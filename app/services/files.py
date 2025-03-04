from sqlalchemy.orm import Session
from app.utils.mysql_client import MySQLClient
from app.db.models.chat import files
from fastapi import HTTPException
from fastapi import UploadFile
from pathlib import Path
from fastapi import File
import shutil


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
                    # TODO: 改成文件真实的url
                    file_path=str(f'https://https://microservices.yswg.com.cn/{file_path}'),
                )
                self.create_file(file_info)

            return {
                "message": "文件上传成功",
                "uploaded_files": [file.filename for file in upload_files],
                "total_files": len(upload_files),
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")

    async def files_study(self):
        """设置文件为已学习状态"""
        try:
            # 将 books 目录的文件移动到 ReadBooks 目录
            books_dir = Path("books")
            readbooks_dir = Path("ReadBooks")
            # 确保 ReadBooks 目录存在
            readbooks_dir.mkdir(exist_ok=True)

            if books_dir.exists():
                for file in books_dir.iterdir():
                    if file.is_file():
                        # 更新数据库中对应文件的状态
                        db_file = (
                            self.db.query(files)
                            .filter(files.file_local_path == str(file))
                            .first()
                        )

                        if db_file:
                            db_file.is_study = True
                            self.db.commit()

                        # 移动文件
                        target_path = readbooks_dir / file.name
                        shutil.copy2(file, target_path)  # 复制文件
                        file.unlink()  # 删除原文件

            return {"message": "文件学习状态更新成功"}
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"文件学习失败: {str(e)}")
