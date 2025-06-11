// Rust test file for analyzer testing
// Contains various Rust constructs to test the analyzer

use std::collections::{HashMap, HashSet};
use std::error::Error;
use std::fmt;
use std::sync::{Arc, Mutex};
use std::thread;
use std::time::Duration;

// Type aliases
type Result<T> = std::result::Result<T, Box<dyn Error>>;
type UserId = u64;

// Custom error type
#[derive(Debug)]
enum AppError {
    NotFound(String),
    InvalidInput(String),
    DatabaseError(String),
}

impl fmt::Display for AppError {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        match self {
            AppError::NotFound(msg) => write!(f, "Not found: {}", msg),
            AppError::InvalidInput(msg) => write!(f, "Invalid input: {}", msg),
            AppError::DatabaseError(msg) => write!(f, "Database error: {}", msg),
        }
    }
}

impl Error for AppError {}

// Enums
#[derive(Debug, Clone, PartialEq)]
enum Role {
    Admin,
    Editor,
    Viewer,
}

// Structs
#[derive(Debug, Clone)]
struct User {
    id: UserId,
    name: String,
    email: String,
    role: Role,
    active: bool,
}

impl User {
    fn new(id: UserId, name: String, email: String, role: Role) -> Self {
        User {
            id,
            name,
            email,
            role,
            active: true,
        }
    }

    fn deactivate(&mut self) {
        self.active = false;
    }

    fn is_admin(&self) -> bool {
        self.role == Role::Admin
    }
}

// Trait definition
trait Repository<T> {
    fn find_by_id(&self, id: u64) -> Option<T>;
    fn save(&mut self, item: T) -> Result<()>;
    fn delete(&mut self, id: u64) -> Result<()>;
    fn find_all(&self) -> Vec<T>;
}

// Implementation of the Repository trait
struct UserRepository {
    users: HashMap<UserId, User>,
}

impl UserRepository {
    fn new() -> Self {
        UserRepository {
            users: HashMap::new(),
        }
    }
}

impl Repository<User> for UserRepository {
    fn find_by_id(&self, id: UserId) -> Option<User> {
        self.users.get(&id).cloned()
    }

    fn save(&mut self, user: User) -> Result<()> {
        self.users.insert(user.id, user);
        Ok(())
    }

    fn delete(&mut self, id: UserId) -> Result<()> {
        if self.users.remove(&id).is_none() {
            return Err(Box::new(AppError::NotFound(format!("User with id {} not found", id))));
        }
        Ok(())
    }

    fn find_all(&self) -> Vec<User> {
        self.users.values().cloned().collect()
    }
}

// Generic struct
struct Cache<T> {
    data: HashMap<String, T>,
}

impl<T: Clone> Cache<T> {
    fn new() -> Self {
        Cache {
            data: HashMap::new(),
        }
    }

    fn get(&self, key: &str) -> Option<T> {
        self.data.get(key).cloned()
    }

    fn set(&mut self, key: String, value: T) {
        self.data.insert(key, value);
    }

    fn remove(&mut self, key: &str) -> Option<T> {
        self.data.remove(key)
    }
}

// Function with complex logic
fn process_users(users: &[User], filter_inactive: bool) -> Result<HashMap<Role, Vec<User>>> {
    if users.is_empty() {
        return Err(Box::new(AppError::InvalidInput("Empty user list".to_string())));
    }

    let mut result: HashMap<Role, Vec<User>> = HashMap::new();

    for user in users {
        if filter_inactive && !user.active {
            continue;
        }

        match user.role {
            Role::Admin => {
                if let Some(admins) = result.get_mut(&Role::Admin) {
                    admins.push(user.clone());
                } else {
                    result.insert(Role::Admin, vec![user.clone()]);
                }
            }
            Role::Editor => {
                if let Some(editors) = result.get_mut(&Role::Editor) {
                    editors.push(user.clone());
                } else {
                    result.insert(Role::Editor, vec![user.clone()]);
                }
            }
            Role::Viewer => {
                if let Some(viewers) = result.get_mut(&Role::Viewer) {
                    viewers.push(user.clone());
                } else {
                    result.insert(Role::Viewer, vec![user.clone()]);
                }
            }
        }
    }

    Ok(result)
}

// Closures and higher-order functions
fn transform_users<F>(users: &[User], transformer: F) -> Vec<String>
where
    F: Fn(&User) -> String,
{
    users.iter().map(transformer).collect()
}

