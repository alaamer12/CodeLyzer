/**
 * Enhanced JavaScript test file for analyzer testing
 * Contains various JavaScript constructs to test the analyzer
 */

// Import statements
import { someFunction } from './nonexistent';
import * as utils from './utils';

// Class declaration with methods and inheritance
class Shape {
    constructor(color) {
        this.color = color;
    }
    
    draw() {
        console.log(`Drawing a ${this.color} shape`);
    }
    
    static createDefault() {
        return new Shape('black');
    }
}

class Circle extends Shape {
    constructor(color, radius) {
        super(color);
        this.radius = radius;
    }
    
    draw() {
        super.draw();
        console.log(`Circle with radius ${this.radius}`);
    }
    
    get area() {
        return Math.PI * this.radius * this.radius;
    }
    
    set radius(value) {
        if (value <= 0) {
            throw new Error('Radius must be positive');
        }
        this._radius = value;
    }
    
    get radius() {
        return this._radius;
    }
}

// Arrow functions
const multiply = (a, b) => a * b;
const add = (a, b) => {
    return a + b;
};

// Complex conditions
function complexFunction(a, b, c) {
    if (a > 0 && b > 0 || c > 0) {
        let result = 0;
        for (let i = 0; i < 10; i++) {
            if (i % 2 === 0) {
                result += i;
            } else if (i % 3 === 0) {
                result -= i;
            } else {
                result *= 2;
            }
        }
        return result;
    } else {
        try {
            return a / (b - c);
        } catch (error) {
            console.error('Division error', error);
            return null;
        } finally {
            console.log('Calculation completed');
        }
    }
}

// Async/await
async function fetchData() {
    try {
        const response = await fetch('https://api.example.com/data');
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Fetch error:', error);
        return [];
    }
}

// Promises
const promiseExample = new Promise((resolve, reject) => {
    setTimeout(() => {
        const success = Math.random() > 0.5;
        if (success) {
            resolve('Operation successful');
        } else {
            reject(new Error('Operation failed'));
        }
    }, 1000);
});

// Higher-order functions
const numbers = [1, 2, 3, 4, 5];
const doubled = numbers.map(x => x * 2);
const evens = numbers.filter(x => x % 2 === 0);
const sum = numbers.reduce((acc, val) => acc + val, 0);

// Object destructuring
const person = { name: 'John', age: 30, city: 'New York' };
const { name, age } = person;

// Spread operator
const newPerson = { ...person, job: 'Developer' };
const combinedArray = [...numbers, ...doubled];

// Template literals
const greeting = `Hello, ${name}! You are ${age} years old.`;

// Default parameters
function greet(name = 'Guest') {
    return `Hello, ${name}!`;
}

// Export statement
export { Shape, Circle, complexFunction, fetchData }; 