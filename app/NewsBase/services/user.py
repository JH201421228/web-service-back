from typing import Optional, Tuple

from sqlalchemy.orm import Session

from app.NewsBase.models.user import User


def get_user_by_uid(db: Session, uid: str) -> Optional[User]:
    """UID로 사용자 조회"""
    return db.query(User).filter(User.uid == uid).first()


def create_user(
    db: Session,
    uid: str,
    email: Optional[str] = None,
    name: Optional[str] = None,
    picture: Optional[str] = None,
) -> User:
    """새 사용자 생성"""
    user = User(
        uid=uid,
        email=email,
        name=name,
        picture=picture,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_user(
    db: Session,
    user: User,
    email: Optional[str] = None,
    name: Optional[str] = None,
    picture: Optional[str] = None,
) -> User:
    """사용자 정보 업데이트"""
    if email is not None:
        user.email = email
    if name is not None:
        user.name = name
    if picture is not None:
        user.picture = picture
    
    db.commit()
    db.refresh(user)
    return user


def get_or_create_user(
    db: Session,
    uid: str,
    email: Optional[str] = None,
    name: Optional[str] = None,
    picture: Optional[str] = None,
) -> Tuple[User, bool]:
    """
    사용자 조회 또는 생성
    
    Returns:
        Tuple[User, bool]: (사용자 객체, 신규 사용자 여부)
    """
    user = get_user_by_uid(db, uid)
    
    if user:
        # 기존 사용자: 정보 업데이트 (변경된 경우만)
        updated = False
        if email and user.email != email:
            user.email = email
            updated = True
        if name and user.name != name:
            user.name = name
            updated = True
        if picture and user.picture != picture:
            user.picture = picture
            updated = True
        
        if updated:
            db.commit()
            db.refresh(user)
        
        return user, False
    
    # 신규 사용자 생성
    new_user = create_user(db, uid, email, name, picture)
    return new_user, True

