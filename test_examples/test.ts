/**
 * TypeScript test file for analyzer testing
 * Contains various TypeScript constructs
 */

// Type definitions
type ID = string | number;
type UserRole = 'admin' | 'editor' | 'viewer';
interface User {
    id: ID;
    name: string;
    email: string;
    role: UserRole;
    age?: number;
}

// Generic types
interface Collection<T> {
    items: T[];
    add(item: T): void;
    remove(item: T): boolean;
    find(predicate: (item: T) => boolean): T | undefined;
}

// Class with implementation and generics
class UserCollection implements Collection<User> {
    private _items: User[] = [];

    constructor(initialUsers?: User[]) {
        if (initialUsers) {
            this._items = [...initialUsers];
        }
    }

    get items(): User[] {
        return [...this._items]; // Return a copy to prevent direct modification
    }

    add(user: User): void {
        if (this._items.some(u => u.id === user.id)) {
            throw new Error(`User with ID ${user.id} already exists`);
        }
        this._items.push(user);
    }

    remove(user: User): boolean {
        const initialLength = this._items.length;
        this._items = this._items.filter(u => u.id !== user.id);
        return initialLength !== this._items.length;
    }

    find(predicate: (user: User) => boolean): User | undefined {
        return this._items.find(predicate);
    }

    findByRole(role: UserRole): User[] {
        return this._items.filter(user => user.role === role);
    }
}

// Function with type parameters and return type
function createUser<T extends Partial<User>>(data: T): User {
    return {
        id: data.id || Math.random().toString(36).substring(2, 9),
        name: data.name || 'Anonymous',
        email: data.email || 'anonymous@example.com',
        role: data.role || 'viewer',
        ...data
    };
}

// Async function with typed parameters and return value
async function fetchUserData(userId: ID): Promise<User> {
    try {
        const response = await fetch(`https://api.example.com/users/${userId}`);
        if (!response.ok) {
            throw new Error(`Failed to fetch user: ${response.statusText}`);
        }
        const data: User = await response.json();
        return data;
    } catch (error) {
        console.error('Error fetching user:', error);
        throw error;
    }
}

// Function with union types
function processValue(value: string | number | boolean): string {
    if (typeof value === 'string') {
        return value.toUpperCase();
    } else if (typeof value === 'number') {
        return value.toFixed(2);
    } else {
        return value ? 'YES' : 'NO';
    }
}

// Abstract class with inheritance
abstract class Component {
    protected _id: string;
    
    constructor(protected element: HTMLElement) {
        this._id = Math.random().toString(36).substring(2, 9);
    }

    abstract render(): void;
    
    get id(): string {
        return this._id;
    }

    dispose(): void {
        this.element.remove();
    }
}

class Button extends Component {
    constructor(
        element: HTMLElement,
        private text: string,
        private onClick: () => void
    ) {
        super(element);
    }

    render(): void {
        this.element.textContent = this.text;
        this.element.addEventListener('click', this.onClick);
    }

    updateText(newText: string): void {
        this.text = newText;
        if (this.element) {
            this.element.textContent = newText;
        }
    }
}

// Enum type
enum Direction {
    Up = 'UP',
    Down = 'DOWN',
    Left = 'LEFT',
    Right = 'RIGHT'
}

// Complex function with nested conditions
function moveCharacter(position: {x: number, y: number}, direction: Direction, steps: number = 1): {x: number, y: number} {
    let newPosition = {...position};
    
    switch (direction) {
        case Direction.Up:
            newPosition.y -= steps;
            break;
        case Direction.Down:
            newPosition.y += steps;
            break;
        case Direction.Left:
            newPosition.x -= steps;
            break;
        case Direction.Right:
            newPosition.x += steps;
            break;
        default:
            // This is technically unreachable with TypeScript's type checking
            console.error('Invalid direction');
    }
    
    // Boundary check
    if (newPosition.x < 0 || newPosition.y < 0) {
        return position; // Don't allow negative positions
    }
    
    return newPosition;
}

// Export declarations
export { 
    User, UserRole, UserCollection, 
    createUser, fetchUserData, processValue,
    Component, Button, Direction, moveCharacter
}; 