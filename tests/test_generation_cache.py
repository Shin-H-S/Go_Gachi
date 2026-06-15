from backend.app.db.models import Generation
from backend.app.services.generation_cache import _snapshot


def test_snapshot_copies_cache_fields() -> None:
    row = Generation(
        image_hash="image-hash",
        preset_id="instagram",
        instruction_hash="instruction-hash",
        prompt_version="prompt-v1",
        model="gpt-image-2",
        original_path="uploads/original.png",
        output_path="outputs/result.png",
        image_url=None,
        prompt="prompt text",
    )

    assert _snapshot(row) == {
        "image_hash": "image-hash",
        "preset_id": "instagram",
        "instruction_hash": "instruction-hash",
        "prompt_version": "prompt-v1",
        "model": "gpt-image-2",
        "original_path": "uploads/original.png",
        "output_path": "outputs/result.png",
        "image_url": None,
        "prompt": "prompt text",
    }
