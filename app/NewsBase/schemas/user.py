from pydantic import BaseModel
from typing import Optional


class UserResponse(BaseModel):
    """사용자 정보 응답 스키마"""
    
    uid: str
    email: Optional[str] = None
    name: Optional[str] = None
    picture: Optional[str] = None
    is_new_user: bool = False


class LoginResponse(BaseModel):
    """로그인 응답 스키마"""
    
    message: str
    user: UserResponse

