from gpt4all import GPT4All

MODEL_GPT_PATH = r"D:\CU\AIML_project\Mistral-7B-Instruct-v0.3-Q4_K_M.gguf"

try:
    model_gpt = GPT4All(MODEL_GPT_PATH)
    #model_gpt = GPT4All("Mistral-7B-Instruct-v0.3-Q4_K_M.gguf", device="cuda")

    response = model_gpt.generate("What is AI?", max_tokens=50)
    print("✅ GPT Response:", response)
except Exception as e:
    print("❌ GPT4All Error:", str(e))
