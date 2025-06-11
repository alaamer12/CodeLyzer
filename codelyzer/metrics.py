from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import StrEnum, auto
from typing import Dict, List, Any, Optional


class MetricLevel(StrEnum):
    """Base enum for all metric levels"""
    UNDEFINED = auto()


@dataclass
class BaseMetric:
    """Base class for all metrics"""
    name: str
    value: Any = None
    level: Optional[MetricLevel] = None


class ComplexityLevel(StrEnum):
    TRIVIAL = 'trivial'
    LOW = 'low'
    MODERATE = 'moderate'
    HIGH = 'high'
    VERY_HIGH = 'very_high'
    EXTREME = 'extreme'


class SecurityLevel(StrEnum):
    SECURE = 'secure'
    LOW_RISK = 'low_risk'
    MEDIUM_RISK = 'medium_risk'
    HIGH_RISK = 'high_risk'
    CRITICAL = 'critical'


class CodeSmellSeverity(StrEnum):
    NONE = 'none'
    MINOR = 'minor'
    MAJOR = 'major'
    CRITICAL = 'critical'


class MaintainabilityLevel(StrEnum):
    EXCELLENT = 'excellent'  # 85-100
    GOOD = 'good'  # 65-84
    MODERATE = 'moderate'  # 40-64
    POOR = 'poor'  # 25-39
    UNMAINTAINABLE = 'unmaintainable'  # 0-24


@dataclass
class FileMetricCategory:
    """Base class for a category of file metrics"""
    metrics: Dict[str, BaseMetric] = field(default_factory=dict)

    def add_metric(self, name: str, value: Any, level: Optional[MetricLevel] = None) -> None:
        self.metrics[name] = BaseMetric(name=name, value=value, level=level)

    def get_metric(self, name: str) -> Optional[BaseMetric]:
        return self.metrics.get(name)


@dataclass
class BaseFileMetrics:
    """Basic metrics common to all files"""
    file_path: str
    language: str
    loc: int = 0  # Lines of code
    sloc: int = 0  # Source lines of code (excluding comments/blanks)
    comments: int = 0  # Comment lines
    blanks: int = 0  # Blank lines
    file_size: int = 0  # Size in bytes
    last_modified: float = 0.0  # Timestamp


@dataclass
class ComplexityMetrics(FileMetricCategory):
    """Complexity-related metrics"""
    cyclomatic_complexity: int = 0
    cognitive_complexity: int = 0
    halstead_complexity: float = 0.0
    complexity_score: float = 0.0
    maintainability_index: float = 0.0

    def determine_complexity_level(self) -> ComplexityLevel:
        """Determine complexity level based on metrics"""
        if self.complexity_score < 50:
            return ComplexityLevel.TRIVIAL
        elif self.complexity_score < 200:
            return ComplexityLevel.LOW
        elif self.complexity_score < 500:
            return ComplexityLevel.MODERATE
        elif self.complexity_score < 1000:
            return ComplexityLevel.HIGH
        elif self.complexity_score < 2000:
            return ComplexityLevel.VERY_HIGH
        else:
            return ComplexityLevel.EXTREME


@dataclass
class SecurityMetrics(FileMetricCategory):
    """Security-related metrics"""
    vulnerabilities: List[Dict] = field(default_factory=list)
    security_score: float = 100.0

    def determine_security_level(self) -> SecurityLevel:
        """Determine security level based on metrics"""
        if not self.vulnerabilities:
            return SecurityLevel.SECURE

        critical_count = sum(1 for v in self.vulnerabilities if v.get('severity') == 'critical')
        high_count = sum(1 for v in self.vulnerabilities if v.get('severity') == 'high')

        if critical_count > 0:
            return SecurityLevel.CRITICAL
        elif high_count > 0:
            return SecurityLevel.HIGH_RISK
        elif len(self.vulnerabilities) > 0:
            return SecurityLevel.MEDIUM_RISK
        else:
            return SecurityLevel.SECURE


