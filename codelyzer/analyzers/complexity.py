import math
from typing import Any, List, Tuple

from codelyzer.metrics import FileMetrics, ProjectMetrics, MetricProvider


class ComplexityAnalyzer(MetricProvider):
    """Analyzer for calculating code complexity metrics"""


    def provide_file_metrics(self, file_metrics: FileMetrics, file_content: str, ast_data: Any) -> None:
        """Calculate complexity metrics for a file"""
        language = file_metrics.language


        # Skip if content is empty
        if not file_content:
            return


        # Calculate basic cyclomatic complexity
        cc = self._calculate_cyclomatic_complexity(file_content, language)
        file_metrics.complexity.cyclomatic_complexity = cc


        # Calculate cognitive complexity
        cognitive = self._calculate_cognitive_complexity(file_content, language)
        file_metrics.complexity.cognitive_complexity = cognitive


        # Calculate maintainability index
        mi = self._calculate_maintainability_index(file_metrics, file_content)
        file_metrics.complexity.maintainability_index = mi


        # Calculate Halstead complexity measures
        halstead = self._calculate_halstead_complexity(file_content, language)
        file_metrics.complexity.halstead_complexity = halstead


        # Calculate overall complexity score based on combined metrics
        complexity_score = self._calculate_complexity_score(
            cc, cognitive, mi, halstead,
            file_metrics.sloc or 0,
            cc, cognitive, mi, halstead,
            file_metrics.sloc or 0,
            file_metrics.functions or 0,
            file_metrics.classes or 0
        )
        file_metrics.complexity.complexity_score = complexity_score


        # Add metrics to categories
        file_metrics.complexity.add_metric("cyclomatic", cc)
        file_metrics.complexity.add_metric("cognitive", cognitive)
        file_metrics.complexity.add_metric("maintainability", mi)
        file_metrics.complexity.add_metric("halstead", halstead)


    def provide_project_metrics(self, project_metrics: ProjectMetrics) -> None:
        """Calculate project-level complexity metrics"""
        if not project_metrics.file_metrics:
            return


        # Calculate average cyclomatic complexity
        valid_files = [f for f in project_metrics.file_metrics if f.cyclomatic_complexity > 0]
        if valid_files:
            project_metrics.complexity.avg_cyclomatic_complexity = sum(
                f.cyclomatic_complexity for f in valid_files
            ) / len(valid_files)


        # Calculate average maintainability index
        valid_mi_files = [f for f in project_metrics.file_metrics if f.complexity.maintainability_index > 0]
        if valid_mi_files:
            project_metrics.complexity.avg_maintainability_index = sum(
                f.complexity.maintainability_index for f in valid_mi_files
            ) / len(valid_mi_files)


        # Find most complex files
        sorted_by_complexity = sorted(
            project_metrics.file_metrics,
            key=lambda f: f.complexity_score,
            project_metrics.file_metrics,
            key=lambda f: f.complexity_score,
            reverse=True
        )
        project_metrics.complexity.most_complex_files = [f.file_path for f in sorted_by_complexity[:10]]

    @staticmethod
    def _calculate_cyclomatic_complexity(content: str, language: str) -> int:
        """Calculate cyclomatic complexity based on control flow structures"""
        if not content:
            return 1


        # Base complexity is 1
        complexity = 1


        # Common control structures across languages
        if language in ["python", "javascript", "typescript", "jsx"]:
            # Count control structures
            import re


            # Branch statements
            patterns = [
                r'\bif\b',  # if statements
                r'\belse\s+if\b',  # else if
                r'\bfor\b',  # for loops
                r'\bwhile\b',  # while loops
                r'\bcase\b',  # switch case
                r'\bcatch\b',  # try/catch
                r'&&',  # logical AND
                r'\|\|',  # logical OR
                r'\?'  # ternary operator
                r'\bif\b',  # if statements
                r'\belse\s+if\b',  # else if
                r'\bfor\b',  # for loops
                r'\bwhile\b',  # while loops
                r'\bcase\b',  # switch case
                r'\bcatch\b',  # try/catch
                r'&&',  # logical AND
                r'\|\|',  # logical OR
                r'\?'  # ternary operator
            ]


            for pattern in patterns:
                complexity += len(re.findall(pattern, content))


        # Language-specific patterns
        if language == "python":
            import re
            # Python-specific control flow structures
            patterns = [
                r'\belif\b',  # elif statements
                r'\bexcept\b'  # except blocks
                r'\belif\b',  # elif statements
                r'\bexcept\b'  # except blocks
            ]


            for pattern in patterns:
                complexity += len(re.findall(pattern, content))


        return complexity


    def _calculate_cognitive_complexity(self, content: str, language: str) -> int:
        """Calculate cognitive complexity based on nesting and logical flow"""
        if not content:
            return 0


        # Basic implementation counting nesting levels
        complexity = 0
        lines = content.split('\n')
        nesting_level = 0


        # Count nesting level increments
        for line in lines:
            stripped = line.strip()


            # Language-specific checks for nesting increases
            if language == "python":
                if stripped.endswith(':') and any(kw in stripped for kw in
                                                  ['if', 'for', 'while', 'elif', 'else', 'try', 'except', 'def',
                                                   'class']):
                if stripped.endswith(':') and any(kw in stripped for kw in
                                                  ['if', 'for', 'while', 'elif', 'else', 'try', 'except', 'def',
                                                   'class']):
                    complexity += nesting_level + 1  # Higher cost for deeper nesting
                    nesting_level += 1
                elif stripped and len(line) - len(stripped) < nesting_level * 4:  # Assuming 4-space indentation
                    # Decreased indentation level
                    new_level = (len(line) - len(stripped)) // 4
                    if new_level < nesting_level:
                        nesting_level = new_level


            elif language in ["javascript", "typescript", "jsx"]:
                if '{' in stripped:
                    complexity += nesting_level + 1
                    nesting_level += stripped.count('{')
                if '}' in stripped:
                    nesting_level -= stripped.count('}')
                    nesting_level = max(0, nesting_level)  # Ensure no negative nesting


        return complexity


    def _calculate_maintainability_index(self, file_metrics: FileMetrics, content: str) -> float:
        """Calculate maintainability index
        
        MI = 171 - 5.2 * ln(HV) - 0.23 * CC - 16.2 * ln(LOC)
        where:
        - HV is Halstead Volume
        - CC is Cyclomatic Complexity
        - LOC is Lines of Code
        """
        import math


        sloc = file_metrics.sloc or 0
        if sloc == 0:
            return 100


        cc = file_metrics.complexity.cyclomatic_complexity or 1


        # Calculate Halstead volume if not already calculated
        halstead_volume = file_metrics.complexity.halstead_complexity or self._calculate_halstead_complexity(content,
                                                                                                             file_metrics.language)

        halstead_volume = file_metrics.complexity.halstead_complexity or self._calculate_halstead_complexity(content,
                                                                                                             file_metrics.language)

        # Convert to positive value for logarithm
        halstead_log = math.log(max(1, halstead_volume)) if halstead_volume > 0 else 0
        sloc_log = math.log(max(1, sloc))


        # Calculate maintainability index
        mi = 171 - (5.2 * halstead_log) - (0.23 * cc) - (16.2 * sloc_log)


        # Normalize to 0-100 scale
        normalized_mi = max(0, min(100, mi * 100 / 171))


        return normalized_mi


    def _calculate_halstead_complexity(self, content: str, language: str) -> float:
        """Calculate Halstead complexity metrics"""
        if not content or len(content) < 10:
            return 0


        # Extract operators and operands
        operators, operands = self._extract_operators_and_operands(content, language)


        # Calculate Halstead metrics
        n1 = len(set(operators))  # Number of distinct operators
        n2 = len(set(operands))  # Number of distinct operands
        N1 = len(operators)  # Total number of operators
        N2 = len(operands)  # Total number of operands

        n2 = len(set(operands))  # Number of distinct operands
        N1 = len(operators)  # Total number of operators
        N2 = len(operands)  # Total number of operands

        # Avoid division by zero
        if n1 == 0 or n2 == 0:
            return 0


        # Calculate Halstead metrics
        program_vocabulary = n1 + n2
        program_length = N1 + N2
        volume = program_length * (math.log2(max(1, program_vocabulary)))


        return volume

    @staticmethod
    def _extract_operators_and_operands(content: str, language: str) -> Tuple[List[str], List[str]]:
        """Extract operators and operands from code content"""
        operators = []
        operands = []


        # Simplified implementation for common operators in most languages
        import re


        # Common operators
        operator_pattern = r'[+\-*/=<>!&|^~%]+'
        operator_matches = re.finditer(operator_pattern, content)
        for match in operator_matches:
            operators.append(match.group())


        # Keywords as operators
        if language == "python":
            keyword_operators = ['if', 'else', 'elif', 'for', 'while', 'in', 'not', 'is', 'and', 'or', 'return',
                                 'import', 'from']
            keyword_operators = ['if', 'else', 'elif', 'for', 'while', 'in', 'not', 'is', 'and', 'or', 'return',
                                 'import', 'from']
        else:  # javascript, typescript
            keyword_operators = ['if', 'else', 'for', 'while', 'switch', 'case', 'return', 'typeof', 'instanceof',
                                 'new', 'delete', 'void']

            keyword_operators = ['if', 'else', 'for', 'while', 'switch', 'case', 'return', 'typeof', 'instanceof',
                                 'new', 'delete', 'void']

        for keyword in keyword_operators:
            pattern = r'\b' + keyword + r'\b'
            matches = re.finditer(pattern, content)
            for match in matches:
                operators.append(match.group())


        # Identifiers and literals as operands
        # Identifiers
        identifier_pattern = r'\b[a-zA-Z_][a-zA-Z0-9_]*\b'
        identifier_matches = re.finditer(identifier_pattern, content)
        for match in identifier_matches:
            # Skip if it's a keyword
            if match.group() not in keyword_operators:
                operands.append(match.group())


        # Number literals
        number_pattern = r'\b\d+(?:\.\d+)?\b'
        number_matches = re.finditer(number_pattern, content)
        for match in number_matches:
            operands.append(match.group())


        # String literals
        string_pattern = r'(?:"[^"\\]*(?:\\.[^"\\]*)*")|(?:\'[^\'\\]*(?:\\.[^\'\\]*)*\')'
        string_matches = re.finditer(string_pattern, content)
        for match in string_matches:
            operands.append(match.group())


        return operators, operands

    @staticmethod
    def _calculate_complexity_score(
            cyclomatic: int,
            cognitive: int,
            maintainability: float,
            halstead: float,
            sloc: int,
            functions_count: int,
            classes_count: int
    ) -> float:
        """Calculate overall complexity score based on multiple metrics"""
        # Weighted formula for complexity score
        score = (
                cyclomatic * 10 +  # Cyclomatic complexity weight
                cognitive * 15 +  # Cognitive complexity weight
                (100 - maintainability) * 5 +  # Inverted maintainability (higher is worse)
                halstead / 100 +  # Halstead complexity
                sloc / 10  # Lines of code factor
                cyclomatic * 10 +  # Cyclomatic complexity weight
                cognitive * 15 +  # Cognitive complexity weight
                (100 - maintainability) * 5 +  # Inverted maintainability (higher is worse)
                halstead / 100 +  # Halstead complexity
                sloc / 10  # Lines of code factor
        )


        # Adjust for large files with many functions/classes
        if functions_count > 10 or classes_count > 5:
            score *= 1.2

        return score


        return score
