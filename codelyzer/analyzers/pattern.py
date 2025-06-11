from typing import Any, Dict, List
import re
from codelyzer.metrics import FileMetrics, ProjectMetrics, MetricProvider


class PatternBasedAnalyzer(MetricProvider):
    """Analyzer for identifying patterns in code"""

    def __init__(self):
        self.design_patterns = {
            "python": self._get_python_patterns(),
            "javascript": self._get_js_patterns(),
            "typescript": self._get_js_patterns(),  # TypeScript uses same patterns as JS
            "jsx": self._get_js_patterns()
        }

    def analyze_file(self, file_metrics: FileMetrics, file_content: str, ast_data: Any) -> None:
        """Analyze file for design patterns and anti-patterns"""
        language = file_metrics.language

        # Skip if content is empty
        if not file_content:
            return

        patterns = self.design_patterns.get(language, {})
        if not patterns:
            return

        # Analyze patterns
        for pattern_name, pattern_info in patterns.items():
            detector_func = pattern_info.get('detector')
            if detector_func:
                locations = detector_func(file_content, ast_data)
                for location in locations:
                    file_metrics.patterns.add_pattern(pattern_name, location)

    def analyze_project(self, project_metrics: ProjectMetrics) -> None:
        """Analyze project-level pattern metrics"""
        # Aggregate patterns by type
        pattern_stats = {}

        for file_metrics in project_metrics.file_metrics:
            for pattern_name, locations in file_metrics.patterns.patterns_found.items():
                if pattern_name not in pattern_stats:
                    pattern_stats[pattern_name] = {
                        'count': 0,
                        'files': set()
                    }
                pattern_stats[pattern_name]['count'] += len(locations)
                pattern_stats[pattern_name]['files'].add(file_metrics.file_path)

        # Convert sets to lists for JSON serialization
        for pattern_name in pattern_stats:
            pattern_stats[pattern_name]['files'] = set(pattern_stats[pattern_name]['files'])

        # Add to project metrics
        project_metrics.add_custom_metric('design_patterns', pattern_stats)

    def _get_python_patterns(self) -> Dict[str, Dict]:
        """Get patterns for Python code"""
        return {
            "singleton": {
                'description': "Singleton pattern - ensures a class has only one instance",
                'detector': self._detect_singleton_python
            },
            "factory_method": {
                'description': "Factory Method pattern - creates objects without specifying exact class",
                'detector': self._detect_factory_method_python
            },
            "observer": {
                'description': "Observer pattern - defines a one-to-many dependency between objects",
                'detector': self._detect_observer_python
            },
            "decorator": {
                'description': "Decorator pattern - dynamically adds responsibilities to objects",
                'detector': self._detect_decorator_python
            },
            "strategy": {
                'description': "Strategy pattern - defines family of algorithms",
                'detector': self._detect_strategy_python
            }
        }

    def _get_js_patterns(self) -> Dict[str, Dict]:
        """Get patterns for JavaScript/TypeScript code"""
        return {
            "module_pattern": {
                'description': "Module pattern - creates private and public encapsulation",
                'detector': self._detect_module_js
            },
            "singleton": {
                'description': "Singleton pattern - ensures a class has only one instance",
                'detector': self._detect_singleton_js
            },
            "factory": {
                'description': "Factory pattern - creates objects without specifying exact class",
                'detector': self._detect_factory_js
            },
            "observer": {
                'description': "Observer pattern - defines a one-to-many dependency between objects",
                'detector': self._detect_observer_js
            },
            "prototype": {
                'description': "Prototype pattern - used for object creation by cloning existing objects",
                'detector': self._detect_prototype_js
            }
        }

    # Python pattern detectors
    @staticmethod
    def _detect_singleton_python(content: str, ast_data: Any) -> List[Dict]:
        """Detect singleton pattern in Python code"""
        locations = []

        # Common singleton implementations in Python
        patterns = [
            r"_instance\s*=\s*None",  # Class variable for instance
            r"if\s+cls\._instance\s+is\s+None",  # Check if instance exists
            r"if\s+not\s+hasattr\(cls,\s*['\"]_instance['\"]\)",  # Alternative check
            r"@classmethod\s+def\s+instance\(\s*cls\s*\)",  # Instance getter
            r"@classmethod\s+def\s+get_instance\(\s*cls\s*\)",  # Instance getter
            r"__new__\(\s*cls\s*,",  # Custom __new__ method (potential singleton)
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                # Get context (20 chars before and after)
                start_idx = max(0, match.start() - 20)
                end_idx = min(len(content), match.end() + 20)
                context = content[start_idx:end_idx]

                locations.append({
                    'position': match.start(),
                    'line': content[:match.start()].count('\n') + 1,
                    'context': context,
                    'type': 'singleton'
                })

        return locations

    @staticmethod
    def _detect_factory_method_python(content: str, ast_data: Any) -> List[Dict]:
        """Detect factory method pattern in Python code"""
        locations = []

        # Common factory method patterns
        patterns = [
            r"def\s+create_\w+\(\s*.*\)\s*:",  # create_* methods
            r"@classmethod\s+def\s+create\(",  # @classmethod create
            r"@classmethod\s+def\s+from_\w+\(",  # from_* factory methods
            r"class\s+\w+Factory\b",  # *Factory classes
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                locations.append({
                    'position': match.start(),
                    'line': content[:match.start()].count('\n') + 1,
                    'context': content[max(0, match.start() - 20):min(len(content), match.end() + 20)],
                    'type': 'factory_method'
                })

        return locations

    @staticmethod
    def _detect_observer_python(content: str, ast_data: Any) -> List[Dict]:
        """Detect observer pattern in Python code"""
        locations = []

        # Observer pattern indicators
        patterns = [
            r"def\s+add_observer\(\s*self\s*,",
            r"def\s+remove_observer\(\s*self\s*,",
            r"def\s+notify_observers\(\s*self\s*",
            r"def\s+register\(\s*self\s*,\s*\w+\s*\)",
            r"def\s+unregister\(\s*self\s*,\s*\w+\s*\)",
            r"def\s+notify\(\s*self\s*",
            r"self\._observers\s*=\s*\[\]",
            r"for\s+observer\s+in\s+self\._observers",
            r"for\s+observer\s+in\s+self\.observers",
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                locations.append({
                    'position': match.start(),
                    'line': content[:match.start()].count('\n') + 1,
                    'context': content[max(0, match.start() - 20):min(len(content), match.end() + 20)],
                    'type': 'observer'
                })

        return locations

    @staticmethod
    def _detect_decorator_python(content: str, ast_data: Any) -> List[Dict]:
        """Detect decorator pattern in Python code"""
        locations = []

        # Python function decorators
        decorator_patterns = [
            r"@\w+(?:\.\w+)*(?:\(.*?\))?\s+def\s+\w+\(",  # @decorator def func
            r"@\w+(?:\.\w+)*\s+class\s+\w+\(",  # @decorator class Name
            r"def\s+\w+\(\s*self\s*,\s*wrapped\s*,",  # Function taking wrapped object
            r"def\s+__init__\(\s*self\s*,\s*decorated\s*",  # Constructor taking decorated object
            r"def\s+__init__\(\s*self\s*,\s*component\s*"  # Constructor taking component
        ]

        for pattern in decorator_patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                locations.append({
                    'position': match.start(),
                    'line': content[:match.start()].count('\n') + 1,
                    'context': content[max(0, match.start() - 20):min(len(content), match.end() + 20)],
                    'type': 'decorator'
                })

        return locations

    @staticmethod
    def _detect_strategy_python(content: str, ast_data: Any) -> List[Dict]:
        """Detect strategy pattern in Python code"""
        import re
        locations = []

        # Strategy pattern indicators
        strategy_patterns = [
            r"class\s+\w+Strategy\b",  # *Strategy class
            r"def\s+set_strategy\(\s*self\s*,\s*\w+\s*\)",  # set_strategy method
            r"self\._strategy\s*=\s*\w+",  # Assigning strategy
            r"self\.strategy\s*=\s*\w+",  # Assigning strategy
            r"return\s+self\._strategy\.",  # Using strategy
            r"return\s+self\.strategy\.",  # Using strategy
        ]

        for pattern in strategy_patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                locations.append({
                    'position': match.start(),
                    'line': content[:match.start()].count('\n') + 1,
                    'context': content[max(0, match.start() - 20):min(len(content), match.end() + 20)],
                    'type': 'strategy'
                })

        return locations

    # JavaScript pattern detectors
    @staticmethod
    def _detect_module_js(content: str, ast_data: Any) -> List[Dict]:
        """Detect module pattern in JavaScript code"""
        locations = []

        # Module pattern indicators
        module_patterns = [
            r"\(\s*function\s*\(\s*\)\s*\{.*\}\s*\)\(\s*\)",  # IIFE
            r"export\s+default\s+\{",  # ES6 module export
            r"module\.exports\s*=",  # CommonJS export
            r"define\s*\(\s*\[",  # AMD define
            r"return\s*\{\s*\w+\s*:.*\}",  # Revealing module pattern
        ]

        for pattern in module_patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                locations.append({
                    'position': match.start(),
                    'line': content[:match.start()].count('\n') + 1,
                    'context': content[max(0, match.start() - 20):min(len(content), match.end() + 20)],
                    'type': 'module_pattern'
                })

        return locations

    @staticmethod
    def _detect_singleton_js(content: str, ast_data: Any) -> List[Dict]:
        """Detect singleton pattern in JavaScript code"""
        locations = []

        # Singleton pattern indicators in JavaScript
        singleton_patterns = [
            r"var\s+\w+\s*=\s*\(\s*function\s*\(\s*\)\s*\{\s*var\s+instance",  # Module singleton
            r"if\s*\(\s*instance\s*\)\s*return\s+instance",  # Instance check
            r"if\s*\(\s*!\s*instance\s*\)",  # Instance check
            r"static\s+getInstance\s*\(\s*\)",  # getInstance method
            r"getInstance\s*:\s*function\s*\(\s*\)",  # getInstance method
        ]

        for pattern in singleton_patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                locations.append({
                    'position': match.start(),
                    'line': content[:match.start()].count('\n') + 1,
                    'context': content[max(0, match.start() - 20):min(len(content), match.end() + 20)],
                    'type': 'singleton'
                })

        return locations

    @staticmethod
    def _detect_factory_js(content: str, ast_data: Any) -> List[Dict]:
        """Detect factory pattern in JavaScript code"""
        locations = []

        # Factory pattern indicators in JavaScript
        factory_patterns = [
            r"function\s+create\w+\s*\(",  # create* functions
            r"class\s+\w*Factory\b",  # *Factory classes
            r"\w+\.prototype\.create\w+\s*=",  # create* prototype methods
            r"static\s+create\w+\s*\(",  # static create* methods
            r"create\s*:\s*function\s*\("  # create method in object literal
        ]

        for pattern in factory_patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                locations.append({
                    'position': match.start(),
                    'line': content[:match.start()].count('\n') + 1,
                    'context': content[max(0, match.start() - 20):min(len(content), match.end() + 20)],
                    'type': 'factory'
                })

        return locations

    @staticmethod
    def _detect_observer_js(content: str, ast_data: Any) -> List[Dict]:
        """Detect observer pattern in JavaScript code"""
        import re
        locations = []

        # Observer pattern indicators in JavaScript
        observer_patterns = [
            r"addEventListener\s*\(\s*['\"]",  # DOM event listener
            r"removeEventListener\s*\(\s*['\"]",  # DOM event listener removal
            r"on\s*\(\s*['\"]",  # jQuery/Node.js style event
            r"emit\s*\(\s*['\"]",  # EventEmitter emit
            r"subscribe\s*\(\s*['\"]",  # Subscribe method
            r"publish\s*\(\s*['\"]",  # Publish method
            r"this\.observers\s*=",  # observers collection
            r"this\._observers\s*="  # _observers collection
        ]

        for pattern in observer_patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                locations.append({
                    'position': match.start(),
                    'line': content[:match.start()].count('\n') + 1,
                    'context': content[max(0, match.start() - 20):min(len(content), match.end() + 20)],
                    'type': 'observer'
                })

        return locations

    @staticmethod
    def _detect_prototype_js(content: str, ast_data: Any) -> List[Dict]:
        """Detect prototype pattern in JavaScript code"""
        import re
        locations = []

        # Prototype pattern indicators in JavaScript
        prototype_patterns = [
            r"\w+\.prototype\.\w+\s*=",  # Setting prototype method
            r"Object\.create\s*\(",  # Object.create usage
            r"clone\s*\(\s*\)",  # clone method
            r"\.clone\s*=\s*function",  # clone method
            r"prototype\s*=\s*Object\.create",  # Setting up prototype chain
        ]

        for pattern in prototype_patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                locations.append({
                    'position': match.start(),
                    'line': content[:match.start()].count('\n') + 1,
                    'context': content[max(0, match.start() - 20):min(len(content), match.end() + 20)],
                    'type': 'prototype'
                })

        return locations
