"""Núcleo do laboratório de agentes para governança PDM/BOM."""

from .catalog_quality import (
    CatalogQualityReport,
    diagnose_catalog_quality,
)
from .catalog_quality_use_case import (
    CatalogDiagnosticPipeline,
    DiagnoseCatalogQualityUseCase,
)
from .decision_recommendation_benchmark_use_case import (
    DecisionRecommendationBenchmarkCase,
    RunDecisionRecommendationBenchmarkUseCase,
)
from .domain import (
    GovernanceAssessment,
    GovernanceDecision,
    GovernanceIssue,
    IssueSeverity,
    IssueType,
    MaterialRecord,
)
from .ground_truth import (
    DecisionRecommendationGroundTruth,
    DecisionRecommendationGroundTruthDataset,
    DuplicatePairGroundTruth,
    DuplicatePairGroundTruthDataset,
    LabelProvenance,
    MaterialRuleGroundTruth,
    MaterialRuleGroundTruthDataset,
)
from .ground_truth_evaluation import (
    DecisionRecommendationCaseEvaluation,
    DecisionRecommendationEvaluationReport,
    DuplicatePairCaseEvaluation,
    DuplicatePairEvaluationReport,
    DuplicatePairPrediction,
    MaterialRuleCaseEvaluation,
    MaterialRuleEvaluationReport,
    MaterialRulePrediction,
    evaluate_decision_recommendation,
    evaluate_decision_recommendations,
    evaluate_duplicate_pair,
    evaluate_duplicate_pairs,
    evaluate_material_rule,
    evaluate_material_rules,
)
from .ground_truth_serialization import (
    RECORD_TYPE_DECISION_RECOMMENDATION_GROUND_TRUTH,
    RECORD_TYPE_DUPLICATE_PAIR_GROUND_TRUTH,
    RECORD_TYPE_MATERIAL_RULE_GROUND_TRUTH,
    decision_recommendation_ground_truth_from_record,
    decision_recommendation_ground_truth_to_record,
    duplicate_pair_ground_truth_from_record,
    duplicate_pair_ground_truth_to_record,
    material_rule_ground_truth_from_record,
    material_rule_ground_truth_to_record,
)
from .human_review_claim import (
    HumanReviewClaim,
    HumanReviewClaimRelease,
    claim_pending_human_review,
    release_human_review_claim,
)
from .human_review_claim_repository import (
    DuplicateHumanReviewClaimError,
    HumanReviewClaimCorruptionError,
    HumanReviewClaimPersistenceError,
    HumanReviewClaimRepository,
    JsonlHumanReviewClaimRepository,
)
from .human_review_claim_release_repository import (
    DuplicateHumanReviewClaimReleaseError,
    HumanReviewClaimReleaseCorruptionError,
    HumanReviewClaimReleasePersistenceError,
    HumanReviewClaimReleaseRepository,
    JsonlHumanReviewClaimReleaseRepository,
)
from .human_review_claim_projection import (
    HumanReviewClaimFactState,
    HumanReviewClaimState,
    ReleaseAwareClaimState,
    project_human_review_claim_state,
    project_release_aware_claim_state,
)
from .human_review_claim_serialization import (
    human_review_claim_from_record,
    human_review_claim_to_record,
)
from .human_review_claim_release_serialization import (
    human_review_claim_release_from_record,
    human_review_claim_release_to_record,
)
from .human_review_claim_use_case import RecordHumanReviewClaimUseCase
from .human_review_claim_release_use_case import (
    ReleaseHumanReviewClaimUseCase,
)
from .reviewer_eligibility_policy import (
    ReviewerEligibilityDecision,
    ReviewerEligibilityStatus,
    evaluate_release_aware_reviewer_claim_eligibility,
    evaluate_reviewer_claim_eligibility,
)
from .validator import DeterministicGovernanceValidator

__all__ = [
    "GovernanceAssessment",
    "GovernanceDecision",
    "GovernanceIssue",
    "IssueSeverity",
    "IssueType",
    "MaterialRecord",
    "DeterministicGovernanceValidator",
    "HumanReviewClaim",
    "HumanReviewClaimRelease",
    "claim_pending_human_review",
    "release_human_review_claim",
    "human_review_claim_to_record",
    "human_review_claim_from_record",
    "HumanReviewClaimPersistenceError",
    "DuplicateHumanReviewClaimError",
    "HumanReviewClaimCorruptionError",
    "HumanReviewClaimRepository",
    "JsonlHumanReviewClaimRepository",
    "human_review_claim_release_to_record",
    "human_review_claim_release_from_record",
    "HumanReviewClaimReleasePersistenceError",
    "DuplicateHumanReviewClaimReleaseError",
    "HumanReviewClaimReleaseCorruptionError",
    "HumanReviewClaimReleaseRepository",
    "JsonlHumanReviewClaimReleaseRepository",
    "RecordHumanReviewClaimUseCase",
    "ReleaseHumanReviewClaimUseCase",
    "HumanReviewClaimFactState",
    "HumanReviewClaimState",
    "ReleaseAwareClaimState",
    "project_human_review_claim_state",
    "project_release_aware_claim_state",
    "ReviewerEligibilityDecision",
    "ReviewerEligibilityStatus",
    "evaluate_release_aware_reviewer_claim_eligibility",
    "evaluate_reviewer_claim_eligibility",
    "DecisionRecommendationGroundTruth",
    "DecisionRecommendationGroundTruthDataset",
    "DuplicatePairGroundTruth",
    "DuplicatePairGroundTruthDataset",
    "LabelProvenance",
    "MaterialRuleGroundTruth",
    "MaterialRuleGroundTruthDataset",
    "DecisionRecommendationCaseEvaluation",
    "DecisionRecommendationEvaluationReport",
    "evaluate_decision_recommendation",
    "evaluate_decision_recommendations",
    "DuplicatePairPrediction",
    "DuplicatePairCaseEvaluation",
    "DuplicatePairEvaluationReport",
    "evaluate_duplicate_pair",
    "evaluate_duplicate_pairs",
    "MaterialRulePrediction",
    "MaterialRuleCaseEvaluation",
    "MaterialRuleEvaluationReport",
    "evaluate_material_rule",
    "evaluate_material_rules",
    "RECORD_TYPE_MATERIAL_RULE_GROUND_TRUTH",
    "RECORD_TYPE_DUPLICATE_PAIR_GROUND_TRUTH",
    "RECORD_TYPE_DECISION_RECOMMENDATION_GROUND_TRUTH",
    "material_rule_ground_truth_to_record",
    "material_rule_ground_truth_from_record",
    "duplicate_pair_ground_truth_to_record",
    "duplicate_pair_ground_truth_from_record",
    "decision_recommendation_ground_truth_to_record",
    "decision_recommendation_ground_truth_from_record",
    "DecisionRecommendationBenchmarkCase",
    "RunDecisionRecommendationBenchmarkUseCase",
    "CatalogDiagnosticPipeline",
    "CatalogQualityReport",
    "DiagnoseCatalogQualityUseCase",
    "diagnose_catalog_quality",
]
