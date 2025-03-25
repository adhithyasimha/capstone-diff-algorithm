from kafka import KafkaConsumer
import json
import time
import os
import difflib

consumer = KafkaConsumer(
    'activity_logs',
    bootstrap_servers='localhost:9092',
    auto_offset_reset='earliest',
    enable_auto_commit=True,
    group_id='diff-algorithm-group',
    key_deserializer=lambda key: key.decode('utf-8'),
    value_deserializer=lambda value: json.loads(value.decode('utf-8'))
)

student_code_history = {}

output_file = "consumer_output.json"

def initialize_json_file():
    with open(output_file, 'w') as file:
        file.write('[\n')

def append_to_json_file(log_entry, is_first_entry):
    with open(output_file, 'a') as file:
        if not is_first_entry:
            file.write(',\n')
        json.dump(log_entry, file, indent=4)

def finalize_json_file():
    with open(output_file, 'r') as file:
        content = file.read()
    
    if content.endswith(',\n'):
        content = content[:-2]
    content += '\n]'
    
    with open(output_file, 'w') as file:
        file.write(content)

def compute_code_changes(previous_code_log, current_code_log):
    previous_code = previous_code_log["code"]
    current_code = current_code_log["code"]
    
    if previous_code == current_code:
        return "No change"
    
    previous_lines = previous_code.splitlines()
    current_lines = current_code.splitlines()
    
    matcher = difflib.SequenceMatcher(None, previous_lines, current_lines)
    
    changes = []
    
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "delete":
            for i in range(i1, i2):
                changes.append(f"- '{previous_lines[i]}'")
        elif tag == "insert":
            for j in range(j1, j2):
                changes.append(f"+ '{current_lines[j]}'")
        elif tag == "replace":
            for i in range(i1, i2):
                changes.append(f"- '{previous_lines[i]}'")
            for j in range(j1, j2):
                changes.append(f"+ '{current_lines[j]}'")
    
    return "\n".join(changes) if changes else "No change"

def process_student_logs():
    print("Starting the diff algorithm consumer... (Press Ctrl+C to stop)\n")
    
    initialize_json_file()
    
    is_first_entry = True
    
    try:
        for message in consumer:
            current_log = message.value
            student_id = current_log["srn"]
            
            if student_id in student_code_history:
                previous_code_log = student_code_history[student_id]
                
                start_time = time.perf_counter()
                code_changes = compute_code_changes(previous_code_log, current_log)
                end_time = time.perf_counter()
                time_taken_microseconds = (end_time - start_time) * 1_000_000
                
                log_entry = {
                    "type": "change",
                    "student_id": student_id,
                    "previous_log": {
                        "timestamp": previous_code_log["timestamp"],
                        "code": previous_code_log["code"]
                    },
                    "current_log": {
                        "timestamp": current_log["timestamp"],
                        "code": current_log["code"]
                    },
                    "event_type": current_log["event_type"],
                    "changes": code_changes,
                    "time_taken_microseconds": time_taken_microseconds
                }
            else:
                log_entry = {
                    "type": "first_log",
                    "student_id": student_id,
                    "log": {
                        "timestamp": current_log["timestamp"],
                        "code": current_log["code"],
                        "event_type": current_log["event_type"]
                    }
                }
            
            append_to_json_file(log_entry, is_first_entry)
            is_first_entry = False
            
            student_code_history[student_id] = current_log
    
    except KeyboardInterrupt:
        print("\nStopped by user. Finalizing the JSON file...")
        finalize_json_file()
        print("JSON file finalized successfully.")
        consumer.close()

if __name__ == "__main__":
    process_student_logs()