import json

training_data = [
    {
        "prompt": "Explain the security risk of 'Hardcoded API Key' in simple terms.",
        "completion": "A 'Hardcoded API Key' is a vulnerability where a secret key, password, or credential is written directly into the source code. This is risky because anyone with access to the code, including attackers, can steal the key and gain unauthorized access to services. Secrets should always be stored in a secure vault or as environment variables, not in the code."
    },
    {
        "prompt": "What is SQL Injection and why is it dangerous?",
        "completion": "SQL Injection (SQLi) is an attack where a malicious user inserts or 'injects' their own SQL code into a query. This can trick the database into revealing sensitive information, deleting data, or even giving the attacker full control over the system. It's dangerous because it directly targets the database, which is often the most critical part of an application."
    },
    {
        "prompt": "Explain Cross-Site Scripting (XSS) like I'm a new developer.",
        "completion": "Cross-Site Scripting (XSS) is an attack where a malicious script is injected into a trusted website. When an unsuspecting user visits the page, the script runs in their browser. This can be used to steal the user's cookies, session tokens, or other sensitive information, effectively hijacking their session. Always sanitize user input before displaying it on a page to prevent this."
    }
]

output_file = "train.jsonl"

with open(output_file, 'w') as f:
    for entry in training_data:
        f.write(json.dumps(entry) + '\n')

print(f"✅ {output_file} created successfully.")
