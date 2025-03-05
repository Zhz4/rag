from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException
from app.api.response import error_response


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """请求参数验证异常处理"""
    return JSONResponse(
        status_code=422,
        content=error_response(code=422, message=f"参数验证错误: {str(exc.errors())}"),
    )


async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP异常处理"""
    return JSONResponse(
        status_code=200,
        content=error_response(code=exc.status_code, message=str(exc.detail)),
    )


async def general_exception_handler(request: Request, exc: Exception):
    """通用异常处理"""
    return JSONResponse(
        status_code=200,
        content=error_response(code=500, message=f"服务器内部错误: {str(exc)}"),
    )
