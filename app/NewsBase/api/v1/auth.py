from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.NewsBase.core.deps import get_current_user, get_db
from app.NewsBase.schemas.user import LoginResponse, UserResponse
from app.NewsBase.services.user import get_or_create_user, get_user_by_uid

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=LoginResponse)
async def login(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Firebase ID Token 검증 후 사용자 정보 반환
    
    - 프론트엔드에서 Firebase 로그인 후 ID Token을 Bearer 토큰으로 전송
    - 백엔드에서 토큰 검증 후 사용자 정보 반환
    - 신규 사용자는 DB에 자동 생성
    """
    uid = current_user["uid"]
    email = current_user.get("email")
    name = current_user.get("name")
    picture = current_user.get("picture")

    # DB에서 사용자 조회/생성
    user, is_new_user = get_or_create_user(
        db=db,
        uid=uid,
        email=email,
        name=name,
        picture=picture,
    )

    return LoginResponse(
        message="Login successful",
        user=UserResponse(
            uid=user.uid,
            email=user.email,
            name=user.name,
            picture=user.picture,
            is_new_user=is_new_user,
        ),
    )


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    현재 로그인한 사용자 정보 조회
    
    - Authorization 헤더에 Bearer 토큰 필요
    - DB에서 사용자 정보 조회
    """
    user = get_user_by_uid(db, current_user["uid"])
    
    if user:
        return UserResponse(
            uid=user.uid,
            email=user.email,
            name=user.name,
            picture=user.picture,
        )
    
    # DB에 없으면 Firebase 토큰 정보 반환
    return UserResponse(
        uid=current_user["uid"],
        email=current_user.get("email"),
        name=current_user.get("name"),
        picture=current_user.get("picture"),
    )
