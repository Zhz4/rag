from pydantic import BaseModel, Field
from typing import List
from fastapi import UploadFile


class Question(BaseModel):
    """用户提问的模型类"""
    text: str = Field(..., description="问题内容")
    session_id: str = Field(..., description="会话ID")
    user_id: str = Field(..., description="用户ID")


class Answer(BaseModel):
    """回答的模型类"""
    question: str = Field(..., description="问题内容")
    answer: str = Field(..., description="回答内容")


class DeleteDocumentsRequest(BaseModel):
    """删除文档请求的模型类"""
    file_paths: List[str] = Field(..., description="要删除的文件路径列表")


class UploadFilesRequest(BaseModel):
    """上传文件请求的模型类"""
    files: List[UploadFile] = Field(..., description="要上传的文件列表")
