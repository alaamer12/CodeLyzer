#!/usr/bin/env python3
"""
Python test file for analyzer testing
Contains various Python constructs to test the analyzer
"""
from __future__ import annotations

import asyncio
import dataclasses
import enum
import functools
import json
import logging
import os
import sys
import typing
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Type, TypeVar, Union, cast

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Type variables for generics
T = TypeVar("T")
U = TypeVar("U", bound="Serializable")

# Enums
class Color(enum.Enum):
    RED = "red"
    GREEN = "green"
    BLUE = "blue"


# Abstract base class
class Serializable(ABC):
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Convert object to dictionary representation."""
        pass
    
    @classmethod
    @abstractmethod
    def from_dict(cls: Type[U], data: Dict[str, Any]) -> U:
        """Create object from dictionary."""
        pass


# Dataclass
@dataclasses.dataclass
class Point:
    x: float
    y: float
    z: Optional[float] = None
    
    def distance_from_origin(self) -> float:
        """Calculate distance from origin (0, 0, 0)."""
        return (self.x ** 2 + self.y ** 2 + (self.z or 0) ** 2) ** 0.5
    
    def __add__(self, other: Point) -> Point:
        """Add two points together."""
        return Point(
            x=self.x + other.x,
            y=self.y + other.y,
            z=(self.z or 0) + (other.z or 0)
        )


# Class with inheritance
class Shape(Serializable):
    def __init__(self, color: Color) -> None:
        self.color = color
    
    @abstractmethod
    def area(self) -> float:
        """Calculate area of the shape."""
        pass
    
    @abstractmethod
    def perimeter(self) -> float:
        """Calculate perimeter of the shape."""
        pass
    
    def to_dict(self) -> Dict[str, Any]:
        return {"color": self.color.value}
    
    @classmethod
    def from_dict(cls: Type[Shape], data: Dict[str, Any]) -> Shape:
        # This would be implemented by subclasses
        raise NotImplementedError("Base Shape class cannot be instantiated from dict")


class Circle(Shape):
    def __init__(self, radius: float, color: Color) -> None:
        super().__init__(color)
        if radius <= 0:
            raise ValueError("Radius must be positive")
        self.radius = radius
    
    def area(self) -> float:
        import math
        return math.pi * self.radius ** 2
    
    def perimeter(self) -> float:
        import math
        return 2 * math.pi * self.radius
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({"radius": self.radius, "type": "circle"})
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Circle:
        return cls(
            radius=data["radius"],
            color=Color(data["color"])
        )


class Rectangle(Shape):
    def __init__(self, width: float, height: float, color: Color) -> None:
        super().__init__(color)
        if width <= 0 or height <= 0:
            raise ValueError("Width and height must be positive")
        self.width = width
        self.height = height
    
    def area(self) -> float:
        return self.width * self.height
    
    def perimeter(self) -> float:
        return 2 * (self.width + self.height)
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "width": self.width,
            "height": self.height,
            "type": "rectangle"
        })
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Rectangle:
        return cls(
            width=data["width"],
            height=data["height"],
            color=Color(data["color"])
        )


# Factory function
def create_shape(shape_type: str, **kwargs) -> Shape:
    """Factory function to create shapes."""
    if shape_type == "circle":
        return Circle(radius=kwargs["radius"], color=kwargs["color"])
    elif shape_type == "rectangle":
        return Rectangle(
            width=kwargs["width"],
            height=kwargs["height"],
            color=kwargs["color"]
        )
    else:
        raise ValueError(f"Unknown shape type: {shape_type}")


# Complex function with nested control flow
def process_shapes(shapes: List[Shape]) -> Dict[str, Any]:
    """Process a list of shapes and return statistics."""
    if not shapes:
        return {"error": "No shapes provided"}
    
    result = {
        "count": len(shapes),
        "total_area": 0.0,
        "total_perimeter": 0.0,
        "shapes_by_color": {},
        "largest_shape": None,
        "smallest_shape": None
    }
    
    largest_area = -1.0
    smallest_area = float('inf')
    
    for shape in shapes:
        area = shape.area()
        perimeter = shape.perimeter()
        
        result["total_area"] += area
        result["total_perimeter"] += perimeter
        
        color_key = shape.color.value
        if color_key not in result["shapes_by_color"]:
            result["shapes_by_color"][color_key] = []
        
        result["shapes_by_color"][color_key].append(shape.to_dict())
        
        if area > largest_area:
            largest_area = area
            result["largest_shape"] = shape.to_dict()
        
        if area < smallest_area:
            smallest_area = area
            result["smallest_shape"] = shape.to_dict()
    
    # Calculate averages
    result["average_area"] = result["total_area"] / len(shapes)
    result["average_perimeter"] = result["total_perimeter"] / len(shapes)
    
    return result


# Decorator
def log_execution(func):
    """Decorator to log function execution time."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        import time
        logger.info(f"Starting execution of {func.__name__}")
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            elapsed = time.time() - start_time
            logger.info(f"Finished {func.__name__} in {elapsed:.4f} seconds")
            return result
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {str(e)}")
            raise
    return wrapper


