from typing import Literal

from pydantic import BaseModel, Field


InspectionArea = Literal["Ceiling", "Walls", "Windows", "Floor", "Electrical outlets"]
RiskLevel = Literal["Safe", "Low Risk", "Medium Risk", "High Risk", "Critical Risk"]
AreaStatus = Literal["checked", "issue_found", "not_visible", "needs_more_photo"]


class BoundingBox(BaseModel):
    x: int = Field(ge=0)
    y: int = Field(ge=0)
    width: int = Field(gt=0)
    height: int = Field(gt=0)


class AnnotationRegion(BaseModel):
    markerNumber: int = Field(ge=1)
    bbox: BoundingBox


class AreaResult(BaseModel):
    name: InspectionArea
    visible: bool
    status: AreaStatus
    confidence: int | None = Field(default=None, ge=0, le=100)
    note: str


class DetectedIssue(BaseModel):
    id: str
    photoIndex: int = Field(ge=0)
    area: InspectionArea
    issueType: str
    riskLevel: RiskLevel
    confidence: int = Field(ge=0, le=100)
    location: str
    description: str
    details: str
    recommendation: str
    bbox: BoundingBox | None = None
    annotations: list[AnnotationRegion] = Field(default_factory=list)


class PublicDetectedIssue(BaseModel):
    id: str
    photoIndex: int = Field(ge=0)
    area: InspectionArea
    issueType: str
    riskLevel: RiskLevel
    confidence: int = Field(ge=0, le=100)
    location: str
    description: str
    details: str
    recommendation: str


class ReportFinding(BaseModel):
    id: str
    area: InspectionArea
    issueType: str
    riskLevel: RiskLevel
    confidence: int = Field(ge=0, le=100)
    location: str
    details: str
    recommendedAction: str
    imageUrl: str | None = None
    annotatedImageUrl: str | None = None
    markerNumbers: list[int] = Field(default_factory=list)


class RecommendedAction(BaseModel):
    issueType: str
    area: InspectionArea
    riskLevel: RiskLevel
    description: str
    action: str


class SeveritySummaryItem(BaseModel):
    key: str
    label: RiskLevel
    count: int = Field(ge=0)
    percentage: int = Field(ge=0, le=100)


class OverallRisk(BaseModel):
    score: int = Field(ge=0, le=100)
    level: RiskLevel
    breakdown: dict[str, int]
    breakdownPercentages: dict[str, int] = Field(default_factory=dict)


class ReportOverview(BaseModel):
    propertyName: str
    propertyAddress: str
    inspectionDate: str
    inspector: str
    executiveSummary: str


class ReportPreview(BaseModel):
    overview: ReportOverview
    findings: list[ReportFinding]
    recommendations: list[RecommendedAction]


class RoomAnalysis(BaseModel):
    analysisId: str
    userId: str
    roomId: str
    roomName: str
    status: Literal["completed"]
    photosAnalyzed: int
    issuesFound: int
    originalImageUrls: list[str]
    annotatedImageUrl: str | None
    annotatedImages: list[str]
    severitySummary: dict[str, int]
    severityLevelSummary: list[SeveritySummaryItem] = Field(default_factory=list)
    overallRisk: OverallRisk
    aiInsightSummary: list[str]
    recommendedActions: list[RecommendedAction]
    detectedIssues: list[DetectedIssue]
    areas: list[AreaResult]
    reportPreview: ReportPreview | None = None


class RoomAnalysisResponse(BaseModel):
    analysisId: str
    userId: str
    roomId: str
    roomName: str
    status: Literal["completed"]
    photosAnalyzed: int
    issuesFound: int
    originalImageUrls: list[str]
    annotatedImageUrl: str | None
    annotatedImages: list[str]
    severitySummary: dict[str, int]
    severityLevelSummary: list[SeveritySummaryItem] = Field(default_factory=list)
    overallRisk: OverallRisk
    aiInsightSummary: list[str]
    recommendedActions: list[RecommendedAction]
    detectedIssues: list[PublicDetectedIssue]
    areas: list[AreaResult]
    reportPreview: ReportPreview | None = None


class ConfirmAnalysisRequest(BaseModel):
    action: Literal["confirmed", "skipped", "edited"]
    userNotes: str | None = None
    confirmedIssueIds: list[str] = Field(default_factory=list)
    removedIssueIds: list[str] = Field(default_factory=list)


class ConfirmAnalysisResponse(BaseModel):
    userId: str
    roomId: str
    status: Literal["saved"]
