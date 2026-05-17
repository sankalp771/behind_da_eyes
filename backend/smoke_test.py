import os
from dotenv import load_dotenv
from videodb import connect, SandboxTier, SandboxModel

load_dotenv()

api_key = os.environ.get("VIDEO_DB_API_KEY", os.environ.get("VIDEODB_API_KEY"))
conn = connect(api_key=api_key)
coll = conn.get_collection()

print("Creating sandbox...")
sandbox = conn.create_sandbox(tier=SandboxTier.medium)
print("Waiting for sandbox to be ready...")
sandbox.wait_for_ready(timeout=300, interval=5)

# Smoke test FLUX image gen
print("Sandbox ready. Starting image generation...")
job = coll.generate_image(
    prompt="Light Yagami anime character, close-up, staring into camera, dramatic lighting",
    model_name=SandboxModel.FLUX,
    sandbox_id=sandbox.id,
    config={"size": "1280x720", "num_inference_steps": 28},
)
img = job.wait(timeout=900, interval=5)
print("Image generated successfully. ID:", img.id)
sandbox.stop()
print("Sandbox stopped.")
