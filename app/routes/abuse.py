from fastapi import APIRouter, Depends, HTTPException
from app.models.abuse import AbuseReportCreate, AbuseReportResponse, AbuseReportUpdate, AbuseType
from app.models.user import TokenUser
from app.utils.auth import get_current_user
from app.utils.sanitizer import InputSanitizer
from app.database import db
from bson import ObjectId
from datetime import datetime, timezone
from typing import List, Optional

router = APIRouter(prefix="/abuse", tags=["Abuse Reports"])

@router.post("/report", response_model=AbuseReportResponse)
async def create_abuse_report(
    report_data: AbuseReportCreate,
    user: TokenUser = Depends(get_current_user)
):
    """Create an abuse report"""
    
    # 1. Sanitize input
    description = InputSanitizer.sanitize_text(report_data.description, max_length=500)
    
    # 2. Validate target exists
    if report_data.target_type == "listing":
        target = await db.listings.find_one({"_id": ObjectId(report_data.target_id)})
    elif report_data.target_type == "message":
        target = await db.messages.find_one({"_id": ObjectId(report_data.target_id)})
    elif report_data.target_type == "user":
        target = await db.users.find_one({"_id": ObjectId(report_data.target_id)})
    else:
        raise HTTPException(status_code=400, detail="Invalid target type")
    
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")
    
    # 3. Check if user already reported this target
    existing_report = await db.abuse_reports.find_one({
        "reporter_id": ObjectId(user.id),
        "target_type": report_data.target_type,
        "target_id": ObjectId(report_data.target_id),
        "status": {"$in": ["pending", "reviewed"]}
    })
    
    if existing_report:
        raise HTTPException(
            status_code=400,
            detail="You have already reported this content"
        )
    
    # 4. Create abuse report
    report_doc = {
        "reporter_id": ObjectId(user.id),
        "target_type": report_data.target_type,
        "target_id": ObjectId(report_data.target_id),
        "abuse_type": report_data.abuse_type.value,
        "description": description,
        "evidence_urls": report_data.evidence_urls or [],
        "status": "pending",
        "created_at": datetime.now(timezone.utc)
    }
    
    result = await db.abuse_reports.insert_one(report_doc)
    
    return AbuseReportResponse(
        id=str(result.inserted_id),
        reporter_id=user.id,
        target_type=report_data.target_type,
        target_id=report_data.target_id,
        abuse_type=report_data.abuse_type,
        description=description,
        evidence_urls=report_data.evidence_urls,
        status="pending",
        created_at=report_doc["created_at"]
    )

@router.get("/my-reports", response_model=List[AbuseReportResponse])
async def get_my_reports(user: TokenUser = Depends(get_current_user)):
    """Get all abuse reports created by the current user"""
    
    reports_cursor = db.abuse_reports.find(
        {"reporter_id": ObjectId(user.id)}
    ).sort("created_at", -1)
    
    reports = await reports_cursor.to_list(length=None)
    
    result = []
    for report in reports:
        result.append(AbuseReportResponse(
            id=str(report["_id"]),
            reporter_id=str(report["reporter_id"]),
            target_type=report["target_type"],
            target_id=str(report["target_id"]),
            abuse_type=AbuseType(report["abuse_type"]),
            description=report["description"],
            evidence_urls=report.get("evidence_urls", []),
            status=report["status"],
            created_at=report["created_at"],
            reviewed_at=report.get("reviewed_at"),
            reviewed_by=str(report["reviewed_by"]) if report.get("reviewed_by") else None,
            admin_notes=report.get("admin_notes")
        ))
    
    return result

@router.get("/admin/pending", response_model=List[AbuseReportResponse])
async def get_pending_reports(user: TokenUser = Depends(get_current_user)):
    """Get all pending abuse reports (admin only)"""
    
    # Check if user is admin
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    reports_cursor = db.abuse_reports.find(
        {"status": "pending"}
    ).sort("created_at", -1)
    
    reports = await reports_cursor.to_list(length=None)
    
    result = []
    for report in reports:
        result.append(AbuseReportResponse(
            id=str(report["_id"]),
            reporter_id=str(report["reporter_id"]),
            target_type=report["target_type"],
            target_id=str(report["target_id"]),
            abuse_type=AbuseType(report["abuse_type"]),
            description=report["description"],
            evidence_urls=report.get("evidence_urls", []),
            status=report["status"],
            created_at=report["created_at"],
            reviewed_at=report.get("reviewed_at"),
            reviewed_by=str(report["reviewed_by"]) if report.get("reviewed_by") else None,
            admin_notes=report.get("admin_notes")
        ))
    
    return result

