from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from app.backend.models.category import Category, CategoryCreate, CategoryUpdate
from app.backend.models.user import User
from app.backend.deps import get_current_active_user, get_db
from app.core.database import db as db_core
import uuid
from datetime import datetime
import pymongo
from bson.objectid import ObjectId

router = APIRouter()

@router.post("/", response_model=Category, status_code=status.HTTP_201_CREATED)
def create_category(
    category_in: CategoryCreate,
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db)
):
    """Create a new category"""
    try:
        # Check if category name already exists for this account
        existing_category = db["categories"].find_one({
            "category_name": category_in.category_name,
            "account_id": current_user.account_id
        })
        
        if existing_category:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Category '{category_in.category_name}' already exists"
            )
        
        category_doc = category_in.dict()
        category_doc["category_id"] = str(uuid.uuid4())
        category_doc["account_id"] = current_user.account_id
        category_doc["created_at"] = datetime.utcnow()
        category_doc["updated_at"] = datetime.utcnow()

        result = db["categories"].insert_one(category_doc)
        
        if not result.inserted_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create category"
            )
            
        # Fetch the created category
        created_category = db["categories"].find_one({"_id": result.inserted_id})
        return db_core.serialize_doc(created_category)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating category: {str(e)}"
        )

@router.get("/", response_model=List[Category])
def list_categories(
    search: Optional[str] = Query(None, description="Search by category name"),
    status_filter: Optional[str] = Query(None, description="Filter by status: active or inactive"),
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db)
):
    """List all categories for the current user's account"""
    try:
        query = {"account_id": current_user.account_id}
        
        if search and search.strip():
            query["$or"] = [
                {"category_name": {"$regex": search.strip(), "$options": "i"}},
                {"description": {"$regex": search.strip(), "$options": "i"}}
            ]
        
        if status_filter and status_filter in ["active", "inactive"]:
            query["status"] = status_filter
        
        categories = list(db["categories"]
                         .find(query)
                         .sort([("category_name", pymongo.ASCENDING)]))
        
        return db_core.serialize_list(categories)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching categories: {str(e)}"
        )

@router.get("/{category_id}", response_model=Category)
def get_category(
    category_id: str,
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db)
):
    """Get a specific category by ID"""
    try:
        category = db["categories"].find_one({
            "category_id": category_id,
            "account_id": current_user.account_id
        })
        
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found or you don't have access to it"
            )
            
        return db_core.serialize_doc(category)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching category: {str(e)}"
        )

@router.put("/{category_id}", response_model=Category)
def update_category(
    category_id: str,
    category_in: CategoryUpdate,
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db)
):
    """Update a category"""
    try:
        query = {
            "category_id": category_id,
            "account_id": current_user.account_id
        }
        
        # Check if category exists
        existing_category = db["categories"].find_one(query)
        if not existing_category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )
        
        # Check for duplicate name (excluding current category)
        if category_in.category_name:
            duplicate = db["categories"].find_one({
                "category_name": category_in.category_name,
                "account_id": current_user.account_id,
                "category_id": {"$ne": category_id}
            })
            
            if duplicate:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Category name '{category_in.category_name}' already exists"
                )
        
        update_data = category_in.dict(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow()
        
        # Perform update
        result = db["categories"].update_one(
            query,
            {"$set": update_data}
        )
        
        # Fetch updated category
        updated_category = db["categories"].find_one(query)
        return db_core.serialize_doc(updated_category)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating category: {str(e)}"
        )

@router.delete("/{category_id}", status_code=status.HTTP_200_OK)
def delete_category(
    category_id: str,
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db)
):
    """Delete a category"""
    try:
        # Check if category exists and belongs to user
        category = db["categories"].find_one({
            "category_id": category_id,
            "account_id": current_user.account_id
        })
        
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )
        
        # Check if items exist in this category
        item_count = db["items"].count_documents({
            "category_id": category_id,
            "account_id": current_user.account_id
        })
        
        if item_count > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete category. {item_count} item(s) are associated with this category."
            )
        
        # Delete category
        result = db["categories"].delete_one({
            "category_id": category_id,
            "account_id": current_user.account_id
        })
        
        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete category"
            )
            
        return {
            "message": "Category deleted successfully",
            "deleted_count": result.deleted_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting category: {str(e)}"
        )
