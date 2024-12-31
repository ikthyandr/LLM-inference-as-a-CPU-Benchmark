import json
import time
from subprocess import Popen, PIPE
import ollama
from config import DEFAULT_MODEL, PROMPT, NUM_OF_ITERATIONS

def measure_tokens_per_second():
    
    res = {}
    #try:
    # Record start time
    start_time = time.time()
    
    # Generate response using Ollama's Llama2 model
    response = ollama.chat(
        model= DEFAULT_MODEL,
        messages= [{'role': 'user', 'content': PROMPT}]
    )
    
    # Record end time
    end_time = time.time()
    
    # Calculate total time taken
    total_time = end_time - start_time
    
    # Count tokens in the response
    # Note: This uses the full response text for token counting
    tokens = len(response['message']['content'].split())
    
    # Calculate tokens per second
    tokens_per_second = tokens / total_time

    res['tokens_per_second'] = tokens_per_second
    res['total_time'] = total_time
    return res


results = []
for _ in range(NUM_OF_ITERATIONS):
    result = measure_tokens_per_second()
    results.append(result)
    time.sleep(2)  # Cool down between runs

print(json.dumps( results ))