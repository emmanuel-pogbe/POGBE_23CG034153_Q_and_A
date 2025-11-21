#!/usr/bin/env python3
import os
import argparse
import sys
import time

try:
    from huggingface_hub import InferenceClient
except Exception:
    InferenceClient = None


def build_parser():
    p = argparse.ArgumentParser(description="CLI chat for HF model (same as app.py)")
    p.add_argument("--model", "-m", help="Model id to use (overrides HF_MODEL env)")
    p.add_argument("--max-tokens", "-k", type=int, default=int(os.environ.get("HF_MAX_TOKENS", 256)),
                   help="Max tokens for generation (default from HF_MAX_TOKENS or 256)")
    p.add_argument("--temperature", "-t", type=float, default=float(os.environ.get("HF_TEMPERATURE", 0.0)),
                   help="Sampling temperature (default 0.0)")
    return p

def main():
    parser = build_parser()
    args = parser.parse_args()

    hf_token = os.environ.get("HF_TOKEN") #Token from the .env file
    model = args.model or os.environ.get("HF_MODEL") or "MiniMaxAI/MiniMax-M2:novita"
    max_tokens = max(1, min(args.max_tokens, 2048))
    temperature = max(0.0, float(args.temperature))

    print(f"Model: {model}")
    print(f"Max tokens: {max_tokens}, temperature: {temperature}")

    if not hf_token or InferenceClient is None:
        if not hf_token:
            print("Warning: HF_TOKEN not set. CLI will use a local placeholder response.")
        if InferenceClient is None:
            print("Warning: huggingface_hub not installed. Install it to use the model: `pip install huggingface-hub`.")

    client = None
    if hf_token and InferenceClient is not None:
        try:
            client = InferenceClient(api_key=hf_token)
        except Exception as e:
            print("Failed to create InferenceClient:", e)
            client = None

    conversation = []

    try:
        while True:
            try:
                user = input("You: ")
            except EOFError:
                print("\nExiting.")
                break

            if not user:
                continue
            if user.strip().lower() in ("exit", "quit"):
                print("Goodbye.")
                break

            conversation.append({"role": "user", "content": user})

            # Call the model (or fallback)
            if client is None:
                # placeholder behavior
                time.sleep(0.5)
                reply = "(placeholder) I received: " + (user[:200] + ("..." if len(user) > 200 else ""))
            else:
                try:
                    out = client.chat.completions.create(
                        model=model,
                        messages=conversation,
                        max_tokens=max_tokens,
                        temperature=temperature,
                    )
                    # extract text in same way app.py does
                    reply = None
                    try:
                        reply = out.choices[0].message.content
                    except Exception:
                        # try other common shapes
                        if isinstance(out, dict):
                            reply = out.get("generated_text") or out.get("text")
                        elif isinstance(out, list) and len(out) > 0:
                            first = out[0]
                            reply = first.get("generated_text") if isinstance(first, dict) else str(first)
                        else:
                            reply = str(out)

                except KeyboardInterrupt:
                    raise
                except Exception as e:
                    print("Error from model call:", e)
                    reply = f"(error) {e}"

            # print and append
            print("Assistant:", reply)
            conversation.append({"role": "assistant", "content": reply})

    except KeyboardInterrupt:
        print("\nInterrupted. Bye.")
        sys.exit(0)
if __name__ == "__main__":
    main()