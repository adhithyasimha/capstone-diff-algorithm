## synthetic_stream
- Simulates coding activity for 10 students, identified by SRNs (e.g., pes2ug22cs001 to pes2ug22cs010).
- Generates logs with fields: SRN, code snippet, timestamp, and event type (keystroke, backspace, copy-paste).
- Sends logs to the `activity_logs` Kafka topic.

## diffalgo
- Reads logs from the `activity_logs` topic.
- Maps logs to SRNs using an in-memory dictionary.
- Computes diffs between consecutive submissions for each student using `difflib`.
- Writes results to `consumer_output.json` in real-time.

## Output
- A JSON file (`consumer_output.json`) containing a list of log entries, including first submissions and changes, for later plagiarism analysis.

# Example Output (`consumer_output.json`)
The output file is a JSON array of log entries. Each entry is either a `first_log` (for a student’s first submission) or a `change` (for subsequent submissions with diffs). Here’s an example:

```json
[
    {
        "type": "first_log",
        "student_id": "pes2ug22cs001",
        "log": {
            "timestamp": "2025-03-23T12:00:00.123456",
            "code": "x = 0\nprint(x)",
            "event_type": "keystroke"
        }
    },
    {
        "type": "change",
        "student_id": "pes2ug22cs001",
        "previous_log": {
            "timestamp": "2025-03-23T12:00:00.123456",
            "code": "x = 0\nprint(x)"
        },
        "current_log": {
            "timestamp": "2025-03-23T12:00:02.345678",
            "code": "x = 0\nprint(x)\ny = 10"
        },
        "event_type": "keystroke",
        "changes": "+ 'y = 10'",
        "time_taken_microseconds": 26.20800847187638
    }
]
```

### Explanation:
- **First Log**: Records the initial submission for a student.
- **Change Log**: Shows the previous and current code, the event type, the diff (e.g., `+ 'y = 10'` for an added line), and the time taken to compute the diff in microseconds.

---

# How It Works

## synthetic_stream.py

### Log Generation:
- Simulates 10 students (SRNs: `pes2ug22cs001` to `pes2ug22cs010`).
- Generates initial code snippets (e.g., `x = 0\nprint(x)`) and applies realistic changes based on event types:
  - **Keystroke**: Adds small changes (e.g., a new variable, loop, or comment).
  - **Backspace**: Removes lines or characters.
  - **Copy-paste**: Adds larger snippets (e.g., a function or loop), simulating potential plagiarism.
- Ensures all code is syntactically valid using Python’s `ast` module.

### Timing:
- Adds realistic delays between logs (e.g., `0.5–2` seconds for `keystroke`, `5–10` seconds for `copy-paste`).

### Kafka Integration:
- Sends logs to the `activity_logs` topic with the SRN as the key, ensuring ordered processing per student.

---

## diffalgo.py

### Log Processing:
- Reads logs from the `activity_logs` topic using `KafkaConsumer`.
- Maps logs to SRNs using an in-memory dictionary (`student_code_history`).

### Diff Computation:
- For each new log:
  - If it’s the **first log** for an SRN, stores it as a `first_log` entry.
  - If there’s a **previous log**, computes the diff using `difflib.SequenceMatcher`:
    - Compares code line by line.
    - Identifies additions (e.g., `+ 'y = 10'`) and removals (e.g., `- 'x = 0'`).
    - Measures computation time in microseconds (e.g., `96.2` microseconds for complex changes).
- Updates the dictionary with the new log for future comparisons.



