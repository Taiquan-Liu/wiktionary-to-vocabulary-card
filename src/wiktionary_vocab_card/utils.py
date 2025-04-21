import json
import subprocess


def add_word(word, url):
    with open("./examples/examples.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    data[word] = url
    with open("./examples/examples.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
        print("Added to examples.json")


def generate_all_examples():
    with open("./examples/examples.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    for word, url in data.items():
        print(f"Regenerating {word}...")
        cmd = [
            "wikt-vocab",
            "generate",
            url,
            "-o",
            f"examples/{word}.md",
            "-t",
            "examples",
        ]
        subprocess.run(cmd, check=True)
        print(f"✓ examples/{word}.md")
