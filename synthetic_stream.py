from kafka import KafkaProducer
import json
import time
import random
from datetime import datetime, timedelta
import ast


producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    key_serializer=lambda k: k.encode('utf-8'),
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# Define the Kafka topic
topic = 'activity_logs'

# Generate SRNs (Student Registration Numbers)
def generate_srns(num_users=10):
    return [f"pes2ug22cs{str(i).zfill(3)}" for i in range(1, num_users + 1)]

# Validate if a given code snippet is syntactically correct
def is_valid_code(code):
    try:
        ast.parse(code)
        return True
    except SyntaxError:
        return False


def apply_change(previous_code, event_type):
    if not previous_code:
        # Initial code snippets if no previous code exists
        initial_snippets = [
            "x = 0\nprint(x)",
            "numbers = [1, 2, 3]\nprint(numbers)",
            "def greet():\n    print('Hello')\ngreet()"
        ]
        return random.choice(initial_snippets)
    
    # Define possible code modifications for each event type
    changes = {
        "keystroke": [
            lambda x: x + "\ny = 10",  # Add a new variable
            lambda x: x + "\nfor i in range(3):\n    print(i)",  # Add a loop
            lambda x: x + " + 5" if "print(" in x else x + "\nx = x + 5",  # Modify an expression
            lambda x: x + "\nif x > 0:\n    print('Positive')",  # Add a conditional
            lambda x: x + "\n# New comment",  # Add a comment
        ],
        "backspace": [
            lambda x: "\n".join(x.split("\n")[:-1]) if "\n" in x else x[:-1],  # Remove last line or last character
            lambda x: x.rsplit(" ", 1)[0] if " " in x else x,  # Remove last word
            lambda x: x.rsplit("\n", 1)[0] if "\n" in x else x,  # Remove last line
        ],
        "copy-paste": [
            lambda x: x + "\ndef square(n):\n    return n * n",  # Add a function
            lambda x: x + "\n# Calculate sum\nresult = sum([1, 2, 3])",  # Add a computation
            lambda x: x + "\nwhile x < 10:\n    x += 1\n    print(x)",  # Add a while loop
            lambda x: x + "\nfor j in range(5):\n    print(j * 2)",  # Add another loop
        ]
    }
    
    # Apply the change and ensure the result is valid
    max_attempts = 5
    for _ in range(max_attempts):
        change = random.choice(changes[event_type])
        new_code = change(previous_code)
        if is_valid_code(new_code):
            return new_code
    
    return previous_code  


def get_event_delay(event_type):
    delay_ranges = {
        "keystroke": (0.5, 2),
        "backspace": (0.3, 1),
        "copy-paste": (5, 10)
    }
    min_delay, max_delay = delay_ranges[event_type]
    return random.uniform(min_delay, max_delay)

# Generate logs and send them to Kafka
def generate_and_send_logs(num_users=10):
    srns = generate_srns(num_users)
    previous_codes = {srn: None for srn in srns} 
    
    base_time = datetime.now()
    time_offset = 0  
    
    print(f"Generating logs for {num_users} users and sending to Kafka topic '{topic}'... (Press Ctrl+C to stop)\n")
    
    try:
        while True:
            srn = random.choice(srns)  
            event_type = random.choice(["keystroke", "backspace", "copy-paste"]) 
            previous_code = previous_codes[srn]
            new_code = apply_change(previous_code, event_type)  
            
            delay = get_event_delay(event_type)  
            time_offset += delay
            timestamp = (base_time + timedelta(seconds=time_offset)).isoformat()
            
            log = {
                "srn": srn,
                "code": new_code,
                "timestamp": timestamp,
                "event_type": event_type
            }
            
            producer.send(topic, key=srn, value=log)  
            previous_codes[srn] = new_code  
            time.sleep(delay)  
    except KeyboardInterrupt:
        print("\nStopped by user.")
        producer.close()

# Run the producer
if __name__ == "__main__":
    generate_and_send_logs(num_users=10)
