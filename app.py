from flask import Flask
from flask import render_template, request, jsonify
import time
from huggingface_hub import InferenceClient
import os

hf_token = os.environ.get("HF_TOKEN")

app = Flask(__name__, template_folder="templates", static_folder="static")

# In-memory conversation store (simple, per-server run).
conversations = {
    "default": {
        "id": "default",
        "messages": []
    }
}

@app.route("/")
def index():
    return render_template("index.html")

def ai_response(prompt=None):
    """Generate a reply using the Hugging Face Inference API.

    Reads `HF_TOKEN` and optional `HF_MODEL` from environment. If no token
    is available, falls back to the local placeholder response.
    """
    model = os.environ.get("HF_MODEL", "gpt2")

    if not hf_token:
        # fallback when token not provided
        time.sleep(0.6)
        return "Hi — placeholder (no HF token configured)."

    if not prompt:
        prompt = "Hello"

    try:
        client = InferenceClient(token=hf_token)

        # Use text_generation for models that support it. We request a short
        # response and return the generated text. Adjust parameters as needed.
        output = client.text_generation(model=model, prompt=prompt, max_new_tokens=150)

        # `output` may be a dict with 'generated_text' or a list; handle common shapes
        if isinstance(output, dict):
            text = output.get("generated_text") or output.get("text")
        elif isinstance(output, list) and len(output) > 0:
            first = output[0]
            text = first.get("generated_text") if isinstance(first, dict) else str(first)
        else:
            text = str(output)

        # final fallback
        if not text:
            text = "Error: currently facing downtime - you've used me too much"
        return text
    except Exception as e:
        # On error, log and return a helpful message
        print("HF inference error:", e)
        return f"AI error: {e}"

@app.route("/api/conversations", methods=["GET"])
def get_conversations():
    # Return the default conversation messages
    conv = conversations.get("default", {"messages": []})
    return jsonify(conv)

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json() or {}
    user_message = data.get("message", "")

    # append user message to conversation
    conversations.setdefault("default", {"id": "default", "messages": []})
    conversations["default"]["messages"].append({"role": "user", "content": user_message})

    # Call the AI function with the user's prompt
    reply = ai_response(user_message)

    # append assistant message
    conversations["default"]["messages"].append({"role": "assistant", "content": reply})

    return jsonify({"reply": reply, "messages": conversations["default"]["messages"]})

@app.route("/api/conversations/clear", methods=["POST"])
def clear_conversation():
    conversations["default"]["messages"] = []
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run("0.0.0.0",port=port,debug=True)