@dataclass
class CodeSmellMetrics(FileMetricCategory):
    """Code smell metrics"""
    smells: List[Dict] = field(default_factory=list)
    duplicated_lines: int = 0
    technical_debt_ratio: float = 0.0

    def determine_smell_severity(self) -> CodeSmellSeverity:
        """Determine code smell severity based on metrics"""
        critical_count = sum(1 for s in self.smells if s.get('severity') == 'critical')
        major_count = sum(1 for s in self.smells if s.get('severity') == 'major')

        if critical_count > 0:
            return CodeSmellSeverity.CRITICAL
        elif major_count > 0:
            return CodeSmellSeverity.MAJOR
        elif len(self.smells) > 0:
            return CodeSmellSeverity.MINOR
        else:
            return CodeSmellSeverity.NONE


@dataclass
class StructureMetrics(FileMetricCategory):
    """Code structure metrics"""
    classes: int = 0
    functions: int = 0
    methods: int = 0
    imports: List[str] = field(default_factory=list)
    methods_per_class: Dict[str, int] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)


@dataclass
class PatternMetrics(FileMetricCategory):
    """Pattern-based metrics"""
    patterns_found: Dict[str, List[Dict]] = field(default_factory=dict)

    def add_pattern(self, pattern_name: str, location: Dict) -> None:
        if pattern_name not in self.patterns_found:
            self.patterns_found[pattern_name] = []
        self.patterns_found[pattern_name].append(location)


@dataclass
class FileMetrics:
    """Comprehensive metrics for a single file"""
    base: BaseFileMetrics
    structure: StructureMetrics = field(default_factory=StructureMetrics)
    complexity: ComplexityMetrics = field(default_factory=ComplexityMetrics)
    security: SecurityMetrics = field(default_factory=SecurityMetrics)
    code_smells: CodeSmellMetrics = field(default_factory=CodeSmellMetrics)
    patterns: PatternMetrics = field(default_factory=PatternMetrics)
    custom_metrics: Dict[str, FileMetricCategory] = field(default_factory=dict)

    @property
    def file_path(self) -> str:
        return self.base.file_path

    @property
    def language(self) -> str:
        return self.base.language

    @property
    def loc(self) -> int:
        return self.base.loc

    @property
    def sloc(self) -> int:
        return self.base.sloc

    @property
    def comments(self) -> int:
        return self.base.comments

    @property
    def blanks(self) -> int:
        return self.base.blanks

    @property
    def file_size(self) -> int:
        return self.base.file_size

    @property
    def complexity_score(self) -> float:
        return self.complexity.complexity_score

    @property
    def cyclomatic_complexity(self) -> int:
        return self.complexity.cyclomatic_complexity

    @property
    def maintainability_index(self) -> float:
        return self.complexity.maintainability_index

    @property
    def technical_debt_ratio(self) -> float:
        return self.code_smells.technical_debt_ratio

    @property
    def duplicated_lines(self) -> int:
        return self.code_smells.duplicated_lines

    @property
    def security_issues(self) -> List[Dict]:
        return self.security.vulnerabilities

    @property
    def code_smells_list(self) -> List[Dict]:
        return self.code_smells.smells

    @property
    def classes(self) -> int:
        return self.structure.classes

    @property
    def functions(self) -> int:
        return self.structure.functions

    @property
    def methods(self) -> int:
        return self.structure.methods

    @property
    def imports(self) -> List[str]:
        return self.structure.imports

    @property
    def methods_per_class(self) -> Dict[str, int]:
        return self.structure.methods_per_class

    def add_custom_metric_category(self, name: str, category: FileMetricCategory) -> None:
        """Add a custom metric category"""
        self.custom_metrics[name] = category

    def get_custom_metric_category(self, name: str) -> Optional[FileMetricCategory]:
        """Get a custom metric category"""
        return self.custom_metrics.get(name)


@dataclass
class BaseProjectMetrics:
    """Basic project-wide metrics"""
    total_files: int = 0
    total_loc: int = 0
    total_sloc: int = 0
    total_comments: int = 0
    total_blanks: int = 0
    languages: Dict[str, int] = field(default_factory=dict)
    project_size: int = 0  # Size in bytes
    analysis_duration: float = 0.0


@dataclass
class ProjectStructureMetrics:
    """Project structure metrics"""
    total_classes: int = 0
    total_functions: int = 0
    total_methods: int = 0
    dependencies: Dict[str, int] = field(default_factory=dict)
    dependency_graph: Dict[str, List[str]] = field(default_factory=dict)