@router.put("/admin/{report_id}", response_model=AbuseReportResponse)
async def update_abuse_report(
    report_id: str,
    update_data: AbuseReportUpdate,
    user: TokenUser = Depends(get_current_user)
):
    """Update an abuse report (admin only)"""
    
    # Check if user is admin
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Check if report exists
    report = await db.abuse_reports.find_one({"_id": ObjectId(report_id)})
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    # Prepare update data
    update_dict = {}
    
    if update_data.status is not None:
        update_dict["status"] = update_data.status
    
    if update_data.admin_notes is not None:
        update_dict["admin_notes"] = InputSanitizer.sanitize_text(update_data.admin_notes, max_length=1000)
    
    if not update_dict:
        raise HTTPException(status_code=400, detail="No valid fields to update")
    
    update_dict["reviewed_at"] = datetime.now(timezone.utc)
    update_dict["reviewed_by"] = ObjectId(user.id)
    
    # Update report
    await db.abuse_reports.update_one(
        {"_id": ObjectId(report_id)},
        {"$set": update_dict}
    )
    
    # Get updated report
    updated_report = await db.abuse_reports.find_one({"_id": ObjectId(report_id)})
    
    return AbuseReportResponse(
        id=str(updated_report["_id"]),
        reporter_id=str(updated_report["reporter_id"]),
        target_type=updated_report["target_type"],
        target_id=str(updated_report["target_id"]),
        abuse_type=AbuseType(updated_report["abuse_type"]),
        description=updated_report["description"],
        evidence_urls=updated_report.get("evidence_urls", []),
        status=updated_report["status"],
        created_at=updated_report["created_at"],
        reviewed_at=updated_report.get("reviewed_at"),
        reviewed_by=str(updated_report["reviewed_by"]) if updated_report.get("reviewed_by") else None,
        admin_notes=updated_report.get("admin_notes")
    )

@router.post("/admin/{report_id}/take-action")
async def take_action_on_report(
    report_id: str,
    action: str,
    user: TokenUser = Depends(get_current_user)
):
    """Take action on an abuse report (admin only)"""
    
    # Check if user is admin
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Check if report exists
    report = await db.abuse_reports.find_one({"_id": ObjectId(report_id)})
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    target_id = report["target_id"]
    target_type = report["target_type"]
    
    # Take action based on target type
    if action == "remove_content":
        if target_type == "listing":
            await db.listings.update_one(
                {"_id": target_id},
                {"$set": {"is_removed": True, "removed_at": datetime.now(timezone.utc), "removed_reason": "Abuse report"}}
            )
        elif target_type == "message":
            await db.messages.update_one(
                {"_id": target_id},
                {"$set": {"is_removed": True, "removed_at": datetime.now(timezone.utc), "removed_reason": "Abuse report"}}
            )
        elif target_type == "user":
            await db.users.update_one(
                {"_id": target_id},
                {"$set": {"is_suspended": True, "suspended_at": datetime.now(timezone.utc), "suspended_reason": "Abuse report"}}
            )
    
    elif action == "warn_user":
        # Add warning to user
        target_user_id = target_id if target_type == "user" else report.get("target_user_id")
        if target_user_id:
            await db.users.update_one(
                {"_id": ObjectId(target_user_id)},
                {"$inc": {"warning_count": 1}}
            )
    
    # Update report status
    await db.abuse_reports.update_one(
        {"_id": ObjectId(report_id)},
        {
            "$set": {
                "status": "action_taken",
                "action_taken": action,
                "reviewed_at": datetime.now(timezone.utc),
                "reviewed_by": ObjectId(user.id)
            }
        }
    )
    
    return {"message": f"Action '{action}' taken on report successfully"}
