class DUMMY {
    constructor() {
        this.name = "DUMMY";
    }
    
}

const dummy = new DUMMY();
console.log(dummy.name);

function dummyFunction() {
    console.log("dummyFunction");
}

dummyFunction();

// if statement
if (dummy.name === "DUMMY") {
    console.log("dummy.name is DUMMY");
} else {
    console.log("dummy.name is not DUMMY");
}

// for loop
for (let i = 0; i < 10; i++) {
    console.log(i);
}

// while loop
let i = 0;
while (i < 10) {
    console.log(i);
    i++;
}

// do while loop
do {
    console.log(i);
    i++;
} while (i < 10);

// switch statement
switch (dummy.name) {
    case "DUMMY":
        console.log("dummy.name is DUMMY");
        break;
}

// try catch
try {
    console.log("try");
} catch (error) {
    console.log("catch");
}