// Async functions
async fn fetch_user_data(user_id: UserId) -> Result<User> {
    // Simulate API call
    tokio::time::sleep(Duration::from_millis(100)).await;
    
    // Simulate response
    if user_id % 2 == 0 {
        Ok(User::new(
            user_id,
            format!("User {}", user_id),
            format!("user{}@example.com", user_id),
            Role::Viewer,
        ))
    } else {
        Err(Box::new(AppError::NotFound(format!("User {} not found", user_id))))
    }
}

// Complex async function with concurrency
async fn process_user_batch(user_ids: Vec<UserId>) -> Result<Vec<User>> {
    if user_ids.is_empty() {
        return Err(Box::new(AppError::InvalidInput("Empty user id list".to_string())));
    }

    let mut tasks = Vec::new();
    for id in user_ids {
        tasks.push(fetch_user_data(id));
    }

    let results = futures::future::join_all(tasks).await;
    let mut users = Vec::new();

    for result in results {
        match result {
            Ok(user) => users.push(user),
            Err(_) => {} // Skip errors
        }
    }

    if users.is_empty() {
        return Err(Box::new(AppError::NotFound("No users found".to_string())));
    }

    Ok(users)
}

// Thread-safe shared state
fn concurrent_counter(num_threads: usize, iterations: usize) -> usize {
    let counter = Arc::new(Mutex::new(0));
    let mut handles = vec![];

    for _ in 0..num_threads {
        let counter_clone = Arc::clone(&counter);
        let handle = thread::spawn(move || {
            for _ in 0..iterations {
                let mut num = counter_clone.lock().unwrap();
                *num += 1;
                // Simulate some work
                thread::sleep(Duration::from_micros(10));
            }
        });
        handles.push(handle);
    }

    for handle in handles {
        handle.join().unwrap();
    }

    *counter.lock().unwrap()
}

// Pattern matching
fn describe_role(role: &Role) -> String {
    match role {
        Role::Admin => "Administrator with full access".to_string(),
        Role::Editor => "Editor with content management access".to_string(),
        Role::Viewer => "Viewer with read-only access".to_string(),
    }
}

// Main function
fn main() -> Result<()> {
    // Create users
    let mut users = vec![
        User::new(1, "Alice".to_string(), "alice@example.com".to_string(), Role::Admin),
        User::new(2, "Bob".to_string(), "bob@example.com".to_string(), Role::Editor),
        User::new(3, "Charlie".to_string(), "charlie@example.com".to_string(), Role::Viewer),
    ];

    // Deactivate a user
    users[2].deactivate();

    // Process users
    let users_by_role = process_users(&users, true)?;
    
    // Print user count by role
    for (role, users) in &users_by_role {
        println!("Role {:?}: {} users", role, users.len());
    }

    // Use higher-order function
    let user_emails = transform_users(&users, |user| {
        format!("{}: {}", user.name, user.email)
    });
    
    for email in user_emails {
        println!("{}", email);
    }

    // Use generic cache
    let mut cache = Cache::new();
    cache.set("key1".to_string(), "value1".to_string());
    cache.set("key2".to_string(), "value2".to_string());
    
    if let Some(value) = cache.get("key1") {
        println!("Found in cache: {}", value);
    }

    // Concurrent operations
    let count = concurrent_counter(4, 100);
    println!("Final count: {}", count);

    // Pattern matching
    for user in &users {
        let role_description = describe_role(&user.role);
        println!("{} is a {}", user.name, role_description);
    }

    Ok(())
}

// Unit tests
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_user_creation() {
        let user = User::new(1, "Test".to_string(), "test@example.com".to_string(), Role::Admin);
        assert_eq!(user.id, 1);
        assert_eq!(user.name, "Test");
        assert_eq!(user.email, "test@example.com");
        assert_eq!(user.role, Role::Admin);
        assert!(user.active);
    }

    #[test]
    fn test_user_deactivation() {
        let mut user = User::new(1, "Test".to_string(), "test@example.com".to_string(), Role::Admin);
        assert!(user.active);
        user.deactivate();
        assert!(!user.active);
    }

    #[test]
    fn test_process_users() {
        let users = vec![
            User::new(1, "A".to_string(), "a@example.com".to_string(), Role::Admin),
            User::new(2, "B".to_string(), "b@example.com".to_string(), Role::Editor),
            User::new(3, "C".to_string(), "c@example.com".to_string(), Role::Viewer),
        ];

        let result = process_users(&users, false).unwrap();
        assert_eq!(result.len(), 3);
        assert_eq!(result.get(&Role::Admin).unwrap().len(), 1);
        assert_eq!(result.get(&Role::Editor).unwrap().len(), 1);
        assert_eq!(result.get(&Role::Viewer).unwrap().len(), 1);
    }
} 