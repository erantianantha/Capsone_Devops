from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db

router = APIRouter(prefix="/api/items", tags=["items"])

EXPIRING_SOON_DAYS = 3


def _get_or_404(db: Session, item_id: int) -> models.PantryItem:
    item = db.get(models.PantryItem, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@router.get("", response_model=list[schemas.ItemOut])
def list_items(
    category: str | None = None,
    search: str | None = Query(default=None, max_length=120),
    db: Session = Depends(get_db),
):
    stmt = select(models.PantryItem)
    if category:
        stmt = stmt.where(models.PantryItem.category == category)
    if search:
        stmt = stmt.where(models.PantryItem.name.ilike(f"%{search}%"))
    # Items without an expiry date sort last
    stmt = stmt.order_by(models.PantryItem.expiry_date.is_(None), models.PantryItem.expiry_date, models.PantryItem.id)
    return db.scalars(stmt).all()


@router.get("/stats", response_model=schemas.Stats)
def item_stats(db: Session = Depends(get_db)):
    today = date.today()
    soon = today + timedelta(days=EXPIRING_SOON_DAYS)
    total = db.scalar(select(func.count(models.PantryItem.id))) or 0
    expired = db.scalar(select(func.count()).where(models.PantryItem.expiry_date < today)) or 0
    expiring = (
        db.scalar(
            select(func.count()).where(
                models.PantryItem.expiry_date >= today, models.PantryItem.expiry_date <= soon
            )
        )
        or 0
    )
    rows = db.execute(
        select(models.PantryItem.category, func.count()).group_by(models.PantryItem.category)
    ).all()
    return schemas.Stats(
        total_items=total, expiring_soon=expiring, expired=expired, by_category={c: n for c, n in rows}
    )


@router.get("/{item_id}", response_model=schemas.ItemOut)
def get_item(item_id: int, db: Session = Depends(get_db)):
    return _get_or_404(db, item_id)


@router.post("", response_model=schemas.ItemOut, status_code=status.HTTP_201_CREATED)
def create_item(payload: schemas.ItemCreate, db: Session = Depends(get_db)):
    item = models.PantryItem(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.put("/{item_id}", response_model=schemas.ItemOut)
def update_item(item_id: int, payload: schemas.ItemUpdate, db: Session = Depends(get_db)):
    item = _get_or_404(db, item_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(item_id: int, db: Session = Depends(get_db)):
    item = _get_or_404(db, item_id)
    db.delete(item)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