# Context manager
class Timer:
    """Context manager for timing code blocks."""
    def __init__(self, name: str) -> None:
        self.name = name
    
    def __enter__(self) -> "Timer":
        import time
        self.start_time = time.time()
        logger.info(f"Starting timer: {self.name}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        import time
        elapsed = time.time() - self.start_time
        if exc_type:
            logger.error(f"Timer {self.name} exited with error: {exc_val}")
        else:
            logger.info(f"Timer {self.name} completed in {elapsed:.4f} seconds")


# Generator function
def fibonacci(n: int) -> typing.Generator[int, None, None]:
    """Generate the first n Fibonacci numbers."""
    a, b = 0, 1
    for _ in range(n):
        yield a
        a, b = b, a + b


# Async function
async def fetch_data(url: str) -> Dict[str, Any]:
    """Simulate fetching data from a URL."""
    logger.info(f"Fetching data from {url}")
    # Simulate network delay
    await asyncio.sleep(0.5)
    return {"url": url, "data": "sample data", "timestamp": "2023-06-01T12:00:00Z"}


# Complex async function
async def process_urls(urls: List[str]) -> Dict[str, Any]:
    """Process multiple URLs concurrently."""
    tasks = [fetch_data(url) for url in urls]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    processed_results = {}
    errors = []
    
    for url, result in zip(urls, results):
        if isinstance(result, Exception):
            errors.append({"url": url, "error": str(result)})
        else:
            processed_results[url] = result
    
    return {
        "results": processed_results,
        "errors": errors,
        "success_count": len(processed_results),
        "error_count": len(errors)
    }


# Main function with error handling
@log_execution
def main() -> int:
    """Main function demonstrating various features."""
    try:
        # Create some shapes
        shapes = [
            create_shape("circle", radius=5.0, color=Color.RED),
            create_shape("rectangle", width=3.0, height=4.0, color=Color.BLUE),
            create_shape("circle", radius=2.5, color=Color.GREEN)
        ]
        
        # Process shapes
        with Timer("process_shapes"):
            stats = process_shapes(shapes)
        
        print(f"Shape statistics: {json.dumps(stats, indent=2)}")
        
        # Demonstrate points
        p1 = Point(1.0, 2.0, 3.0)
        p2 = Point(4.0, 5.0, 6.0)
        p3 = p1 + p2
        
        print(f"Distance of {p3} from origin: {p3.distance_from_origin()}")
        
        # Demonstrate generators
        print("First 10 Fibonacci numbers:")
        for i, fib in enumerate(fibonacci(10)):
            print(f"{i}: {fib}")
        
        # Demonstrate async
        urls = [
            "https://example.com/api/1",
            "https://example.com/api/2",
            "https://example.com/api/3"
        ]
        
        if sys.platform != "win32":  # asyncio.run has issues on Windows in some Python versions
            results = asyncio.run(process_urls(urls))
            print(f"Processed {results['success_count']} URLs successfully")
        
        return 0
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 