@dataclass
class ProjectComplexityMetrics:
    """Project complexity metrics"""
    complexity_distribution: Dict[ComplexityLevel, int] = field(default_factory=dict)
    most_complex_files: List[str] = field(default_factory=list)
    avg_cyclomatic_complexity: float = 0.0
    avg_maintainability_index: float = 0.0
    maintainability_score: float = 0.0


@dataclass
class ProjectSecurityMetrics:
    """Project security metrics"""
    security_summary: Dict[SecurityLevel, int] = field(default_factory=dict)
    critical_vulnerabilities: List[Dict] = field(default_factory=list)
    security_score: float = 100.0


@dataclass
class ProjectCodeQualityMetrics:
    """Project code quality metrics"""
    code_quality_score: float = 100.0
    duplicate_blocks: List[Dict] = field(default_factory=list)
    duplicated_lines_ratio: float = 0.0
    largest_files: List[str] = field(default_factory=list)
    hotspots: List[str] = field(default_factory=list)


@dataclass
class ProjectMetrics:
    """Comprehensive project metrics"""
    base: BaseProjectMetrics = field(default_factory=BaseProjectMetrics)
    structure: ProjectStructureMetrics = field(default_factory=ProjectStructureMetrics)
    complexity: ProjectComplexityMetrics = field(default_factory=ProjectComplexityMetrics)
    security: ProjectSecurityMetrics = field(default_factory=ProjectSecurityMetrics)
    code_quality: ProjectCodeQualityMetrics = field(default_factory=ProjectCodeQualityMetrics)
    file_metrics: List[FileMetrics] = field(default_factory=list)
    custom_metrics: Dict[str, Any] = field(default_factory=dict)
    git_stats: Dict = field(default_factory=dict)

    @property
    def total_files(self) -> int:
        return self.base.total_files

    @property
    def total_loc(self) -> int:
        return self.base.total_loc

    @property
    def total_sloc(self) -> int:
        return self.base.total_sloc

    @property
    def total_comments(self) -> int:
        return self.base.total_comments

    @property
    def total_blanks(self) -> int:
        return self.base.total_blanks

    @property
    def total_classes(self) -> int:
        return self.structure.total_classes

    @property
    def total_functions(self) -> int:
        return self.structure.total_functions

    @property
    def total_methods(self) -> int:
        return self.structure.total_methods

    @property
    def languages(self) -> Dict[str, int]:
        return self.base.languages

    @property
    def project_size(self) -> int:
        return self.base.project_size

    @property
    def analysis_duration(self) -> float:
        return self.base.analysis_duration

    @analysis_duration.setter
    def analysis_duration(self, value: float):
        self.base.analysis_duration = value

    @property
    def complexity_distribution(self) -> Dict[ComplexityLevel, int]:
        return self.complexity.complexity_distribution

    @property
    def most_complex_files(self) -> List[str]:
        return self.complexity.most_complex_files

    @property
    def code_quality_score(self) -> float:
        return self.code_quality.code_quality_score

    @property
    def maintainability_score(self) -> float:
        return self.complexity.maintainability_score

    @property
    def language_distribution(self) -> Dict[str, int]:
        """Get the language distribution dictionary"""
        return self.base.languages

    def add_custom_metric(self, name: str, value: Any) -> None:
        """Add a custom metric"""
        self.custom_metrics[name] = value

    def get_custom_metric(self, name: str) -> Optional[Any]:
        """Get a custom metric"""
        return self.custom_metrics.get(name)


class MetricProvider(ABC):
    """Interface for classes that provide metrics"""

    @abstractmethod
    def analyze_file(self, file_metrics: FileMetrics, file_content: str, ast_data: Any) -> None:
        """Provide metrics for a file"""
        pass

    @abstractmethod
    def analyze_project(self, project_metrics: ProjectMetrics) -> None:
        """Provide metrics for a project"""
        pass


# Factory method for creating FileMetrics
def create_file_metrics(file_path: str, language: str) -> FileMetrics:
    """Create a FileMetrics object with the appropriate language"""
    base_metrics = BaseFileMetrics(file_path=file_path, language=language)
    return FileMetrics(base=base_metrics)


# Factory method for creating ProjectMetrics
def create_project_metrics() -> ProjectMetrics:
    """Create a ProjectMetrics object"""
    return ProjectMetrics()
