from typing import TypeVar, Generic, Optional, Any
from pydantic import BaseModel

T = TypeVar("T")


class ResponseModel(BaseModel, Generic[T]):
    """统一响应模型"""

    code: int = 200
    message: str = "success"
    data: Optional[T] = None


def success_response(data: Any = None, message: str = "success") -> dict:
    """成功响应"""
    return {"code": 200, "message": message, "data": data}


def error_response(code: int = 500, message: str = "服务器内部错误") -> dict:
    """错误响应"""
    return {"code": code, "message": message, "data": None}
